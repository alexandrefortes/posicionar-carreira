import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import call, patch


PACOTE = Path(__file__).resolve().parents[1]
EXEMPLO = PACOTE / "exemplo"
SERVIDOR = PACOTE / "plugins" / "posicionar-carreira" / "server"
sys.path[:0] = [str(EXEMPLO), str(SERVIDOR)]

from inicializar import inicializar, raiz_padrao
from servidor import respond


ID_EXEMPLO = "laboratorio-exemplo/local-001"
PDF_EXEMPLO = "Marina_Exemplo_CV_Laboratorio_Exemplo_Analista_Dados.pdf"


class ExemploTest(unittest.TestCase):
    def setUp(self):
        temporario = TemporaryDirectory()
        self.addCleanup(temporario.cleanup)
        self.raiz = Path(temporario.name).resolve()
        self.dossie = self.raiz / "carreira" / "oportunidades" / ID_EXEMPLO
        ambiente = patch.dict(os.environ, {"POSICIONAR_CARREIRA_ROOT": str(self.raiz)})
        ambiente.start()
        self.addCleanup(ambiente.stop)

    def chamar(self, ferramenta, **argumentos):
        resposta = respond(json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": ferramenta, "arguments": argumentos},
        }))
        self.assertNotIn("error", resposta)
        return resposta["result"]

    def test_base_vazia_e_recusa_de_sobrescrita(self):
        inicializar(self.raiz)
        self.assertEqual(self.chamar("listar_vagas")["structuredContent"]["vagas"], [])
        inicializar(self.raiz, com_exemplo=True)
        carreira = self.raiz / "carreira"
        for relativo in (
            "perfil/perfil-profissional.md",
            "perfil/evidencias/painel-indicadores-operacionais.md",
            "estrategia/objetivos.md",
            "curriculos/base.md",
            "portfolio/painel-indicadores-operacionais.md",
        ):
            self.assertTrue((carreira / relativo).is_file(), relativo)
        curriculo = self.dossie / "curriculo.md"
        curriculo.write_text("Alteração local de teste.", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "base vazia"):
            inicializar(self.raiz, com_exemplo=True)
        self.assertEqual(curriculo.read_text(encoding="utf-8"), "Alteração local de teste.")

    def test_exemplo_nao_mistura_perfil_existente_com_dados_ficticios(self):
        inicializar(self.raiz)
        perfil = self.raiz / "carreira/perfil/perfil-profissional.md"
        perfil.parent.mkdir()
        perfil.write_text("Perfil existente.", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "base vazia"):
            inicializar(self.raiz, com_exemplo=True)
        self.assertEqual(perfil.read_text(encoding="utf-8"), "Perfil existente.")
        self.assertFalse(self.dossie.exists())

    def test_precedencia_da_raiz_e_recusa_de_dados_no_pacote(self):
        com_variavel = self.raiz / "base-var"
        com_seletor = self.raiz / "base-seletor"
        seletor = self.raiz / ".posicionar-carreira-raiz"
        with patch("pathlib.Path.home", return_value=self.raiz), patch.dict(
            os.environ, {"POSICIONAR_CARREIRA_ROOT": ""}, clear=False
        ):
            self.assertEqual(raiz_padrao(), self.raiz / "PosicionarCarreira")
            seletor.write_text(str(com_seletor) + "\n", encoding="utf-8-sig")
            self.assertEqual(raiz_padrao(), com_seletor)
            os.environ["POSICIONAR_CARREIRA_ROOT"] = str(com_variavel)
            self.assertEqual(raiz_padrao(), com_variavel)
        with self.assertRaisesRegex(ValueError, "fora do repositório"):
            inicializar(PACOTE / "dados-teste")

    def test_mcp_lista_detalha_atualiza_e_abre_arquivos_do_exemplo(self):
        inicializar(self.raiz, com_exemplo=True)
        lista = self.chamar("listar_vagas")["structuredContent"]["vagas"]
        self.assertEqual([vaga["id"] for vaga in lista], [ID_EXEMPLO])
        detalhe = self.chamar("detalhar_vaga", processo_id=ID_EXEMPLO)["structuredContent"]
        self.assertEqual(set(detalhe["curriculos"]), {"markdown", "pdf"})
        self.assertEqual(detalhe["responsavel"], "candidato")
        self.assertTrue((self.dossie / PDF_EXEMPLO).read_bytes().startswith(b"%PDF-"))
        for nome in ("avaliacao.md", "benchmark-salarial.md", "carta.md"):
            self.assertIn({"caminho": nome, "tipo": "material"}, detalhe["materiais"])

        atualizado = self.chamar(
            "atualizar_vaga", processo_id=ID_EXEMPLO, revisao=detalhe["revisao"],
            descricao="Currículo fictício revisado.",
            fonte=f"oportunidades/{ID_EXEMPLO}/curriculo.md",
            mudancas={"proxima_acao": "Simular entrevista"},
        )["structuredContent"]
        self.assertNotEqual(atualizado["revisao"], detalhe["revisao"])
        self.assertEqual(atualizado["proxima_acao"], "Simular entrevista")
        self.assertEqual(atualizado["eventos"][-1]["descricao"], "Currículo fictício revisado.")
        self.assertIn("## Currículo atual", (self.dossie / "processo.md").read_text(encoding="utf-8"))

        with patch("os.startfile", create=True) as abrir:
            for tipo, nome in (("markdown", "curriculo.md"), ("pdf", PDF_EXEMPLO)):
                resposta = self.chamar("abrir_curriculo", processo_id=ID_EXEMPLO, tipo=tipo, enviado=False)
                self.assertEqual(resposta["structuredContent"]["nome"], nome)
            resposta = self.chamar("abrir_curriculo", processo_id="../local-001", tipo="pdf", enviado=False)
            self.assertTrue(resposta["isError"])
            self.assertEqual(abrir.call_args_list, [
                call(str(self.dossie / "curriculo.md")), call(str(self.dossie / PDF_EXEMPLO)),
            ])

    def test_servidor_responde_por_stdio(self):
        inicializar(self.raiz)
        resultado = subprocess.run(
            [sys.executable, "-B", str(SERVIDOR / "servidor.py")],
            input=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}) + "\n",
            encoding="utf-8", capture_output=True, check=True,
        )
        ferramentas = json.loads(resultado.stdout)["result"]["tools"]
        self.assertTrue({"abrir_painel", "registrar_evento", "abrir_curriculo"}
                        <= {ferramenta["name"] for ferramenta in ferramentas})


if __name__ == "__main__":
    unittest.main()
