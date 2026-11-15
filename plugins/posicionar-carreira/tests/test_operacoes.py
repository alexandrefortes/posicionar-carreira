from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from hashlib import sha256
from threading import Barrier
import unittest

import test_dados
from dados import detalhar, listar
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

    def test_cria_processo_sem_inventar_envio_e_recusa_duplicatas(self):
        painel = self.painel.read_bytes()
        identificador = "outra-empresa/local-002"
        criado = criar_vaga(self.carreira, "Outra Empresa", "Vaga nova", FONTE, identificador)
        self.assertEqual(criado["id"], identificador)
        self.assertEqual(criado["etapa"], "identificada")
        self.assertEqual(criado["estado"], "aberto")
        self.assertIsNone(criado["resultado"])
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
        self.assertEqual(salvo["etapa"], "triagem")
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
        self.assertEqual(previa["processo"]["etapa"], "identificada")
        self.assertEqual(len(listar(self.carreira)), 2)

        evento = registrar_evento(self.carreira, PRIMEIRO_ID, revisao, "Novo evento", FONTE, previa=True)
        self.assertEqual(evento["evento"]["descricao"], "Novo evento")
        mudanca = atualizar_vaga(
            self.carreira, PRIMEIRO_ID, revisao, "Mudança", FONTE, {"estado": "pausado"}, previa=True,
        )
        self.assertEqual(mudanca["mudancas"]["estado"], "pausado")
        self.assertEqual(mudanca["revisao"], revisao)
        self.assertEqual(self.primeiro.read_bytes(), original)
        self.assertEqual(self.painel.read_bytes(), painel)

    def test_exige_evidencia_para_registrar_candidatura(self):
        anterior = self.primeiro.read_bytes()
        for mudancas in (
            {"etapa": "candidatura_enviada"},
            {"etapa": "candidatura_enviada", "candidatura_confirmada": True},
        ):
            with self.subTest(mudancas=mudancas), self.assertRaises(ValueError):
                self.atualizar(mudancas)
            self.assertEqual(self.primeiro.read_bytes(), anterior)
        salvo = self.atualizar({
            "etapa": "candidatura_enviada",
            "candidatura_confirmada": True,
            "fonte_candidatura": FONTE,
        })
        self.assertEqual(salvo["etapa"], "candidatura_enviada")
        self.assertTrue(salvo["candidatura_confirmada"])
        self.assertIsNone(salvo["candidatura_em"])
        self.assertEqual(salvo["fonte_candidatura"], FONTE)

    def test_reabertura_precisa_de_mudanca_explicita_de_estado(self):
        anterior = self.segundo.read_bytes().replace(
            b"estado: encerrado", b"encerrada_em: '2026-10-12'\nestado: encerrado",
        )
        self.segundo.write_bytes(anterior)
        with self.assertRaises(ValueError):
            self.atualizar({"estado": "aberto", "resultado": "reprovado"}, SEGUNDO_ID)
        self.assertEqual(self.segundo.read_bytes(), anterior)
        registro = self.atualizar({"proxima_acao": "Registrar feedback"}, SEGUNDO_ID)
        self.assertEqual(registro["estado"], "encerrado")
        self.assertEqual(registro["resultado"], "reprovado")
        self.assertEqual(registro["encerrada_em"], "2026-10-12")

        aberto = self.atualizar({"estado": "aberto", "etapa": "triagem"}, SEGUNDO_ID, "Reabertura confirmada")
        self.assertEqual(aberto["estado"], "aberto")
        self.assertEqual(aberto["etapa"], "triagem")
        self.assertIsNone(aberto["resultado"])
        self.assertIsNone(aberto["encerrada_em"])
        self.assertEqual(aberto["eventos"][:-1], registro["eventos"])

    def test_recusa_datas_futuras_de_evento_envio_e_encerramento(self):
        futuro = (date.today() + timedelta(days=3)).isoformat()
        anterior = self.primeiro.read_bytes()
        with self.assertRaises(ValueError):
            registrar_evento(
                self.carreira, PRIMEIRO_ID, self.atual()["revisao"], "Evento futuro", FONTE, futuro,
            )
        for mudancas in (
            {"estado": "encerrado", "resultado": "reprovado", "encerrada_em": futuro},
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
