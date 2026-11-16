import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


SERVIDOR = Path(__file__).resolve().parents[1] / "server/servidor.py"


class ConfiguracaoTest(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.workspace = Path(temp.name).resolve()
        self.raiz = self.workspace / "dados de teste"
        self.raiz.mkdir()

    def mcp(self, *chamadas, configurada=None):
        mensagens = [{"method": "initialize", "params": {"protocolVersion": "2025-11-25"}},
                     {"method": "tools/list"}]
        mensagens += [
            {"method": "tools/call", "params": {"name": ferramenta, "arguments": argumentos}}
            for ferramenta, argumentos in chamadas
        ]
        entrada = "".join(json.dumps({"jsonrpc": "2.0", "id": indice, **mensagem}) + "\n"
                          for indice, mensagem in enumerate(mensagens))
        resultado = subprocess.run(
            [sys.executable, "-B", "-u", str(SERVIDOR)], input=entrada,
            capture_output=True, encoding="utf-8", check=True, timeout=15,
            env={**os.environ, "CARREIRA_ROOT": str(configurada or self.workspace / "ausente")},
        )
        respostas = [json.loads(linha) for linha in resultado.stdout.splitlines()]
        self.assertEqual([msg["id"] for msg in respostas], list(range(len(mensagens))))
        self.assertTrue(all("result" in msg for msg in respostas), respostas)
        self.assertEqual(respostas[0]["result"]["serverInfo"]["name"], "posicionar-carreira-local")
        self.assertEqual(respostas[0]["result"]["serverInfo"]["version"], "0.6.2")
        ferramentas = {item["name"]: item for item in respostas[1]["result"]["tools"]}
        self.assertTrue(ferramentas["verificar_configuracao"]["annotations"]["readOnlyHint"])
        self.assertEqual(ferramentas["inicializar_carreira"]["inputSchema"]["required"], ["pasta"])
        return [resposta["result"] for resposta in respostas[2:]]

    def test_verifica_sem_base_e_inicializa_apenas_pasta_minima(self):
        absent, inspected, initialized, still_absent = self.mcp(
            ("verificar_configuracao", {}),
            ("verificar_configuracao", {"pasta": str(self.raiz)}),
            ("inicializar_carreira", {"pasta": str(self.raiz)}),
            ("verificar_configuracao", {}),
        )
        self.assertIsNone(absent["structuredContent"]["pasta"])
        self.assertFalse(inspected["structuredContent"]["base_configurada"])
        self.assertEqual(absent, still_absent)
        self.assertEqual(inspected["structuredContent"]["materiais"]["oportunidades"]["estado"], "ausente")
        estrutura = initialized["structuredContent"]
        self.assertEqual(estrutura["criados"], ["oportunidades/"])
        self.assertEqual(estrutura["fluxos"]["gestao_de_vagas"]["estado"], "fontes_disponiveis")
        self.assertEqual(estrutura["fluxos"]["candidatura"]["estado"], "fontes_pendentes")
        self.assertEqual(list(self.raiz.iterdir()), [self.raiz / "oportunidades"])

        lista, nova = self.mcp(
            ("listar_vagas", {}),
            ("criar_vaga", {"empresa": "Empresa Exemplo", "titulo": "Vaga exemplo", "fonte": "https://example.org/"}),
            configurada=self.raiz,
        )
        self.assertEqual(lista["structuredContent"]["vagas"], [])
        self.assertEqual(nova["structuredContent"]["responsavel"], "titular")
        self.assertEqual(nova["structuredContent"]["id"], "empresa-exemplo/local-001")

    def test_preserva_arquivos_e_identifica_rascunho_sem_mostrar_conteudo(self):
        perfil = self.raiz / "perfil/perfil-profissional.md"
        perfil.parent.mkdir()
        perfil.write_bytes(b"Conteudo privado de teste\r\n")
        processo = self.raiz / "oportunidades/empresa/local-001/processo.md"
        processo.parent.mkdir(parents=True)
        processo.write_bytes(b"Registro de teste\r\n")
        args = {"pasta": str(self.raiz), "modelos": ["perfil", "preferencias", "curriculo"]}
        before, initialized, repeated = self.mcp(
            ("verificar_configuracao", {}),
            ("inicializar_carreira", args),
            ("inicializar_carreira", args),
            configurada=self.raiz,
        )
        self.assertEqual(before["structuredContent"]["materiais"]["perfil"]["estado"], "disponivel")
        self.assertNotIn("Conteudo privado de teste", json.dumps([before, initialized, repeated]))
        dados = initialized["structuredContent"]
        self.assertEqual(dados["criados"], ["estrategia/referencias-candidaturas.md", "curriculos/base.md"])
        self.assertEqual(dados["materiais"]["preferencias"]["estado"], "rascunho")
        self.assertEqual(dados["materiais"]["curriculo"]["estado"], "rascunho")
        self.assertEqual(dados["materiais"]["portfolio"]["estado"], "ausente")
        self.assertTrue(dados["materiais"]["evidencias"]["opcional"])
        self.assertEqual(repeated["structuredContent"]["criados"], [])
        self.assertEqual(perfil.read_bytes(), b"Conteudo privado de teste\r\n")
        self.assertEqual(processo.read_bytes(), b"Registro de teste\r\n")

    def test_reconhece_materiais_de_outra_pessoa_sem_trocar_a_base(self):
        selecionada = self.workspace / "segunda identidade"
        (selecionada / "oportunidades").mkdir(parents=True)
        for relative in ("perfil/perfil-profissional.md", "estrategia/referencias-candidaturas.md",
                         "curriculos/base.md", "portfolio/caso-exemplo.md"):
            arquivo = selecionada / relative
            arquivo.parent.mkdir(exist_ok=True)
            arquivo.write_text("Material sintético de outra pessoa.", encoding="utf-8")
        atual, outra = self.mcp(
            ("verificar_configuracao", {}),
            ("verificar_configuracao", {"pasta": str(selecionada)}),
            configurada=self.raiz,
        )
        self.assertTrue(atual["structuredContent"]["base_configurada"])
        self.assertFalse(outra["structuredContent"]["base_configurada"])
        self.assertEqual(outra["structuredContent"]["pasta"], str(selecionada))
        self.assertTrue(all(fluxo["estado"] == "fontes_disponiveis"
                            for fluxo in outra["structuredContent"]["fluxos"].values()))
        self.assertFalse((self.raiz / "oportunidades").exists())

    def test_recusa_caminho_relativo_e_modelo_desconhecido_sem_gravar(self):
        relative, invalid = self.mcp(
            ("inicializar_carreira", {"pasta": "."}),
            ("inicializar_carreira", {"pasta": str(self.raiz), "modelos": ["../fora"]}),
        )
        self.assertTrue(relative["isError"])
        self.assertTrue(invalid["isError"])
        self.assertEqual(list(self.raiz.iterdir()), [])

    def test_reconhece_objetivos_da_versao_publica_anterior(self):
        objetivos = self.raiz / "estrategia/objetivos.md"
        objetivos.parent.mkdir()
        objetivos.write_bytes(b"# Objetivos reais de teste\n")
        preferencias = self.raiz / "estrategia/referencias-candidaturas.md"
        args = {"pasta": str(self.raiz), "modelos": ["preferencias"]}
        before, initialized = self.mcp(
            ("verificar_configuracao", {}),
            ("inicializar_carreira", args),
            configurada=self.raiz,
        )
        self.assertEqual(before["structuredContent"]["materiais"]["preferencias"], {
            "caminho": "estrategia/objetivos.md", "estado": "disponivel",
        })
        self.assertEqual(initialized["structuredContent"]["criados"], ["oportunidades/"])
        self.assertFalse(preferencias.exists())
        self.assertEqual(objetivos.read_bytes(), b"# Objetivos reais de teste\n")

        preferencias.write_text("# Preferências\n\n[preencher: condições]\n", encoding="utf-8")
        atual, = self.mcp(("verificar_configuracao", {}), configurada=self.raiz)
        self.assertEqual(atual["structuredContent"]["materiais"]["preferencias"]["caminho"],
                         "estrategia/objetivos.md")

    def test_recusa_pasta_de_modelo_redirecionada_para_fora_da_base(self):
        destino = self.workspace / "externo"
        destino.mkdir()
        try:
            (self.raiz / "perfil").symlink_to(destino, target_is_directory=True)
        except OSError:
            self.skipTest("A criação de links simbólicos não está disponível neste ambiente.")
        antes, resultado = self.mcp(
            ("verificar_configuracao", {"pasta": str(self.raiz)}),
            ("inicializar_carreira", {"pasta": str(self.raiz), "modelos": ["perfil"]}),
        )
        self.assertEqual(antes["structuredContent"]["materiais"]["perfil"]["estado"], "indisponivel")
        self.assertTrue(resultado["isError"])
        self.assertEqual(list(destino.iterdir()), [])
        self.assertFalse((self.raiz / "oportunidades").exists())
