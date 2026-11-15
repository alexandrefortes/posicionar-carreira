from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import test_dados  # configura o acesso aos módulos de server/
from curriculos import resolver_curriculos


class CurriculosTest(unittest.TestCase):
    def setUp(self):
        temporario = TemporaryDirectory()
        self.addCleanup(temporario.cleanup)
        self.raiz = Path(temporario.name).resolve()
        self.dossie = self.raiz / "empresa-exemplo" / "local-001"
        self.dossie.mkdir(parents=True)
        self.processo = {
            "_path": self.dossie / "processo.md",
            "id": "empresa-exemplo/local-001",
            "empresa": "Empresa Exemplo",
            "titulo": "Engenheiro de Dados",
        }

    def criar(self, nome):
        caminho = self.dossie / nome
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(b"Arquivo ficticio.")
        return caminho

    def resolver(self, corpo=""):
        return resolver_curriculos(self.processo, corpo.encode("utf-8"))

    def test_formatos_ausentes_sao_independentes(self):
        self.assertEqual(self.resolver(), {})
        fonte = self.criar("curriculo.md")
        curriculos = self.resolver()
        self.assertEqual(set(curriculos), {"markdown"})
        self.assertEqual(curriculos["markdown"].caminho, fonte)
        fonte.unlink()
        pdf = self.criar("Candidato_Exemplo_CV_Empresa_Exemplo_Engenheiro_de_Dados.pdf")
        curriculos = self.resolver()
        self.assertEqual(set(curriculos), {"pdf"})
        self.assertEqual(curriculos["pdf"].caminho, pdf)

    def test_link_atual_supera_raiz_preparacoes_antigas_e_envios(self):
        self.criar("curriculo.md")
        self.criar("curriculo.pdf")
        self.criar("preparacao-2026-10-21/Candidato_CV_Empresa_Engenheiro.pdf")
        self.criar("envios/2026-10-22/curriculo-final.pdf")
        fonte = self.criar("preparacao-2026-10-31/curriculo.md")
        pdf = self.criar("preparacao-2026-10-31/Candidato CV Empresa.pdf")
        curriculos = self.resolver(
            "## Currículo atual\n"
            "[Currículo em PDF](<preparacao-2026-10-31/Candidato%20CV%20Empresa.pdf>)\n"
            "[Currículo anterior](curriculo.md)\n"
            "[PDF anterior](curriculo.pdf)\n"
        )
        self.assertEqual(curriculos["markdown"].caminho, fonte)
        self.assertEqual(curriculos["pdf"].caminho, pdf)
        self.assertFalse(curriculos["pdf"].enviado)

    def test_links_separados_preservam_a_versao_explicita_de_cada_tipo(self):
        self.criar("curriculo.md")
        pdf = self.criar("curriculo.pdf")
        revisao = self.criar("curriculo-revisao-2026-10-07.md")
        curriculos = self.resolver(
            "## Currículo atual\n"
            "[Currículo anterior](curriculo.md)\n"
            "[Currículo revisado em 07/10](curriculo-revisao-2026-10-07.md)\n"
            "[PDF regenerado em 07/10](curriculo.pdf)\n"
        )
        self.assertEqual(curriculos["markdown"].caminho, revisao)
        self.assertEqual(curriculos["pdf"].caminho, pdf)

    def test_ausencia_de_arquivo_explicitamente_atual_nao_promove_versao_antiga(self):
        self.criar("curriculo.md")
        self.criar("curriculo.pdf")
        pdf = self.criar("envios/2026-10-22/curriculo-final.pdf")
        curriculos = self.resolver(
            "## Currículo atual\n"
            "[Currículo editável](preparacao-2026-10-31/curriculo.md)\n"
            "[Currículo em PDF](preparacao-2026-10-31/curriculo.pdf)\n"
        )
        self.assertEqual(set(curriculos), {"pdf"})
        self.assertEqual(curriculos["pdf"].caminho, pdf)
        self.assertTrue(curriculos["pdf"].enviado)

    def test_falta_de_arquivo_vinculado_nao_impede_achar_o_formato_irmao(self):
        self.criar("curriculo.md")
        self.criar("curriculo.pdf")
        fonte = self.criar("preparacao-2026-10-31/curriculo.md")
        curriculos = self.resolver(
            "## Currículo atual\n[Currículo em PDF](preparacao-2026-10-31/curriculo.pdf)\n"
        )
        self.assertEqual(set(curriculos), {"markdown"})
        self.assertEqual(curriculos["markdown"].caminho, fonte)
        fonte.unlink()
        pdf = self.criar("preparacao-2026-10-31/curriculo.pdf")
        curriculos = self.resolver(
            "## Currículo atual\n[Currículo editável](preparacao-2026-10-31/curriculo.md)\n"
        )
        self.assertEqual(set(curriculos), {"pdf"})
        self.assertEqual(curriculos["pdf"].caminho, pdf)

    def test_pdf_enviado_aparece_so_se_for_a_unica_versao_identificada(self):
        self.criar("envios/2026-10-01/curriculo.md")
        enviado = self.criar("envios/2026-10-01/curriculo.pdf")
        self.assertEqual(set(self.resolver()), {"pdf"})
        self.assertEqual(self.resolver()["pdf"].caminho, enviado)
        self.assertTrue(self.resolver()["pdf"].enviado)
        self.criar("envios/2026-10-02/curriculo.pdf")
        self.assertEqual(self.resolver(), {})

    def test_nao_escolhe_entre_dois_pdfs_atuais_nem_usando_mtime(self):
        self.criar("Candidato_CV_Empresa_Exemplo_Engenheiro_de_Dados.pdf")
        self.criar("Outro_Candidato_CV_Empresa_Exemplo_Engenheiro_de_Dados.pdf")
        self.criar("envios/curriculo-final.pdf")
        self.assertEqual(self.resolver(), {})

    def test_rejeita_vinculos_externos_ou_de_outra_vaga(self):
        vizinho = self.dossie.parent / "local-002"
        vizinho.mkdir()
        (vizinho / "curriculo.md").touch()
        (vizinho / "curriculo.pdf").touch()
        curriculos = self.resolver(
            "## Currículo atual\n"
            "[Currículo editável](%2E%2E/local-002/curriculo.md)\n"
            f"[Currículo em PDF](<{(vizinho / 'curriculo.pdf').as_posix()}>)\n"
        )
        self.assertEqual(curriculos, {})

    def test_rejeita_symlink_para_outra_vaga(self):
        vizinho = self.dossie.parent / "local-002"
        vizinho.mkdir()
        arquivo = vizinho / "curriculo.md"
        arquivo.touch()
        try:
            (self.dossie / "curriculo.md").symlink_to(arquivo)
        except OSError:
            self.skipTest("A criação de links simbólicos não está disponível neste Windows.")
        self.assertEqual(self.resolver(), {})

    def test_nao_promove_variantes_historicas_nem_pdfs_de_outro_cargo(self):
        self.criar("curriculo-revisao-2026-10-31.md")
        self.criar("Candidato_CV_Empresa_Exemplo_Analista_Contabil.pdf")
        self.criar("Candidato_CV_Empresa_Exemplo_Engenheiro_de_Dados_anterior.pdf")
        self.criar("preparacao-2026-10-21/curriculo.pdf")
        self.assertEqual(self.resolver(), {})

    def test_link_atual_nao_promove_arquivos_de_entrevista_ou_arquivo(self):
        for pasta in ("entrevistas", "historico", "archive"):
            with self.subTest(pasta=pasta):
                self.criar(f"{pasta}/curriculo.md")
                self.criar(f"{pasta}/curriculo.pdf")
                self.assertEqual(self.resolver(
                    f"## Currículo atual\n[Currículo em PDF]({pasta}/curriculo.pdf)\n"
                ), {})

    def test_codigo_exemplo_no_processo_nao_conta_como_vinculo(self):
        self.criar("curriculo.md")
        self.criar("preparacao-2026-10-31/curriculo.md")
        curriculos = self.resolver(
            "```markdown\n"
            "## Currículo atual\n"
            "[Currículo editável](preparacao-2026-10-31/curriculo.md)\n"
            "```\n"
        )
        self.assertEqual(curriculos["markdown"].caminho, self.dossie / "curriculo.md")
