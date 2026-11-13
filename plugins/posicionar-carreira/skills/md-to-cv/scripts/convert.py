#!/usr/bin/env python3
"""Converte um curriculo em Markdown para PDF amigavel a ATS via pandoc + pdflatex.

Uso (entrada relativa ao diretório atual ou absoluta):
    python "<diretorio absoluto da skill>/scripts/convert.py" caminho/para/curriculo.md --output Nome_CV_Empresa_Cargo.pdf

Saida:
    PDF no diretorio do Markdown. Sem --output, usa o nome do Markdown.

O PDF sai em coluna unica, texto selecionavel, alinhado a esquerda, com
metadados (nome e palavras-chave da vaga) lidos do frontmatter YAML do .md.
Avisa se passar de MAX_PAGES paginas e roda uma checagem de extracao de texto
(teste rapido de ATS).

Requisitos:
    - pandoc >= 3.0
    - pdflatex (TeX Live ou MiKTeX)
    - pip install pypdf
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

MAX_PAGES = 2            # CV: mire em 1-2 paginas
MIN_EXTRACT_CHARS = 200  # abaixo disso, a extracao pode ter falhado

SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL_DIR / "scripts" / "template.tex"


def find_tool(name: str, search_globs: tuple = ()) -> str:
    """Acha o executavel no PATH ou nos locais conhecidos de instalacao (Windows)."""
    found = shutil.which(name)
    if found:
        return found
    for pattern in search_globs:
        matches = sorted(glob.glob(os.path.expandvars(pattern)))
        if matches:
            return matches[-1]
    print(
        f"[ERRO] nao encontrei '{name}'. Instale-o ou adicione ao PATH.\n"
        f"       Locais procurados: {', '.join(search_globs) or 'apenas o PATH'}"
    )
    sys.exit(1)


def require_pypdf() -> None:
    import importlib.util
    if importlib.util.find_spec("pypdf") is None:
        print(
            "[ERRO] dependencia 'pypdf' nao instalada. Execute:\n"
            f'       python -m pip install -r "{SKILL_DIR / "requirements.txt"}"'
        )
        sys.exit(1)


def run(cmd: list[str], label: str) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"\n[ERRO] {label} falhou com codigo {result.returncode}:")
        print(result.stderr or result.stdout)
        sys.exit(1)
    return result


def count_pages(pdf_path: Path) -> int:
    from pypdf import PdfReader
    return len(PdfReader(str(pdf_path)).pages)


def extract_text(pdf_path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(pdf_path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def ats_check(pdf_path: Path) -> None:
    """Teste de ATS: confirma que o texto e selecionavel e mostra o topo."""
    text = extract_text(pdf_path)
    chars = len(text.strip())
    print("\n--- Teste ATS (extracao de texto) ---")
    print(f"Caracteres extraidos: {chars}")
    if chars < MIN_EXTRACT_CHARS:
        print("[AVISO] Pouco texto extraido. O PDF pode nao estar selecionavel.")
        print("        Confira se o conteudo nao virou imagem.")
    preview = [ln.strip() for ln in text.splitlines() if ln.strip()][:5]
    if preview:
        print("Primeiras linhas extraidas (confira nome e contato):")
        for ln in preview:
            print(f"  | {ln}")
    print("-------------------------------------")


def convert(md_path: Path, output_name: str | None = None) -> Path:
    if output_name is not None:
        output = Path(output_name)
        if (
            output.name != output_name
            or output.suffix.lower() != ".pdf"
            or any(char in output_name for char in '<>:"/\\|?*')
            or output.stem.casefold() in {"curriculo", "currículo", "cv", "resume", "résumé", "curriculum", "curriculum_vitae"}
        ):
            print("[ERRO] --output exige um nome de PDF descritivo, sem diretorios nem nomes genericos como curriculo.pdf.")
            sys.exit(1)
    md_path = md_path.resolve()
    if not md_path.exists():
        print(f"[ERRO] Arquivo nao encontrado: {md_path}")
        sys.exit(1)
    if not TEMPLATE.exists():
        print(f"[ERRO] Template nao encontrado: {TEMPLATE.resolve()}")
        sys.exit(1)
    require_pypdf()

    out_pdf = md_path.with_name(output_name) if output_name is not None else md_path.with_suffix(".pdf")
    print(f"Convertendo: {md_path.name} -> {out_pdf.name}")

    pandoc = find_tool("pandoc", (
        r"%LOCALAPPDATA%\Pandoc\pandoc.exe",
        r"C:\Program Files\Pandoc\pandoc.exe",
        r"C:\Program Files\RStudio\resources\app\bin\quarto\bin\tools\pandoc.exe",
    ))
    pdflatex = find_tool("pdflatex", (
        r"%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe",
        r"C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe",
        r"%APPDATA%\TinyTeX\bin\windows\pdflatex.exe",
        r"C:\texlive\*\bin\win*\pdflatex.exe",
    ))

    run([
        pandoc,
        str(md_path),
        # respeita as quebras de linha do .md (cabecalho, contato) sem depender
        # de espacos no fim da linha, que editores costumam apagar ao salvar
        "--from", "markdown+hard_line_breaks",
        "--template", str(TEMPLATE),
        "--pdf-engine", pdflatex,
        "--output", str(out_pdf),
        "--standalone",
    ], "pandoc")

    pages = count_pages(out_pdf)
    status = "OK" if pages <= MAX_PAGES else "AVISO"
    print(f"[{status}] Paginas: {pages}/{MAX_PAGES}")
    if pages > MAX_PAGES:
        print("[AVISO] Revise a relevancia e a legibilidade do conteudo para a vaga.")

    ats_check(out_pdf)

    print(f"\n[OK] PDF salvo: {out_pdf.resolve()}")
    return out_pdf


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path, help="Curriculo Markdown, relativo ao diretorio atual ou absoluto")
    parser.add_argument("--output", metavar="NOME.pdf", help="Nome descritivo do PDF na pasta do Markdown")
    args = parser.parse_args()
    convert(args.markdown, args.output)
