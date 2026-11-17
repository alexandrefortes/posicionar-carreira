"""Cria a pasta local de dados e, quando solicitado, uma base fictícia."""

import argparse
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


EXEMPLO = Path(__file__).resolve().parent
BASE = EXEMPLO / "base"
MODELO = EXEMPLO / "modelo"
SERVIDOR = EXEMPLO.parent / "plugins/posicionar-carreira/server"
sys.path.insert(0, str(SERVIDOR))

from dados import caminho_carreira_configurado


def inicializar(carreira: Path, *, com_exemplo: bool = False) -> Path:
    carreira = carreira.expanduser().resolve()
    if carreira.is_relative_to(EXEMPLO.parent):
        raise ValueError("Escolha uma pasta de dados fora do repositório do plugin.")
    oportunidades = carreira / "oportunidades"
    if oportunidades.resolve() != oportunidades:
        raise ValueError("Escolha uma pasta de dados sem atalhos em oportunidades/.")
    if not com_exemplo:
        oportunidades.mkdir(parents=True, exist_ok=True)
        return carreira

    if (carreira.exists() and any(item != oportunidades for item in carreira.iterdir())
            or oportunidades.exists() and any(oportunidades.iterdir())):
        raise ValueError("O exemplo só pode ser criado em uma base vazia.")

    carreira.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=carreira.parent, prefix=".exemplo-") as temporario:
        base = Path(temporario) / "carreira"
        shutil.copytree(BASE, base)
        shutil.copytree(MODELO, base / "oportunidades/conselho-de-rotas-de-hyrule/local-001")
        if oportunidades.exists():
            oportunidades.rmdir()
        if carreira.exists():
            carreira.rmdir()
        base.rename(carreira)
    return carreira


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    caminhos = parser.add_mutually_exclusive_group()
    caminhos.add_argument("--carreira-root", type=Path, help="Pasta de dados que conterá oportunidades/.")
    caminhos.add_argument("--raiz", type=Path, help="Pasta legada que conterá carreira/oportunidades.")
    parser.add_argument("--com-exemplo", action="store_true", help="Cria um perfil e um dossiê fictícios em uma base vazia.")
    args = parser.parse_args()
    try:
        carreira = args.carreira_root or (args.raiz / "carreira" if args.raiz else caminho_carreira_configurado())
        criada = inicializar(carreira, com_exemplo=args.com_exemplo)
        print(criada.parent if args.raiz else criada)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
