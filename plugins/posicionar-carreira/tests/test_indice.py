import unittest

import test_dados
from dados import listar


class IndiceTest(unittest.TestCase):
    def setUp(self):
        self.dados = test_dados.DadosTest()
        self.addCleanup(self.dados.doCleanups)
        self.dados.setUp()
        self.painel = self.dados.carreira / "painel-vagas.md"
        self.dados.criar_processo("local-003", "2026-10-13")
        self.dados.criar_processo("local-004", "2026-10-14")

    def test_painel_incompleto_prioriza_links_sem_inferir_status(self):
        texto = (
            "# Painel geral de vagas\n"
            "[Apresentação](oportunidades/empresa-exemplo/local-003/processo.md)\n"
            "## Em andamento ou pausadas\n"
            "- [Primeira](<oportunidades/empresa-exemplo/local-001/processo.md>)\n"
            "- [Processo ausente](oportunidades/empresa-exemplo/local-999/processo.md)\n"
            "- [Segunda](./oportunidades/empresa-exemplo/local-002/processo.md#histórico)\n"
            "## Anúncios expirados ou processos encerrados\n"
            "- [Repetido](oportunidades/empresa-exemplo/local-001/processo.md)\n"
            "## Revisões recebidas — exemplo\n"
            "- [Menção](oportunidades/empresa-exemplo/local-003/processo.md)\n"
        )
        self.painel.write_text(texto, encoding="utf-8")
        vagas = listar(self.dados.carreira)
        self.assertEqual(
            [vaga["id"] for vaga in vagas],
            [f"empresa-exemplo/local-00{numero}" for numero in (1, 2, 4, 3)],
        )
        self.assertEqual([vaga["status"] for vaga in vagas[:2]], ["identificada", "reprovado"])
        self.assertEqual(self.painel.read_text(encoding="utf-8"), texto)

    def test_painel_ausente_mantem_ordem_por_atualizacao(self):
        self.painel.unlink()
        self.assertEqual(
            [vaga["id"] for vaga in listar(self.dados.carreira)],
            [f"empresa-exemplo/local-00{numero}" for numero in (4, 3, 2, 1)],
        )
        self.assertFalse(self.painel.exists())
