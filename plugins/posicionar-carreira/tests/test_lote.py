import json
import os
import subprocess
import sys
import unittest

import test_dados
from dados import detalhar
from lote import executar_lote


PRIMEIRO = "empresa-exemplo/local-001"
SEGUNDO = "empresa-exemplo/local-002"
FONTE = "https://example.org/retorno"


class LoteTest(unittest.TestCase):
    def setUp(self):
        dados = test_dados.DadosTest()
        self.addCleanup(dados.doCleanups)
        dados.setUp()
        self.raiz = dados.carreira
        self.painel = dados.carreira / "painel-vagas.md"
        self.primeiro = dados.primeiro / "processo.md"
        self.segundo = dados.carreira / "oportunidades" / SEGUNDO / "processo.md"

    def detalhe(self, processo_id):
        return detalhar(self.raiz, processo_id)

    def evento(self, processo_id, descricao):
        return {
            "ferramenta": "registrar_evento",
            "argumentos": {
                "processo_id": processo_id, "revisao": self.detalhe(processo_id)["revisao"],
                "descricao": descricao, "fonte": FONTE,
            },
        }

    def rodar_cli(self, entrada, *opcoes):
        caminho = self.raiz / "entrada.json"
        caminho.write_text(json.dumps(entrada), encoding="utf-8")
        return self.cli(str(caminho), *opcoes)

    def cli(self, *opcoes):
        cli = test_dados.PLUGIN / "server" / "lote.py"
        processo = subprocess.run(
            [sys.executable, "-B", str(cli), *opcoes],
            capture_output=True, encoding="utf-8", env={**os.environ, "CARREIRA_ROOT": str(self.raiz)},
            timeout=15,
        )
        self.assertTrue(processo.stdout, processo.stderr)
        return processo.returncode, json.loads(processo.stdout)

    def test_previa_padrao_e_aplicacao_parcial_preservam_indice(self):
        cadastro = {
            "ferramenta": "criar_vaga",
            "argumentos": {
                "empresa": "Outra empresa", "titulo": "Vaga sintética",
                "fonte": "https://example.org/cadastro", "processo_id": "outra-empresa/local-001",
            },
        }
        atualizacao = self.evento(PRIMEIRO, "Mudança de próxima ação")
        atualizacao["ferramenta"] = "atualizar_vaga"
        atualizacao["argumentos"]["mudancas"] = {"proxima_acao": "Preparar entrevista"}
        invalido = self.evento(SEGUNDO, "Tentativa com campo extra")
        invalido["argumentos"]["previa"] = False
        entradas = [cadastro, atualizacao, invalido]
        anteriores = [p.read_bytes() for p in (self.primeiro, self.segundo, self.painel)]
        novo = self.segundo.parents[2] / "outra-empresa/local-001/processo.md"

        codigo, previa = self.rodar_cli(entradas)
        self.assertEqual(codigo, 1)
        self.assertEqual([r["status"] for r in previa["resultados"]], ["previa", "previa", "erro"])
        self.assertEqual(previa["resultados"][1]["previa"]["mudancas"], {"proxima_acao": "Preparar entrevista"})
        self.assertEqual(previa["falhas"], [invalido])
        self.assertEqual([p.read_bytes() for p in (self.primeiro, self.segundo, self.painel)], anteriores)
        self.assertFalse(novo.exists())

        codigo, aplicado = self.rodar_cli(entradas, "--aplicar")
        self.assertEqual(codigo, 1)
        self.assertEqual([r["status"] for r in aplicado["resultados"]], ["aplicado", "aplicado", "erro"])
        self.assertEqual(aplicado["falhas"], [invalido])
        self.assertEqual(self.detalhe(PRIMEIRO)["proxima_acao"], "Preparar entrevista")
        self.assertTrue(novo.is_file())
        self.assertEqual(self.segundo.read_bytes(), anteriores[1])
        self.assertEqual(self.painel.read_bytes(), anteriores[2])

    def test_conflito_e_reexecucao_seletiva_conservam_revisao(self):
        valido = self.evento(PRIMEIRO, "Evento do primeiro dossiê")
        desatualizado = self.evento(SEGUNDO, "Evento a revisar")
        self.segundo.write_bytes(self.segundo.read_bytes() + b"\nNota feita depois da abertura\n")
        alterado = self.segundo.read_bytes()
        relatorio = executar_lote(self.raiz, [valido, desatualizado], aplicar=True)
        self.assertEqual([r["status"] for r in relatorio["resultados"]], ["aplicado", "conflito"])
        self.assertEqual(relatorio["falhas"], [desatualizado])
        primeiro_aplicado = self.primeiro.read_bytes()

        codigo, nova_tentativa = self.rodar_cli(relatorio, "--somente-falhas", "--aplicar")
        self.assertEqual(codigo, 1)
        self.assertEqual([r["status"] for r in nova_tentativa["resultados"]], ["conflito"])
        self.assertEqual(nova_tentativa["falhas"], [desatualizado])
        self.assertEqual(self.primeiro.read_bytes(), primeiro_aplicado)
        self.assertEqual(self.segundo.read_bytes(), alterado)

    def test_repeticao_no_lote_e_no_historico_nao_duplica_eventos(self):
        item = self.evento(PRIMEIRO, "Retorno anotado")
        for aplicar, esperado in ((False, "previa"), (True, "aplicado")):
            with self.subTest(aplicar=aplicar):
                relatorio = executar_lote(self.raiz, [item, item], aplicar=aplicar)
                self.assertEqual([r["status"] for r in relatorio["resultados"]], [esperado, "repetido"])
                self.assertEqual(relatorio["falhas"], [])

        corrente = self.evento(PRIMEIRO, "Retorno anotado")
        relatorio = executar_lote(self.raiz, [corrente], aplicar=True)
        self.assertEqual(relatorio["resultados"][0]["status"], "repetido")
        self.assertEqual(relatorio["falhas"], [])
        self.assertEqual(len(self.detalhe(PRIMEIRO)["eventos"]), 2)

    def test_duas_operacoes_distintas_no_mesmo_dossie_conflitam_na_previa(self):
        primeira = self.evento(PRIMEIRO, "Primeira nota")
        segunda = self.evento(PRIMEIRO, "Segunda nota")
        antes = self.primeiro.read_bytes()
        for aplicar, esperado in ((False, "previa"), (True, "aplicado")):
            with self.subTest(aplicar=aplicar):
                relatorio = executar_lote(self.raiz, [primeira, segunda], aplicar=aplicar)
                self.assertEqual([r["status"] for r in relatorio["resultados"]], [esperado, "conflito"])
                self.assertEqual(relatorio["falhas"], [segunda])
                if not aplicar:
                    self.assertEqual(self.primeiro.read_bytes(), antes)
        self.assertEqual(self.detalhe(PRIMEIRO)["eventos"][-1]["descricao"], "Primeira nota")

    def test_detalhar_cli_devolve_revisao_do_mesmo_carregador(self):
        codigo, detalhe = self.cli("--detalhar", PRIMEIRO)
        self.assertEqual(codigo, 0)
        self.assertEqual(detalhe, self.detalhe(PRIMEIRO))
