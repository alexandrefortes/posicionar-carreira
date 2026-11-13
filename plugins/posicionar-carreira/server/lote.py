"""Prévia e aplicação de um lote local de operações de carreira."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from dados import detalhar, resolver_raiz
from operacoes import CONFLITO, EVENTO_REPETIDO, OPERACOES, executar_operacao
from servidor import validar_argumentos


def executar_lote(raiz, itens, *, aplicar=False):
    if not isinstance(itens, list):
        raise ValueError("Informe uma lista de operações.")

    relatorio = {"modo": "aplicar" if aplicar else "previa", "resultados": [], "falhas": []}
    processadas = set()
    dossies = set()
    for indice, item in enumerate(itens, start=1):
        resultado = {"item": indice}
        try:
            if not isinstance(item, dict) or item.keys() != {"ferramenta", "argumentos"}:
                raise ValueError("Cada operação exige apenas ferramenta e argumentos.")
            ferramenta, argumentos = item["ferramenta"], item["argumentos"]
            resultado["ferramenta"] = ferramenta
            if isinstance(argumentos, dict) and isinstance(argumentos.get("processo_id"), str):
                resultado["id"] = argumentos["processo_id"]
            if not isinstance(ferramenta, str) or ferramenta not in OPERACOES:
                raise ValueError("Use criar_vaga, atualizar_vaga ou registrar_evento.")
            if isinstance(argumentos, dict) and "previa" in argumentos:
                raise ValueError("Use --aplicar para mudar o modo do lote.")
            validar_argumentos(ferramenta, argumentos)

            chave = json.dumps(item, sort_keys=True, ensure_ascii=False)
            if chave in processadas:
                resultado.update(status="repetido", mensagem="Operação já processada neste lote.")
            elif resultado.get("id") in dossies:
                resultado.update(
                    status="conflito",
                    mensagem="Outra operação já ocupa este dossiê no lote. Revise a operação separadamente.",
                )
                relatorio["falhas"].append(item)
            else:
                resposta = executar_operacao(raiz, ferramenta, argumentos, previa=not aplicar)
                processadas.add(chave)
                dossies.add(resposta["id"])
                resultado.update(id=resposta["id"], status="aplicado" if aplicar else "previa")
                if aplicar:
                    resultado["revisao"] = resposta["revisao"]
                else:
                    resultado["previa"] = resposta
        except (ValueError, OSError, yaml.YAMLError) as exc:
            mensagem = str(exc)
            if mensagem == EVENTO_REPETIDO:
                status = "repetido"
            elif mensagem == CONFLITO:
                status = "conflito"
            else:
                status = "erro"
            resultado.update(status=status, mensagem=mensagem)
            if status != "repetido":
                relatorio["falhas"].append(item)
        relatorio["resultados"].append(resultado)
    return relatorio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entrada", nargs="?", type=Path, help="Lista JSON de operações ou relatório anterior.")
    parser.add_argument("--aplicar", action="store_true", help="Grava as operações válidas.")
    parser.add_argument("--somente-falhas", action="store_true", help="Usa a lista falhas do relatório informado.")
    parser.add_argument("--detalhar", metavar="ID", help="Consulta o dossiê e a sua revisão atual.")
    args = parser.parse_args()
    if args.detalhar is not None:
        if args.entrada or args.aplicar or args.somente_falhas:
            parser.error("--detalhar deve ser usado sozinho.")
    elif args.entrada is None:
        parser.error("Informe a entrada JSON ou --detalhar ID.")

    try:
        raiz = resolver_raiz()
        if args.detalhar is not None:
            relatorio = detalhar(raiz, args.detalhar)
        else:
            entrada = json.loads(args.entrada.read_text(encoding="utf-8-sig"))
            if args.somente_falhas:
                if not isinstance(entrada, dict) or "falhas" not in entrada:
                    raise ValueError("Informe um relatório de lote com a lista falhas.")
                entrada = entrada["falhas"]
            relatorio = executar_lote(raiz, entrada, aplicar=args.aplicar)
    except (ValueError, OSError, yaml.YAMLError) as exc:
        parser.error(str(exc))
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    return int(bool(relatorio.get("falhas")))


if __name__ == "__main__":
    raise SystemExit(main())
