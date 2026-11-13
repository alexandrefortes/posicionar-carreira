"""Cria a pasta local de dados e, quando solicitado, uma base fictícia."""

import argparse
import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory


EXEMPLO = Path(__file__).resolve().parent
BASE = EXEMPLO / "base"
MODELO = EXEMPLO / "modelo"


def raiz_padrao() -> Path:
    configurado = os.environ.get("POSICIONAR_CARREIRA_ROOT")
    if not configurado:
        seletor = Path.home() / ".posicionar-carreira-raiz"
        if seletor.is_file():
            configurado = seletor.read_text(encoding="utf-8-sig").strip()
    return Path(configurado) if configurado else Path.home() / "PosicionarCarreira"


def inicializar(raiz: Path, *, com_exemplo: bool = False) -> Path:
    raiz = raiz.expanduser().resolve()
    if raiz.is_relative_to(EXEMPLO.parent):
        raise ValueError("Escolha uma pasta de dados fora do repositório do plugin.")
    carreira = raiz / "carreira"
    oportunidades = carreira / "oportunidades"
    if oportunidades.resolve() != oportunidades:
        raise ValueError("Escolha uma pasta de dados sem atalhos em carreira/oportunidades.")
    if not com_exemplo:
        oportunidades.mkdir(parents=True, exist_ok=True)
        return raiz

    if (carreira.exists() and any(item != oportunidades for item in carreira.iterdir())
            or oportunidades.exists() and any(oportunidades.iterdir())):
        raise ValueError("O exemplo só pode ser criado em uma base vazia.")

    raiz.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=raiz, prefix=".exemplo-") as temporario:
        base = Path(temporario) / "carreira"
        shutil.copytree(BASE, base)
        shutil.copytree(MODELO, base / "oportunidades/laboratorio-exemplo/local-001")
        if oportunidades.exists():
            oportunidades.rmdir()
        if carreira.exists():
            carreira.rmdir()
        base.rename(carreira)
    return raiz


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", type=Path, help="Pasta que conterá carreira/oportunidades.")
    parser.add_argument("--com-exemplo", action="store_true", help="Cria um perfil e um dossiê fictícios em uma base vazia.")
    args = parser.parse_args()
    try:
        print(inicializar(args.raiz or raiz_padrao(), com_exemplo=args.com_exemplo))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
