import json
import os
import subprocess
import sys
import unittest
from contextlib import ExitStack
from datetime import date

import test_dados
from dados import detalhar, listar

try:
    from playwright.sync_api import expect, sync_playwright
except ImportError:
    sync_playwright = None


SERVIDOR_COM_ABERTURA_SIMULADA = """
import json
import os
from pathlib import Path
import runpy
import sys

servidor = Path(sys.argv[1])
log = Path(sys.argv[2])

def registrar_abertura(caminho):
    with log.open("a", encoding="utf-8") as saida:
        saida.write(json.dumps(caminho) + "\\n")

os.startfile = registrar_abertura
sys.path.insert(0, str(servidor.parent))
sys.argv = [str(servidor)]
runpy.run_path(str(servidor), run_name="__main__")
"""


@unittest.skipIf(sync_playwright is None, "Instale Playwright e Chrome para testar o painel.")
class PainelTest(unittest.TestCase):
    def setUp(self):
        self.dados = test_dados.DadosTest()
        self.addCleanup(self.dados.doCleanups)
        self.dados.setUp()
        self.recursos = ExitStack()
        self.addCleanup(self.recursos.close)
        self.vaga_id = "empresa-exemplo/local-002"
        self.dossie = self.dados.carreira / "oportunidades" / self.vaga_id
        (self.dossie / "envios").mkdir()
        self.material = self.dossie / "envios" / "curriculo-final.pdf"
        self.material.write_text("Material de teste", encoding="utf-8")
        self.aberturas = self.dados.workspace / "aberturas.jsonl"
        self.servidor = self.recursos.enter_context(subprocess.Popen(
            [sys.executable, "-B", "-c", SERVIDOR_COM_ABERTURA_SIMULADA,
             str(test_dados.PLUGIN / "server" / "servidor.py"), str(self.aberturas)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env={**os.environ, "CARREIRA_ROOT": str(self.dados.carreira)},
        ))
        self.recursos.callback(self.servidor.stdin.close)
        self.id_rpc = 0
        self.mensagens = []
        self.selecoes = []
        self.pedidos_de_abertura = []
        self.recusar_primeira = False
        self.mcp("initialize", {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {
            "name": "teste-painel", "version": "0.3.0",
        }})
        self.servidor.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
        self.servidor.stdin.flush()
        self.ferramentas = {item["name"]: item for item in self.mcp("tools/list")["tools"]}

    def mcp(self, metodo, params=None):
        self.id_rpc += 1
        chamada = {"jsonrpc": "2.0", "id": self.id_rpc, "method": metodo, "params": params or {}}
        self.servidor.stdin.write(json.dumps(chamada) + "\n")
        self.servidor.stdin.flush()
        resposta = json.loads(self.servidor.stdout.readline())
        self.assertEqual(resposta["id"], self.id_rpc)
        self.assertNotIn("error", resposta)
        return resposta["result"]

    def host(self, chamada):
        metodo = chamada["method"]
        params = chamada["params"]
        if metodo == "ui/initialize":
            self.assertEqual(params["protocolVersion"], "2026-01-26")
            return {"protocolVersion": params["protocolVersion"], "hostContext": {"theme": "dark"}}
        if metodo == "tools/call":
            if params["name"] == "detalhar_vaga":
                self.selecoes.append(params["arguments"]["processo_id"])
            if params["name"] == "abrir_curriculo":
                self.pedidos_de_abertura.append(params["arguments"])
            return self.mcp(metodo, params)
        if metodo == "ui/message":
            self.mensagens.append(params)
            if self.recusar_primeira and len(self.mensagens) == 1:
                return {"isError": True}
            return {}
        raise AssertionError(f"Método não esperado no host: {metodo}")

    def abrir_painel(self, *, boas_vindas=False):
        nome = "abrir_boas_vindas" if boas_vindas else "abrir_painel"
        abrir = self.ferramentas[nome]
        self.assertFalse(self.mcp("tools/call", {"name": nome}).get("isError", False))
        uri = abrir["_meta"]["ui"]["resourceUri"]
        recurso = self.mcp("resources/read", {"uri": uri})["contents"][0]
        self.assertEqual(recurso["mimeType"], "text/html;profile=mcp-app")
        playwright = self.recursos.enter_context(sync_playwright())
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        self.recursos.callback(browser.close)
        page = browser.new_page()
        page.expose_function("host", self.host)
        page.evaluate("""html => {
            const frame = document.createElement("iframe");
            frame.setAttribute("sandbox", "allow-scripts");
            frame.width = "900";
            frame.height = "650";
            window.addEventListener("message", async ({source, data}) => {
                if (source !== frame.contentWindow || data?.jsonrpc !== "2.0" || !data.id) return;
                const result = await window.host(data);
                source.postMessage({jsonrpc: "2.0", id: data.id, result}, "*");
            });
            frame.srcdoc = html;
            document.body.append(frame);
        }""", recurso["text"])
        painel = page.frame_locator("iframe")
        expect(painel.get_by_role("heading", name="Painel de vagas")).to_be_visible()
        if not boas_vindas:
            expect(painel.get_by_text("2 vagas", exact=True)).to_be_visible()
        expect(painel.locator("html")).to_have_attribute("data-theme", "dark")
        return painel, painel.get_by_role("region", name="Detalhes da vaga")

    def test_boas_vindas_verifica_pastas_e_orienta_no_chat(self):
        for relativo in ("perfil/perfil-profissional.md", "estrategia/referencias-candidaturas.md", "curriculos/base.md"):
            material = self.dados.carreira / relativo
            material.parent.mkdir(exist_ok=True)
            material.write_text("Material sintético de teste", encoding="utf-8")
        outra_base = self.dados.workspace / "outra base de exemplo"
        perfil = outra_base / "perfil/perfil-profissional.md"
        perfil.parent.mkdir(parents=True)
        perfil.write_text("# Perfil profissional\n\n[preencher: experiências]\n", encoding="utf-8")

        painel, _ = self.abrir_painel(boas_vindas=True)
        boas_vindas = painel.get_by_role("region", name="Boas-vindas ao Posicionar Carreira")
        verificar = boas_vindas.get_by_role("button", name="Verificar pasta")
        abrir = boas_vindas.get_by_role("button", name="Abrir vagas na base em uso")
        estado = boas_vindas.locator("#configuracao-status")
        expect(boas_vindas).to_be_visible()
        expect(painel.get_by_role("region", name="Lista de vagas")).to_be_hidden()
        expect(estado).to_contain_text("Base em uso")
        expect(abrir).to_be_visible()
        expect(boas_vindas.get_by_text("Pandoc, pdflatex e pypdf", exact=False)).to_be_visible()
        expect(boas_vindas.get_by_text("uma conta conectada", exact=False)).to_be_visible()
        expect(boas_vindas.get_by_text("ferramenta de transcrição na sessão", exact=False)).to_be_visible()
        curriculo = boas_vindas.get_by_role("button", name="Preparar currículo", exact=True)
        curriculo.click()
        expect(boas_vindas.locator("#configuracao-chat-status")).to_contain_text("Pedido enviado")
        self.assertEqual(
            self.mensagens[0]["content"][0]["text"],
            "Use $posicionar-carreira:posicionar-carreira. "
            "Ajude-me a escolher uma vaga e a preparar um currículo para ela. "
            "Siga o ciclo de otimização por vaga e apresente o resumo da revisão.",
        )
        boas_vindas.get_by_role("button", name="Revisar perfil e objetivos").click()
        expect(boas_vindas.locator("#configuracao-chat-status")).to_contain_text("Pedido enviado")
        self.assertIn("revisar meu perfil e meus objetivos", self.mensagens[1]["content"][0]["text"])

        campo = boas_vindas.get_by_label("Pasta de dados")
        campo.fill(str(outra_base))
        verificar.click()
        expect(estado).to_contain_text(f"Pasta verificada · {outra_base}")
        expect(boas_vindas.get_by_text("Perfil profissional · Rascunho")).to_be_visible()
        expect(boas_vindas.get_by_text("Oportunidades · Ausente", exact=False)).to_be_visible()
        expect(abrir).to_be_hidden()
        fluxo = boas_vindas.get_by_role("listitem").filter(has_text="Currículo e candidatura")
        fluxo.get_by_role("button", name="Configurar fluxo").click()
        expect(boas_vindas.locator("#configuracao-chat-status")).to_contain_text("Pedido enviado")
        mensagem = self.mensagens[-1]
        texto = mensagem["content"][0]["text"]
        self.assertIn("fluxo Currículo e candidatura", texto)
        self.assertIn("Peça minha confirmação antes de criar qualquer arquivo.", texto)
        self.assertIn(json.dumps(str(outra_base), ensure_ascii=False), texto)
        self.assertFalse((outra_base / "oportunidades").exists())

        campo.fill("")
        verificar.click()
        expect(abrir).to_be_visible()
        abrir.click()
        expect(painel.get_by_text("2 vagas", exact=True)).to_be_visible()
        expect(boas_vindas).to_be_hidden()
        painel.get_by_role("button", name="Boas-vindas", exact=True).click()
        expect(boas_vindas).to_be_visible()
        expect(estado).to_contain_text("Base em uso")

    def test_selecao_e_contexto_da_vaga(self):
        self.recusar_primeira = True
        painel, detalhe = self.abrir_painel()
        painel.get_by_role("button", name="Vaga de exemplo Empresa Exemplo · Triagem · Aberto").click()
        expect(detalhe.get_by_text("Empresa Exemplo · empresa-exemplo/local-001")).to_be_visible()
        painel.get_by_role("button", name="Vaga de exemplo Empresa Exemplo · Entrevista técnica · Encerrado").click()
        expect(detalhe.get_by_text(f"Empresa Exemplo · {self.vaga_id}")).to_be_visible()
        expect(detalhe.get_by_text("Reprovado", exact=True)).to_be_visible()
        expect(detalhe.get_by_text("Aguardar retorno")).to_be_visible()
        expect(detalhe.get_by_text("Data desconhecida · Retorno registrado")).to_be_visible()
        expect(detalhe.get_by_text("envios/curriculo-final.pdf · Versão em envios")).to_be_visible()
        self.assertEqual(self.selecoes, ["empresa-exemplo/local-001", self.vaga_id])

        preparar = painel.get_by_role("button", name="Preparar entrevista")
        preparar.click()
        expect(detalhe.get_by_role("status")).to_contain_text("O chat não recebeu o contexto.")
        expect(preparar).to_be_enabled()
        preparar.click()
        expect(detalhe.get_by_role("status")).to_have_text("O chat recebeu o contexto da vaga.")
        expect(preparar).to_be_disabled()
        self.assertEqual(len(self.mensagens), 2)
        self.assertEqual(self.mensagens[0], self.mensagens[1])
        self.assertEqual(self.mensagens[1]["role"], "user")
        processo = self.dossie / "processo.md"
        self.assertEqual(self.mensagens[1]["content"], [{
            "type": "text",
            "text": "Use $posicionar-carreira:posicionar-carreira para preparar a entrevista desta oportunidade.\n"
                    f"ID do processo: {self.vaga_id}\nArquivo oficial: {processo}",
        }])

        curriculo = detalhe.get_by_role("button", name="Preparar currículo", exact=True)
        curriculo.click()
        expect(curriculo).to_be_disabled()
        expect(detalhe.get_by_role("status")).to_have_text("O chat recebeu o contexto da vaga.")
        self.assertEqual(self.mensagens[2], {"role": "user", "content": [{
            "type": "text",
            "text": "Use $posicionar-carreira:posicionar-carreira para preparar o currículo desta oportunidade. "
                    "Siga o ciclo de otimização por vaga e apresente o resumo da revisão.\n"
                    f"ID do processo: {self.vaga_id}\nArquivo oficial: {processo}",
        }]})

    def test_abertura_independente_de_curriculos_do_dossie(self):
        primeiro_id = "empresa-exemplo/local-001"
        primeiro_md = self.dados.primeiro / "curriculo.md"
        primeiro_md.write_text("# Fonte fictícia", encoding="utf-8")
        painel, detalhe = self.abrir_painel()
        primeiro = painel.get_by_role("button", name="Vaga de exemplo Empresa Exemplo · Triagem · Aberto")
        segundo = painel.get_by_role("button", name="Vaga de exemplo Empresa Exemplo · Entrevista técnica · Encerrado")
        markdown = detalhe.get_by_role("button", name="Abrir currículo em Markdown", exact=True)
        pdf = detalhe.get_by_role("button", name="Abrir currículo em PDF", exact=True)
        pdf_enviado = detalhe.get_by_role("button", name="Abrir currículo enviado em PDF", exact=True)
        sucesso = detalhe.get_by_text("Abertura solicitada ao Windows.", exact=True)

        primeiro.click()
        expect(markdown).to_be_visible()
        expect(pdf).to_have_count(0)
        expect(pdf_enviado).to_have_count(0)
        markdown.click()
        expect(sucesso).to_be_visible()

        # A abertura é revalidada se o arquivo desaparecer após abrir o detalhe.
        primeiro_md.unlink()
        markdown.click()
        conflito = detalhe.get_by_text("O currículo disponível mudou. Reabra o detalhe da vaga.", exact=True)
        expect(conflito).to_be_visible()
        expect(markdown).to_be_enabled()

        segundo.click()
        expect(pdf_enviado).to_be_visible()
        expect(markdown).to_have_count(0)
        expect(pdf).to_have_count(0)
        pdf_enviado.click()
        expect(sucesso).to_be_visible()

        atual_pdf = self.dossie / "curriculo.pdf"
        atual_pdf.write_bytes(b"%PDF-1.4\n% Teste sintetico\n")
        atual_md = self.dossie / "curriculo.md"
        atual_md.write_text("# Fonte fictícia da segunda vaga", encoding="utf-8")
        pdf_enviado.click()
        expect(conflito).to_be_visible()
        segundo.click()
        expect(markdown).to_be_visible()
        expect(pdf).to_be_visible()
        expect(pdf_enviado).to_have_count(0)
        pdf.click()
        expect(sucesso).to_be_visible()

        primeiro.click()
        expect(detalhe.get_by_text(f"Empresa Exemplo · {primeiro_id}", exact=True)).to_be_visible()
        expect(detalhe.get_by_role("heading", name="Currículo", exact=True)).to_have_count(0)
        self.assertEqual(self.pedidos_de_abertura, [
            {"processo_id": primeiro_id, "tipo": "markdown", "enviado": False},
            {"processo_id": primeiro_id, "tipo": "markdown", "enviado": False},
            {"processo_id": self.vaga_id, "tipo": "pdf", "enviado": True},
            {"processo_id": self.vaga_id, "tipo": "pdf", "enviado": True},
            {"processo_id": self.vaga_id, "tipo": "pdf", "enviado": False},
        ])
        abertos = [json.loads(linha) for linha in self.aberturas.read_text("utf-8").splitlines()]
        self.assertEqual(abertos, [str(primeiro_md), str(self.material), str(atual_pdf)])
        self.assertEqual(self.mensagens, [])

    def test_configurar_monitoramento_geral_e_por_vaga(self):
        painel, detalhe = self.abrir_painel()
        painel.get_by_role("button", name="Monitorar novas vagas", exact=True).click()
        expect(painel.locator("#monitoramento-status")).to_have_text(
            "Pedido enviado. Continue a configuração no chat."
        )
        painel.get_by_role(
            "button", name="Vaga de exemplo Empresa Exemplo · Entrevista técnica · Encerrado"
        ).click()
        detalhe.get_by_role("button", name="Monitorar esta vaga", exact=True).click()
        expect(detalhe.get_by_role("status")).to_have_text(
            "Pedido enviado. Continue a configuração no chat."
        )
        geral, especifico = (item["content"][0]["text"] for item in self.mensagens)
        self.assertIn("novas vagas compatíveis", geral)
        self.assertNotIn("ID do processo:", geral)
        self.assertIn("retornos desta vaga", especifico)
        self.assertIn(
            f"ID do processo: {self.vaga_id}\nArquivo oficial: {self.dossie / 'processo.md'}",
            especifico,
        )

    def test_pesquisar_vagas_na_web_pelo_chat(self):
        painel, _ = self.abrir_painel()
        painel.get_by_role("button", name="Pesquisar vagas na web", exact=True).click()
        expect(painel.locator("#monitoramento-status")).to_have_text(
            "Pedido enviado. Acompanhe a pesquisa no chat."
        )
        pedido, = self.mensagens
        self.assertEqual(pedido["role"], "user")
        texto = pedido["content"][0]["text"]
        self.assertIn("$posicionar-carreira:posicionar-carreira", texto)
        self.assertIn("pesquisar vagas abertas na web", texto)
        self.assertIn("meu perfil e meus objetivos de carreira", texto)
        self.assertIn("sites de empresas e portais como Vagas.com, Gupy, Indeed e LinkedIn", texto)
        self.assertIn("Use o navegador", texto)
        self.assertIn("ordem de aderência", texto)
        self.assertIn("Aguarde meu pedido para cadastrar", texto)

    def test_planejar_busca_no_linkedin_pelo_chat(self):
        self.recusar_primeira = True
        painel, _ = self.abrir_painel()
        botao = painel.get_by_role("button", name="Planejar busca no LinkedIn", exact=True)
        feedback = painel.locator("#monitoramento-status")
        botao.click()
        expect(feedback).to_have_text(
            "O chat não recebeu o pedido. Você pode pedir no chat: planejar busca no LinkedIn."
        )
        expect(botao).to_be_enabled()
        botao.click()
        expect(feedback).to_have_text("Pedido enviado. Continue o planejamento no chat.")
        self.assertEqual(len(self.mensagens), 2)
        self.assertEqual(self.mensagens[0], self.mensagens[1])
        pedido = self.mensagens[1]
        self.assertEqual(pedido["role"], "user")
        texto = pedido["content"][0]["text"]
        self.assertIn("$posicionar-carreira:posicionar-carreira", texto)
        self.assertIn("objetivos de carreira", texto)
        self.assertIn("termos e filtros", texto)
        self.assertIn("como posso ativar o alerta oficial no LinkedIn", texto)
        self.assertIn("monitoramento por e-mail se eu quiser", texto)

    def test_editar_titulo_preservando_processo(self):
        processo = self.dossie / "processo.md"
        original = processo.read_text(encoding="utf-8")
        processo.write_text(original.replace("responsavel: empresa", "responsavel: titular"), encoding="utf-8")
        painel, detalhe = self.abrir_painel()
        vaga = detalhar(self.dados.carreira, self.vaga_id)
        corrigido = "Engenharia de Dados"
        fonte = "https://example.org/correcao"
        painel.get_by_role("button", name="Vaga de exemplo Empresa Exemplo · Entrevista técnica · Encerrado").click()
        detalhe.get_by_role("button", name="Editar processo").click()
        titulo = detalhe.get_by_label("Título da vaga")
        salvar = detalhe.get_by_role("button", name="Salvar alterações")
        expect(titulo).to_have_value(vaga["titulo"])
        expect(detalhe.get_by_label("Responsável")).to_have_value("titular")
        detalhe.get_by_label("Descrição do evento").fill("Corrigir título conforme o anúncio")
        detalhe.get_by_label("Fonte do evento").fill(fonte)

        titulo.fill(f"  {vaga['titulo']}  ")
        salvar.click()
        expect(detalhe.get_by_role("alert")).to_have_text("Altere um campo do processo ou use Registrar evento.")
        self.assertEqual(detalhar(self.dados.carreira, self.vaga_id)["revisao"], vaga["revisao"])

        titulo.fill(f"  {corrigido}  ")
        salvar.click()
        expect(detalhe.get_by_text("Processo atualizado.", exact=True)).to_be_visible()
        expect(detalhe.get_by_role("heading", name=corrigido)).to_be_visible()
        expect(painel.get_by_role("button", name=f"{corrigido} Empresa Exemplo · Entrevista técnica · Encerrado")).to_be_visible()
        vigente = detalhar(self.dados.carreira, self.vaga_id)
        self.assertEqual(vigente["id"], vaga["id"])
        self.assertEqual(vigente["processo"], vaga["processo"])
        self.assertEqual(vigente["responsavel"], "titular")
        self.assertEqual(vigente["eventos"][-1]["fonte"], fonte)
        self.assertEqual(vigente["eventos"][-1]["alteracoes"], {
            "titulo": {"anterior": vaga["titulo"], "atual": corrigido},
        })

    def test_editar_e_remover_disponibilidade_de_inscricao(self):
        painel, detalhe = self.abrir_painel()
        painel.get_by_role("button", name="Vaga de exemplo Empresa Exemplo · Triagem · Aberto").click()
        editar = detalhe.get_by_role("button", name="Editar processo")
        salvar = detalhe.get_by_role("button", name="Salvar alterações")
        disponibilidade = detalhe.get_by_label("Disponibilidade de inscrição")
        fonte = detalhe.get_by_label("Fonte da disponibilidade")
        fonte_anuncio = "https://example.org/anuncio"
        fonte_evento = "https://example.org/verificacao"

        editar.click()
        expect(disponibilidade).to_have_value("")
        expect(fonte).to_be_hidden()
        disponibilidade.select_option("anuncio_expirado")
        expect(fonte).to_have_attribute("required", "")
        fonte.fill(fonte_anuncio)
        detalhe.get_by_label("Descrição do evento").fill("Anúncio expirou")
        detalhe.get_by_label("Fonte do evento").fill(fonte_evento)
        salvar.click()
        expect(detalhe.get_by_text("Processo atualizado.", exact=True)).to_be_visible()
        expect(detalhe.get_by_text("Anúncio expirado", exact=True)).to_be_visible()

        editar.click()
        expect(disponibilidade).to_have_value("anuncio_expirado")
        expect(fonte).to_have_value(fonte_anuncio)
        disponibilidade.select_option("")
        expect(fonte).to_be_hidden()
        detalhe.get_by_label("Descrição do evento").fill("Remover registro desatualizado")
        detalhe.get_by_label("Fonte do evento").fill(fonte_evento)
        salvar.click()
        expect(detalhe.get_by_text("Processo atualizado.", exact=True)).to_be_visible()
        expect(detalhe.get_by_text("Anúncio expirado", exact=True)).to_have_count(0)
        vigente = detalhar(self.dados.carreira, "empresa-exemplo/local-001")
        self.assertIsNone(vigente["disponibilidade_inscricao"])
        self.assertIsNone(vigente["fonte_disponibilidade_inscricao"])

    def test_gestao_pelo_painel_e_conflito_de_edicao(self):
        painel, detalhe = self.abrir_painel()
        curadoria = self.dados.carreira / "painel-vagas.md"
        painel_original = curadoria.read_bytes()
        material_original = self.material.read_bytes()

        painel.get_by_role("button", name="Nova vaga").click()
        detalhe.get_by_label("Empresa", exact=True).fill("Empresa Nova")
        detalhe.get_by_label("Título da vaga").fill("Engenharia de teste")
        detalhe.get_by_label("Fonte da vaga").fill("https://example.org/vaga-nova")
        detalhe.get_by_role("button", name="Cadastrar vaga").click()
        expect(detalhe.get_by_text("Vaga cadastrada.", exact=True)).to_be_visible()
        expect(detalhe.get_by_text("Responsável: Pessoa Exemplo", exact=True)).to_be_visible()
        expect(painel.get_by_text("3 vagas", exact=True)).to_be_visible()
        novas = [vaga for vaga in listar(self.dados.carreira) if vaga["empresa"] == "Empresa Nova"]
        self.assertEqual(len(novas), 1)
        self.assertEqual(novas[0]["etapa"], "identificada")
        self.assertEqual(self.mensagens, [])
        processo_novo = detalhar(self.dados.carreira, novas[0]["id"])
        self.assertEqual(processo_novo["titulo_chat"], "candidatura empresa nova - identificada")
        detalhe.get_by_role("button", name="Usar vaga neste chat", exact=True).click()
        expect(detalhe.get_by_role("status")).to_have_text("O chat recebeu o contexto da vaga.")
        self.assertEqual(self.mensagens[0]["content"][0]["text"],
                         "Use $posicionar-carreira:posicionar-carreira para usar este chat no acompanhamento "
                         "desta oportunidade. Ajuste o título do chat.\n"
                         f"ID do processo: {processo_novo['id']}\nArquivo oficial: {processo_novo['processo']}")

        painel.get_by_role("button", name="Vaga de exemplo Empresa Exemplo · Entrevista técnica · Encerrado").click()
        detalhe.get_by_role("button", name="Registrar evento").click()
        detalhe.get_by_label("Descrição do evento").fill("Retorno adicional")
        detalhe.get_by_label("Fonte do evento").fill("https://example.org/retorno")
        detalhe.get_by_role("button", name="Salvar evento").click()
        expect(detalhe.get_by_text("Evento registrado.", exact=True)).to_be_visible()
        expect(detalhe.get_by_text("Data desconhecida · Retorno adicional")).to_be_visible()

        detalhe.get_by_role("button", name="Reabrir processo").click()
        expect(detalhe.get_by_label("Estado", exact=True)).to_have_value("aberto")
        detalhe.get_by_label("Prioridade", exact=True).select_option("alta")
        detalhe.get_by_label("Próxima ação").fill("Aguardar confirmação da entrevista")
        responsavel = detalhe.get_by_label("Responsável")
        expect(responsavel).to_have_value("empresa")
        self.assertCountEqual(responsavel.locator("option").all_text_contents(), ["Pessoa Exemplo", "Assistente", "Empresa"])
        responsavel.select_option("Pessoa Exemplo")
        detalhe.get_by_label("Prazo", exact=True).fill("2026-12-15")
        detalhe.get_by_label("Fonte do prazo").fill("https://example.org/prazo")
        detalhe.get_by_label("Descrição do evento").fill("Mesmo processo retomado")
        detalhe.get_by_label("Fonte do evento").fill("https://example.org/reabertura")
        detalhe.get_by_role("button", name="Salvar alterações").click()
        expect(detalhe.get_by_text("Processo atualizado.", exact=True)).to_be_visible()
        retomada = detalhar(self.dados.carreira, self.vaga_id)
        self.assertEqual(retomada["estado"], "aberto")
        self.assertIsNone(retomada["resultado"])
        self.assertEqual(retomada["prioridade"], "alta")
        self.assertEqual(retomada["responsavel"], "Pessoa Exemplo")
        self.assertEqual(retomada["prazo"], "2026-12-15")
        self.assertEqual(retomada["fonte_prazo"], "https://example.org/prazo")

        detalhe.get_by_role("button", name="Encerrar processo").click()
        expect(detalhe.get_by_label("Estado", exact=True)).to_have_value("encerrado")
        detalhe.get_by_label("Resultado", exact=True).select_option("reprovado")
        encerrada_em = date.today().isoformat()
        detalhe.get_by_label("Data de encerramento").fill(encerrada_em)
        detalhe.get_by_label("Descrição do evento").fill("Encerramento confirmado")
        detalhe.get_by_label("Fonte do evento").fill("https://example.org/encerramento")
        detalhe.get_by_role("button", name="Salvar alterações").click()
        expect(detalhe.get_by_text("Processo atualizado.", exact=True)).to_be_visible()
        expect(detalhe.get_by_text("Reprovado", exact=True)).to_be_visible()
        self.assertEqual(detalhar(self.dados.carreira, self.vaga_id)["encerrada_em"], encerrada_em)

        detalhe.get_by_role("button", name="Registrar evento").click()
        detalhe.get_by_label("Descrição do evento").fill("Rascunho durante edição externa")
        detalhe.get_by_label("Fonte do evento").fill("https://example.org/rascunho")
        processo = self.dossie / "processo.md"
        processo.write_bytes(processo.read_bytes() + b"\nEdicao externa.\n")
        externo = processo.read_bytes()
        detalhe.get_by_role("button", name="Salvar evento").click()
        expect(detalhe.get_by_role("alert")).to_contain_text("O processo mudou desde a abertura")
        expect(detalhe.get_by_label("Descrição do evento")).to_have_value("Rascunho durante edição externa")
        expect(detalhe.get_by_role("button", name="Salvar evento")).to_be_disabled()
        self.assertEqual(processo.read_bytes(), externo)
        detalhe.get_by_role("button", name="Recarregar processo").click()
        expect(detalhe.get_by_text("Reprovado", exact=True)).to_be_visible()

        painel.get_by_role("button", name="Vaga de exemplo Empresa Exemplo · Triagem · Aberto").click()
        detalhe.get_by_role("button", name="Editar processo").click()
        detalhe.get_by_label("Etapa", exact=True).select_option("candidatura_enviada")
        detalhe.get_by_label("Descrição do evento").fill("Recebido comprovante de envio")
        detalhe.get_by_label("Fonte do evento").fill("https://example.org/recibo")
        detalhe.get_by_role("button", name="Salvar alterações").click()
        expect(detalhe.get_by_role("heading", name="Editar processo")).to_be_visible()
        self.assertFalse(detalhar(self.dados.carreira, "empresa-exemplo/local-001")["candidatura_confirmada"])
        detalhe.get_by_label("Confirmo que a candidatura foi enviada").check()
        detalhe.get_by_label("Fonte do envio").fill("https://example.org/comprovante")
        detalhe.get_by_role("button", name="Salvar alterações").click()
        expect(detalhe.get_by_text("Processo atualizado.", exact=True)).to_be_visible()
        self.assertTrue(detalhar(self.dados.carreira, "empresa-exemplo/local-001")["candidatura_confirmada"])
        painel.get_by_role("button", name="Vaga de exemplo Empresa Exemplo · Entrevista técnica · Encerrado").click()

        painel.get_by_text("Filtros", exact=True).click()
        painel.get_by_label("Filtrar por estado").select_option("encerrado")
        painel.get_by_label("Filtrar por resultado").select_option("reprovado")
        expect(painel.get_by_text("1 de 3", exact=True)).to_be_visible()
        for titulo, acao in [
            ("Avaliar vaga", "avaliar a vaga"),
            ("Preparar currículo", "preparar o currículo"),
            ("Preparar candidatura", "preparar a candidatura"),
        ]:
            botao = detalhe.get_by_role("button", name=titulo, exact=True)
            botao.click()
            expect(botao).to_be_disabled()
            expect(detalhe.get_by_role("status")).to_have_text("O chat recebeu o contexto da vaga.")
            mensagem = self.mensagens[-1]["content"][0]["text"]
            self.assertIn(f"para {acao}", mensagem)
            self.assertIn(f"ID do processo: {self.vaga_id}\nArquivo oficial: {processo}", mensagem)
        self.assertEqual(curadoria.read_bytes(), painel_original)
        self.assertEqual(self.material.read_bytes(), material_original)


if __name__ == "__main__":
    unittest.main()
