from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from hashlib import sha256
from threading import Barrier
import unittest

import test_dados
from dados import detalhar, listar
from gestao_vagas import metadata
from operacoes import atualizar_vaga, criar_vaga, registrar_evento


FONTE = "https://example.org/evidencia"
PRIMEIRO_ID = "empresa-exemplo/local-001"
SEGUNDO_ID = "empresa-exemplo/local-002"


class OperacoesTest(unittest.TestCase):
    def setUp(self):
        dados = test_dados.DadosTest()
        self.addCleanup(dados.doCleanups)
        dados.setUp()
        self.carreira = dados.carreira
        self.primeiro = dados.primeiro / "processo.md"
        self.segundo = dados.carreira / "oportunidades" / SEGUNDO_ID / "processo.md"
        self.painel = dados.carreira / "painel-vagas.md"

    def atual(self, processo_id=PRIMEIRO_ID):
        return detalhar(self.carreira, processo_id)

    def atualizar(self, mudancas, processo_id=PRIMEIRO_ID, descricao="Mudança registrada"):
        return atualizar_vaga(
            self.carreira, processo_id, self.atual(processo_id)["revisao"], descricao,
            FONTE, mudancas,
        )

    def test_grava_status_e_historico_seguindo_o_fluxo(self):
        for proibido in ("entrevistas", "oferta", "reprovado", "pausado"):
            with self.subTest(proibido=proibido), self.assertRaisesRegex(ValueError, "Transição de status"):
                self.atualizar({"status": proibido})
        self.atualizar({
            "status": "candidatura-enviada", "candidatura_confirmada": True, "fonte_candidatura": FONTE,
        }, descricao="Envio confirmado")
        atualizada = self.atualizar({"status": "entrevistas"}, descricao="Entrevista confirmada")
        self.assertEqual(atualizada["status"], "entrevistas")
        self.assertEqual(atualizada["eventos"][-1]["alteracoes"]["status"], {
            "anterior": "candidatura-enviada", "atual": "entrevistas",
        })
        registro = metadata(self.primeiro)
        self.assertEqual(registro["status"], "entrevistas")
        self.assertFalse(registro.keys() & {"estado", "etapa", "resultado"})

    def test_cria_processo_sem_inventar_envio_e_recusa_duplicatas(self):
        painel = self.painel.read_bytes()
        identificador = "outra-empresa/local-002"
        criado = criar_vaga(self.carreira, "Outra Empresa", "Vaga nova", FONTE, identificador)
        self.assertEqual(criado["id"], identificador)
        self.assertEqual(criado["status"], "identificada")
        self.assertFalse(criado["candidatura_confirmada"])
        self.assertEqual(criado["eventos"][0]["fonte"], FONTE)
        self.assertEqual(self.atual(identificador), criado)
        self.assertEqual(self.painel.read_bytes(), painel)
        for empresa, fonte, processo_id in (
            ("Outra Empresa", "https://example.org/segunda", identificador),
            ("Outro cadastro", FONTE, "outro-cadastro/local-001"),
        ):
            with self.subTest(processo_id=processo_id), self.assertRaises(ValueError):
                criar_vaga(self.carreira, empresa, "Vaga nova", fonte, processo_id)
        self.assertEqual(len(listar(self.carreira)), 3)
        self.assertEqual(self.atual(identificador), criado)

    def test_arquivar_fonte_preserva_processo_e_permite_corrigir_referencia(self):
        fonte = self.carreira / "consulta.md"
        fonte.write_text("Formulário de inscrição acessível.", encoding="utf-8")
        processo_id = "outra-empresa/local-001"
        criado = criar_vaga(self.carreira, "Outra Empresa", "Vaga nova", fonte.name, processo_id)
        antes = atualizar_vaga(
            self.carreira, processo_id, criado["revisao"], "Inscrição conferida", fonte.name,
            {"disponibilidade_inscricao": "aberta_verificada", "fonte_disponibilidade_inscricao": fonte.name},
        )
        arquivada = self.carreira / "archive" / fonte.name
        arquivada.parent.mkdir()
        fonte.rename(arquivada)

        lista = {vaga["id"]: vaga for vaga in listar(self.carreira)}
        self.assertEqual(lista[processo_id]["status"], antes["status"])
        atual = self.atual(processo_id)
        for campo in ("revisao", "eventos", "disponibilidade_inscricao", "fonte_disponibilidade_inscricao"):
            self.assertEqual(atual[campo], antes[campo])
        outro = criar_vaga(self.carreira, "Outro Cadastro", "Outra vaga", FONTE)
        self.assertEqual(outro["status"], "identificada")

        ref = arquivada.relative_to(self.carreira).as_posix()
        corrigido = atualizar_vaga(
            self.carreira, processo_id, atual["revisao"], "Referência atualizada após arquivar", ref,
            {"fonte_disponibilidade_inscricao": ref},
        )
        self.assertEqual(corrigido["fonte_disponibilidade_inscricao"], ref)
        self.assertEqual(corrigido["eventos"][:-1], antes["eventos"])
        processo = self.carreira / "oportunidades" / processo_id / "processo.md"
        salvo = processo.read_bytes()
        with self.assertRaisesRegex(ValueError, "Fonte local inexistente"):
            atualizar_vaga(
                self.carreira, processo_id, corrigido["revisao"], "Fonte incorreta", FONTE,
                {"fonte_disponibilidade_inscricao": "nao-existe.md"},
            )
        self.assertEqual(processo.read_bytes(), salvo)

    def test_registra_evento_preservando_corpo_metadados_painel_e_envios(self):
        original = self.primeiro.read_bytes().replace(
            b"---\r\n# Processo", b"observacao_manual: preservar\r\n---\r\n# Processo"
        ).replace(b"---\n# Processo", b"observacao_manual: preservar\n---\n# Processo")
        original = b"---\r\n" + original.split(b"\n", 1)[1].replace(b"\r\n", b"\n")
        corpo = b"\r\n# Anotacao manual\r\n\r\n  Preservar espacos.  \r\n"
        self.primeiro.write_bytes(original + corpo)
        material = self.primeiro.parent / "envios/2026-10-01/cv.pdf"
        material.parent.mkdir(parents=True)
        material.write_bytes(b"material enviado")
        painel = self.painel.read_bytes()
        outro = self.segundo.read_bytes()
        revisao = self.atual()["revisao"]
        self.assertEqual(revisao, sha256(original + corpo).hexdigest())

        salvo = registrar_evento(self.carreira, PRIMEIRO_ID, revisao, "Retorno adicional", FONTE)
        self.assertEqual(salvo["status"], "identificada")
        self.assertEqual([e["descricao"] for e in salvo["eventos"]], [
            "Retorno registrado", "Retorno adicional",
        ])
        self.assertIsNone(salvo["eventos"][-1]["data"])
        self.assertNotEqual(salvo["revisao"], revisao)
        self.assertEqual(salvo["materiais"], [
            {"caminho": "envios/2026-10-01/cv.pdf", "tipo": "envio"},
        ])
        novo = self.primeiro.read_bytes()
        self.assertIn(b"observacao_manual: preservar", novo)
        self.assertTrue(novo.endswith(corpo))
        self.assertEqual(salvo["revisao"], sha256(novo).hexdigest())
        self.assertEqual(material.read_bytes(), b"material enviado")
        self.assertEqual(self.painel.read_bytes(), painel)
        self.assertEqual(self.segundo.read_bytes(), outro)
        with self.assertRaisesRegex(ValueError, "O processo mudou"):
            registrar_evento(self.carreira, PRIMEIRO_ID, revisao, "Registro antigo", FONTE)
        with self.assertRaisesRegex(ValueError, "já foi registrado"):
            registrar_evento(self.carreira, PRIMEIRO_ID, salvo["revisao"], "Retorno adicional", FONTE)
        self.assertEqual(self.primeiro.read_bytes(), novo)

    def test_previas_validam_sem_gravar_processo_ou_painel(self):
        painel = self.painel.read_bytes()
        original = self.primeiro.read_bytes()
        revisao = self.atual()["revisao"]
        previa = criar_vaga(self.carreira, "Outra empresa", "Vaga nova", FONTE, previa=True)
        self.assertEqual(previa["processo"]["status"], "identificada")
        self.assertEqual(len(listar(self.carreira)), 2)

        evento = registrar_evento(self.carreira, PRIMEIRO_ID, revisao, "Novo evento", FONTE, previa=True)
        self.assertEqual(evento["evento"]["descricao"], "Novo evento")
        mudanca = atualizar_vaga(
            self.carreira, PRIMEIRO_ID, revisao, "Mudança", FONTE, {"status": "descartada"}, previa=True,
        )
        self.assertEqual(mudanca["mudancas"]["status"], "descartada")
        self.assertEqual(mudanca["revisao"], revisao)
        self.assertEqual(self.primeiro.read_bytes(), original)
        self.assertEqual(self.painel.read_bytes(), painel)

    def test_exige_evidencia_para_registrar_candidatura(self):
        anterior = self.primeiro.read_bytes()
        for mudancas in (
            {"status": "candidatura-enviada"},
            {"status": "candidatura-enviada", "candidatura_confirmada": True},
        ):
            with self.subTest(mudancas=mudancas), self.assertRaises(ValueError):
                self.atualizar(mudancas)
            self.assertEqual(self.primeiro.read_bytes(), anterior)
        salvo = self.atualizar({
            "status": "candidatura-enviada",
            "candidatura_confirmada": True,
            "fonte_candidatura": FONTE,
        })
        self.assertEqual(salvo["status"], "candidatura-enviada")
        self.assertTrue(salvo["candidatura_confirmada"])
        self.assertIsNone(salvo["candidatura_em"])
        self.assertEqual(salvo["fonte_candidatura"], FONTE)

    def test_status_final_preserva_edicao_sem_permitir_transicoes(self):
        anterior = self.segundo.read_bytes().replace(
            b"status: reprovado", b"encerrada_em: '2026-10-12'\nstatus: reprovado",
        )
        self.segundo.write_bytes(anterior)
        with self.assertRaisesRegex(ValueError, "Transição de status"):
            self.atualizar({"status": "identificada"}, SEGUNDO_ID)
        self.assertEqual(self.segundo.read_bytes(), anterior)
        registro = self.atualizar({"proxima_acao": "Registrar feedback"}, SEGUNDO_ID)
        self.assertEqual(registro["status"], "reprovado")
        self.assertEqual(registro["encerrada_em"], "2026-10-12")

    def test_recusa_datas_futuras_de_evento_envio_e_encerramento(self):
        futuro = (date.today() + timedelta(days=3)).isoformat()
        anterior = self.primeiro.read_bytes()
        with self.assertRaises(ValueError):
            registrar_evento(
                self.carreira, PRIMEIRO_ID, self.atual()["revisao"], "Evento futuro", FONTE, futuro,
            )
        for mudancas in (
            {"status": "descartada", "encerrada_em": futuro},
            {"candidatura_confirmada": True, "candidatura_em": futuro, "fonte_candidatura": FONTE},
            {"prazo": futuro},
        ):
            with self.subTest(mudancas=mudancas), self.assertRaises(ValueError):
                self.atualizar(mudancas)
        self.assertEqual(self.primeiro.read_bytes(), anterior)
        prazo = self.atualizar({"prazo": futuro, "fonte_prazo": FONTE})
        self.assertEqual(prazo["prazo"], futuro)

    def test_operacoes_concorrentes_com_mesma_revisao_gravam_um_evento(self):
        revisao = self.atual()["revisao"]
        inicio = Barrier(2, timeout=5)

        def registrar(descricao):
            inicio.wait()
            try:
                registrar_evento(self.carreira, PRIMEIRO_ID, revisao, descricao, FONTE)
            except (ValueError, OSError):
                return False
            return True

        with ThreadPoolExecutor(2) as executores:
            resultados = list(executores.map(registrar, ("Evento A", "Evento B")))
        self.assertEqual(sum(resultados), 1)
        self.assertEqual(len(self.atual()["eventos"]), 2)


if __name__ == "__main__":
    unittest.main()
