import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from contextlib import ExitStack
from hashlib import sha256

import test_dados


PROCESSO_ID = "empresa-exemplo/local-001"
DISPONIBILIDADE = "disponibilidade_inscricao"
FONTE_DISPONIBILIDADE = "fonte_disponibilidade_inscricao"
FONTE_EVENTO = "https://example.org/evento"
FONTE_ANUNCIO = "https://example.org/anuncio"
FONTE_LOCAL = "evidencia.md"


class ServidorTest(unittest.TestCase):
    def setUp(self):
        self.dados = test_dados.DadosTest()
        self.addCleanup(self.dados.doCleanups)
        self.dados.setUp()
        self.processo = self.dados.primeiro / "processo.md"
        self.painel = self.dados.carreira / "painel-vagas.md"
        (self.dados.carreira / FONTE_LOCAL).write_text("Evidência sintética", encoding="utf-8")
        recursos = ExitStack()
        self.addCleanup(recursos.close)
        self.servidor = recursos.enter_context(subprocess.Popen(
            [sys.executable, "-B", "-u", str(test_dados.PLUGIN / "server/servidor.py")],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding="utf-8",
            cwd=test_dados.PLUGIN, env={**os.environ, "CARREIRA_ROOT": str(self.dados.carreira)},
        ))
        recursos.callback(self.servidor.stdin.close)
        self.id_rpc = 0
        self.mcp("initialize", {
            "protocolVersion": "2025-11-25", "capabilities": {},
            "clientInfo": {"name": "teste-servidor", "version": "1"},
        })
        self.enviar({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def enviar(self, mensagem):
        self.servidor.stdin.write(json.dumps(mensagem) + "\n")
        self.servidor.stdin.flush()

    def mcp(self, metodo, params=None):
        self.id_rpc += 1
        self.enviar({"jsonrpc": "2.0", "id": self.id_rpc, "method": metodo, "params": params or {}})
        resposta = json.loads(self.servidor.stdout.readline())
        self.assertEqual(resposta["id"], self.id_rpc)
        self.assertNotIn("error", resposta)
        return resposta["result"]

    def detalhe(self, processo_id=PROCESSO_ID):
        return self.mcp("tools/call", {
            "name": "detalhar_vaga", "arguments": {"processo_id": processo_id},
        })["structuredContent"]

    def atualizar(self, atual, mudancas, descricao, *, fonte=FONTE_EVENTO):
        return self.mcp("tools/call", {"name": "atualizar_vaga", "arguments": {
            "processo_id": atual["id"], "revisao": atual["revisao"], "mudancas": mudancas,
            "descricao": descricao, "fonte": fonte,
        }})

    def verificar_mudanca(self, anterior, mudancas, esperado, descricao):
        resposta = self.atualizar(anterior, mudancas, descricao)
        self.assertFalse(resposta.get("isError"), resposta)
        atual = resposta["structuredContent"]
        self.assertEqual(atual, self.detalhe(anterior["id"]))
        self.assertNotEqual(atual["revisao"], anterior["revisao"])
        self.assertEqual(atual["revisao"], sha256(Path(atual["processo"]).read_bytes()).hexdigest())
        self.assertEqual(atual["eventos"][:-1], anterior["eventos"])
        evento = atual["eventos"][-1]
        self.assertEqual(evento["descricao"], descricao)
        self.assertEqual(evento["fonte"], FONTE_EVENTO)
        self.assertEqual(evento["alteracoes"], {
            campo: {"anterior": anterior[campo], "atual": valor} for campo, valor in esperado.items()
        })
        for campo, valor in esperado.items():
            self.assertEqual(atual[campo], valor)
        return atual

    def test_mcp_cadastra_e_registra_evento_com_responsavel_configurado(self):
        resposta = self.mcp("tools/call", {"name": "criar_vaga", "arguments": {
            "empresa": "Outra Empresa", "titulo": "Nova Vaga", "fonte": FONTE_ANUNCIO,
        }})
        self.assertFalse(resposta.get("isError"), resposta)
        vaga = resposta["structuredContent"]
        self.assertEqual(vaga["responsavel"], "Pessoa Exemplo")
        self.assertEqual(vaga["responsaveis"], ["Pessoa Exemplo", "assistente", "empresa"])
        resposta = self.mcp("tools/call", {"name": "registrar_evento", "arguments": {
            "processo_id": vaga["id"], "revisao": vaga["revisao"],
            "descricao": "Retorno recebido", "fonte": FONTE_EVENTO,
        }})
        self.assertFalse(resposta.get("isError"), resposta)
        registrada = self.detalhe(vaga["id"])
        self.assertEqual(registrada["eventos"][-1]["fonte"], FONTE_EVENTO)
        self.assertEqual(registrada["eventos"][:-1], vaga["eventos"])

    def test_mcp_publica_campos_e_grava_par_com_historico_e_revisao(self):
        ferramenta = next(tool for tool in self.mcp("tools/list")["tools"]
                          if tool["name"] == "atualizar_vaga")
        mudancas = ferramenta["inputSchema"]["properties"]["mudancas"]["properties"]
        self.assertEqual(set(mudancas[DISPONIBILIDADE]["enum"]),
                         {"aberta_verificada", "nao_confirmada", "anuncio_expirado", None})
        self.assertEqual(set(mudancas[FONTE_DISPONIBILIDADE]["type"]), {"string", "null"})

        painel_original = self.painel.read_bytes()
        anterior = self.detalhe()
        self.assertIsNone(anterior[DISPONIBILIDADE])
        self.assertIsNone(anterior[FONTE_DISPONIBILIDADE])
        mudancas = {DISPONIBILIDADE: "aberta_verificada", FONTE_DISPONIBILIDADE: FONTE_ANUNCIO}
        aberta = self.verificar_mudanca(anterior, mudancas, mudancas, "Inscrições verificadas")
        conflito = self.atualizar(anterior, {
            DISPONIBILIDADE: "nao_confirmada", FONTE_DISPONIBILIDADE: FONTE_ANUNCIO,
        }, "Revisão antiga")
        self.assertTrue(conflito.get("isError"), conflito)
        self.assertIn("O processo mudou", conflito["content"][0]["text"])
        self.assertEqual(self.detalhe(), aberta)

        mudancas = {DISPONIBILIDADE: "anuncio_expirado", FONTE_DISPONIBILIDADE: FONTE_LOCAL}
        expirada = self.verificar_mudanca(aberta, mudancas, mudancas, "Anúncio expirado")
        mudancas = {FONTE_DISPONIBILIDADE: FONTE_ANUNCIO}
        nova_fonte = self.verificar_mudanca(expirada, mudancas, mudancas, "Fonte corrigida")
        self.verificar_mudanca(nova_fonte, {DISPONIBILIDADE: None},
                               {DISPONIBILIDADE: None, FONTE_DISPONIBILIDADE: None},
                               "Registro de disponibilidade removido")
        self.assertEqual(self.painel.read_bytes(), painel_original)

    def test_mcp_rejeita_fonte_ausente_ou_invalida_sem_gravar(self):
        anterior = self.detalhe()
        original = self.processo.read_bytes()
        for mudancas, mensagem in (
            ({DISPONIBILIDADE: "aberta_verificada"}, "Informe a fonte da disponibilidade"),
            ({DISPONIBILIDADE: "aberta_verificada", FONTE_DISPONIBILIDADE: ""}, "Informe a fonte da disponibilidade"),
            ({DISPONIBILIDADE: "aberta_verificada", FONTE_DISPONIBILIDADE: "https://"}, "Informe uma URL completa"),
            ({DISPONIBILIDADE: "aberta_verificada", FONTE_DISPONIBILIDADE: "inexistente.md"}, "Fonte local inexistente"),
            ({DISPONIBILIDADE: "outro", FONTE_DISPONIBILIDADE: FONTE_ANUNCIO}, "Disponibilidade de inscrição inválida"),
            ({DISPONIBILIDADE: "", FONTE_DISPONIBILIDADE: FONTE_ANUNCIO}, "Disponibilidade de inscrição inválida"),
            ({FONTE_DISPONIBILIDADE: FONTE_ANUNCIO}, "Informe a disponibilidade de inscrição"),
            ({DISPONIBILIDADE: None, FONTE_DISPONIBILIDADE: FONTE_ANUNCIO}, "Informe a disponibilidade de inscrição"),
        ):
            with self.subTest(mudancas=mudancas):
                resposta = self.atualizar(anterior, mudancas, "Tentativa com dado inválido")
                self.assertTrue(resposta.get("isError"), resposta)
                self.assertIn(mensagem, resposta["content"][0]["text"])
                self.assertEqual(self.processo.read_bytes(), original)
        self.assertEqual(self.detalhe(), anterior)

    def test_mcp_preserva_processo_existente_e_exige_fonte_ao_mudar_disponibilidade(self):
        processo = self.dados.criar_processo(
            "local-003", "2026-10-10",
            disponibilidade_inscricao="nao_confirmada", fonte_disponibilidade_inscricao=FONTE_ANUNCIO,
        ) / "processo.md"
        legado = self.detalhe("empresa-exemplo/local-003")
        self.assertEqual(legado[DISPONIBILIDADE], "nao_confirmada")
        self.assertEqual(legado[FONTE_DISPONIBILIDADE], FONTE_ANUNCIO)
        original = processo.read_bytes()
        for mudancas in (
            {DISPONIBILIDADE: "aberta_verificada"},
            {FONTE_DISPONIBILIDADE: None},
        ):
            with self.subTest(mudancas=mudancas):
                resposta = self.atualizar(legado, mudancas, "Tentativa sem nova fonte")
                self.assertTrue(resposta.get("isError"), resposta)
                self.assertIn("Informe a fonte da disponibilidade", resposta["content"][0]["text"])
                self.assertEqual(processo.read_bytes(), original)
        mudancas = {"prioridade": "alta"}
        atualizado = self.verificar_mudanca(legado, mudancas, mudancas, "Prioridade revisada")
        self.assertEqual(atualizado[DISPONIBILIDADE], legado[DISPONIBILIDADE])
        self.assertEqual(atualizado[FONTE_DISPONIBILIDADE], legado[FONTE_DISPONIBILIDADE])

    def test_mcp_corrige_titulo_preservando_id_e_dossie(self):
        ferramenta = next(tool for tool in self.mcp("tools/list")["tools"]
                          if tool["name"] == "atualizar_vaga")
        schema = ferramenta["inputSchema"]
        titulo = schema["properties"]["mudancas"]["properties"]["titulo"]
        self.assertEqual(titulo["type"], "string")
        self.assertIn("fonte", schema["required"])

        anterior = self.detalhe()
        painel_original = self.painel.read_bytes()
        corrigido = self.verificar_mudanca(
            anterior, {"titulo": "  Gerência de Dados  "}, {"titulo": "Gerência de Dados"},
            "Título corrigido conforme o anúncio",
        )
        self.assertEqual(corrigido["id"], anterior["id"])
        self.assertEqual(corrigido["processo"], anterior["processo"])
        vagas = self.mcp("tools/call", {"name": "listar_vagas"})["structuredContent"]["vagas"]
        vaga = next(vaga for vaga in vagas if vaga["id"] == anterior["id"])
        self.assertEqual(vaga["titulo"], corrigido["titulo"])

        corrigido_original = self.processo.read_bytes()
        resposta = self.atualizar(anterior, {"titulo": "Título obsoleto"}, "Tentativa desatualizada")
        self.assertTrue(resposta.get("isError"), resposta)
        self.assertIn("O processo mudou", resposta["content"][0]["text"])
        self.assertEqual(self.processo.read_bytes(), corrigido_original)
        self.assertEqual(self.painel.read_bytes(), painel_original)

    def test_mcp_recusa_titulo_sem_valor_ou_evidencia(self):
        anterior = self.detalhe()
        original = self.processo.read_bytes()
        for titulo, fonte, mensagem in (
            (None, FONTE_EVENTO, "Preencha o título da vaga"),
            ("  ", FONTE_EVENTO, "Preencha o título da vaga"),
            ("Título corrigido", None, "Preencha a fonte"),
            ("Título corrigido", "https://", "Informe uma URL completa"),
        ):
            with self.subTest(titulo=titulo, fonte=fonte):
                resposta = self.atualizar(anterior, {"titulo": titulo}, "Tentativa inválida", fonte=fonte)
                self.assertTrue(resposta.get("isError"), resposta)
                self.assertIn(mensagem, resposta["content"][0]["text"])
                self.assertEqual(self.processo.read_bytes(), original)
