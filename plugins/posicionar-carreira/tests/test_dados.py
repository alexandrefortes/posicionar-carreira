import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import yaml

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "server"))
from dados import caminho_carreira_configurado, detalhar, listar, resolver_carreira_root


class DadosTest(unittest.TestCase):
    def setUp(self):
        diretorio = TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)
        self.workspace = Path(diretorio.name).resolve()
        self.carreira = self.workspace / "dados-exemplo"
        self.carreira.mkdir()
        (self.carreira / "config.json").write_text(json.dumps({"responsavel": "Pessoa Exemplo"}), encoding="utf-8")
        (self.carreira / "painel-vagas.md").write_text("Painel desatualizado", encoding="utf-8")
        self.primeiro = self.criar_processo("local-001", "2026-10-10")
        self.criar_processo(
            "local-002", "2026-10-12",
            estado="encerrado", etapa="entrevista_tecnica", resultado="reprovado",
        )

    def criar_processo(self, identificador, atualizado, **campos):
        processo_id = f"empresa-exemplo/{identificador}"
        dossie = self.carreira / "oportunidades" / processo_id
        dossie.mkdir(parents=True)
        fonte = "https://example.org/oportunidade"
        processo = {
            "id": processo_id, "empresa": "Empresa Exemplo", "titulo": "Vaga de exemplo",
            "estado": "aberto", "etapa": "triagem", "resultado": None,
            "prioridade": "media", "responsavel": "empresa", "proxima_acao": "Aguardar retorno",
            "fonte_estado": fonte, "candidatura_confirmada": False, "atualizado_em": atualizado,
            "eventos": [
                {"data": None, "registrado_em": atualizado, "descricao": "Retorno registrado", "fonte": fonte}
            ],
        }
        processo.update(campos)
        (dossie / "processo.md").write_text(
            "---\n" + yaml.safe_dump(processo, allow_unicode=True) + "---\n# Processo\n",
            encoding="utf-8",
        )
        return dossie

    def test_lista_usa_processos_com_mesma_empresa_e_titulo(self):
        segundo, primeiro = listar(self.carreira)
        self.assertEqual(segundo["id"], "empresa-exemplo/local-002")
        self.assertEqual(segundo["estado"], "encerrado")
        self.assertEqual(segundo["etapa"], "entrevista_tecnica")
        self.assertEqual(segundo["resultado"], "reprovado")
        self.assertEqual(primeiro["id"], "empresa-exemplo/local-001")
        self.assertEqual(primeiro["estado"], "aberto")
        self.assertIsNone(primeiro["resultado"])
        self.assertNotIn("processo", primeiro)

    def test_detalhe_preserva_historico_e_identifica_versoes_por_pasta(self):
        for arquivo in ("cv.pdf", "entrevistas/perguntas.md", "envios/2026-10-01/cv.pdf"):
            destino = self.primeiro / arquivo
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text("Arquivo sintético", encoding="utf-8")
        resultado = detalhar(self.carreira, "empresa-exemplo/local-001")
        self.assertEqual(resultado["processo"], str(self.primeiro / "processo.md"))
        self.assertEqual(resultado["proxima_acao"], "Aguardar retorno")
        self.assertIsNone(resultado["eventos"][0]["data"])
        self.assertEqual(resultado["eventos"][0]["descricao"], "Retorno registrado")
        self.assertEqual(resultado["materiais"], [
            {"caminho": "cv.pdf", "tipo": "material"},
            {"caminho": "entrevistas/perguntas.md", "tipo": "entrevista"},
            {"caminho": "envios/2026-10-01/cv.pdf", "tipo": "envio"},
        ])

    def test_titulo_chat_usa_empresa_e_status_confirmados(self):
        casos = (
            ("aberto", "identificada", None, "identificada"),
            ("aberto", "candidatura_enviada", None, "enviada"),
            ("aberto", "entrevista_tecnica", None, "entrevista técnica"),
            ("pausado", "entrevista_tecnica", None, "pausado"),
            ("encerrado", "entrevista_tecnica", "desistencia", "desistência"),
        )
        for numero, (estado, etapa, resultado, status) in enumerate(casos, start=3):
            with self.subTest(estado=estado, etapa=etapa):
                identificador = f"local-{numero:03}"
                self.criar_processo(
                    identificador, "2026-10-12",
                    empresa="  Empresa. Café–Norte - Exemplo  ",
                    estado=estado, etapa=etapa, resultado=resultado,
                )
                detalhe = detalhar(self.carreira, f"empresa-exemplo/{identificador}")
                self.assertEqual(detalhe["titulo_chat"], f"candidatura empresa café norte exemplo - {status}")

    def test_rejeita_id_inexistente_ou_caminho_arbitrario(self):
        for identificador in ("empresa-exemplo/local-999", "../carreira/AGENTS.md", str(self.primeiro)):
            with self.subTest(identificador=identificador):
                with self.assertRaisesRegex(ValueError, "Processo não encontrado"):
                    detalhar(self.carreira, identificador)

    def test_detalhe_le_apenas_o_processo_selecionado(self):
        outro = self.carreira / "oportunidades/empresa-exemplo/local-002/processo.md"
        outro.write_text("Processo sem metadados", encoding="utf-8")
        detalhe = detalhar(self.carreira, "empresa-exemplo/local-001")
        self.assertEqual(detalhe["processo"], str(self.primeiro / "processo.md"))
        with self.assertRaisesRegex(ValueError, "metadados YAML ausentes"):
            listar(self.carreira)

    def test_resolucao_explicitamente_configurada(self):
        with patch.dict(os.environ, {"CARREIRA_ROOT": str(self.carreira)}, clear=True):
            self.assertEqual(resolver_carreira_root(), self.carreira)
        with patch.dict(os.environ, {"CARREIRA_ROOT": str(self.carreira / "invalido")}, clear=True):
            self.assertEqual(resolver_carreira_root(self.carreira), self.carreira)
            with self.assertRaisesRegex(FileNotFoundError, "CARREIRA_ROOT"):
                resolver_carreira_root()

    def test_resolucao_persistente_e_alias_de_workspaces_anteriores(self):
        arquivo = self.workspace / ".config/posicionar-carreira/data-root.txt"
        arquivo.parent.mkdir(parents=True)
        arquivo.write_text(str(self.carreira) + "\n", encoding="utf-8")
        with patch.dict(os.environ, {}, clear=True), patch("dados.Path.home", return_value=self.workspace):
            self.assertEqual(resolver_carreira_root(), self.carreira)
        legado = self.workspace / "carreira"
        (legado / "oportunidades").mkdir(parents=True)
        with patch.dict(os.environ, {"PAPAO_ROOT": str(self.workspace)}, clear=True):
            self.assertEqual(resolver_carreira_root(), legado)

    def test_configuracoes_publicas_anteriores_e_precedencia(self):
        legado = self.workspace / "base-pública" / "carreira"
        (legado / "oportunidades").mkdir(parents=True)
        with patch("dados.Path.home", return_value=self.workspace), patch.dict(os.environ, {}, clear=True):
            padrao = self.workspace / "PosicionarCarreira" / "carreira"
            self.assertEqual(caminho_carreira_configurado(), padrao)
            with self.assertRaises(FileNotFoundError):
                resolver_carreira_root()
            (padrao / "oportunidades").mkdir(parents=True)
            self.assertEqual(resolver_carreira_root(), padrao)

            seletor_antigo = self.workspace / ".posicionar-carreira-raiz"
            seletor_antigo.write_text(str(legado.parent) + "\n", encoding="utf-8-sig")
            self.assertEqual(resolver_carreira_root(), legado)

            seletor_atual = self.workspace / ".config/posicionar-carreira/data-root.txt"
            seletor_atual.parent.mkdir(parents=True)
            seletor_atual.write_text(str(self.carreira), encoding="utf-8")
            self.assertEqual(resolver_carreira_root(), self.carreira)

            os.environ["PAPAO_ROOT"] = str(self.workspace / "ausente")
            os.environ["POSICIONAR_CARREIRA_ROOT"] = str(legado.parent)
            self.assertEqual(resolver_carreira_root(), legado)
            os.environ["CARREIRA_ROOT"] = str(self.carreira)
            self.assertEqual(resolver_carreira_root(), self.carreira)

            os.environ["CARREIRA_ROOT"] = "relativo"
            with self.assertRaisesRegex(FileNotFoundError, "caminho absoluto"):
                resolver_carreira_root()

    def test_detalhe_preserva_responsavel_da_versao_publica_anterior(self):
        dossie = self.criar_processo("local-003", "2026-10-12", responsavel="candidato")
        original = (dossie / "processo.md").read_bytes()
        detalhe = detalhar(self.carreira, "empresa-exemplo/local-003")
        self.assertEqual(detalhe["responsavel"], "candidato")
        self.assertEqual((dossie / "processo.md").read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
