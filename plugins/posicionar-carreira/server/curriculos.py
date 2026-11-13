"""Identifica os currículos da vaga sem usar caminhos vindos do painel."""
from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import unquote


FORMATOS = {"markdown": ".md", "pdf": ".pdf"}
LINK = re.compile(r"\[([^\]]+)\]\((<[^>]+>|[^)]+)\)")
TITULO = re.compile(r"^#{1,6}\s+(.*)$")
ATUAIS = ("curriculo atual", "curriculo de trabalho", "curriculo vigente")
IDENTIFICADORES = {"curriculo", "cv", "resume"}
PASTAS_EXCLUIDAS = {"archive", "arquivo", "backup", "entrevista", "entrevistas", "historico", "historicos"}
HISTORICO = {
    "anterior", "antigo", "archive", "arquivo", "backup", "copia", "enviado", "enviada",
    "historico", "historica", "old", "original", "preservado", "preservada", "previous",
    "rascunho", "draft",
}
PALAVRAS_COMUNS = {"a", "and", "da", "das", "de", "do", "dos", "e", "em", "for", "i", "ii", "in", "of", "the"}


@dataclass(frozen=True)
class Curriculo:
    caminho: Path
    enviado: bool = False


def _palavras(texto: str) -> list[str]:
    ascii_texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.findall(r"[a-z0-9]+", ascii_texto.lower())


def _historico(texto: str) -> bool:
    return bool(HISTORICO.intersection(_palavras(texto)))


def _caminho(dossie: Path, destino: str) -> Path | None:
    destino = unquote(destino.strip().strip("<>").split("#", 1)[0])
    partes = PurePosixPath(destino).parts
    if not partes or destino.startswith("/") or ".." in partes:
        return None
    if any(c in destino for c in ('\\', ':', '\0')):
        return None
    return dossie.joinpath(*partes)


def _arquivo(dossie: Path, caminho: Path | None, enviado: bool = False) -> Path | None:
    if caminho is None or not caminho.is_relative_to(dossie):
        return None
    partes = caminho.relative_to(dossie).parts
    if not partes or (partes[0].casefold() == "envios") != enviado:
        return None
    if any(" ".join(_palavras(parte)) in PASTAS_EXCLUIDAS for parte in partes[:-1]):
        return None
    if not enviado and any(_historico(parte) for parte in partes):
        return None
    try:
        real = caminho.resolve(strict=True)
        if real == caminho and real.is_relative_to(dossie) and real.is_file():
            return real
    except (OSError, RuntimeError, ValueError):
        pass
    return None


def _referencias(dossie: Path, conteudo: bytes):
    referencias = defaultdict(set)
    historicos = set()
    secao = ""
    cerca = ""
    texto = conteudo.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    corpo = texto.split("\n---\n", 1)[-1]
    for linha in corpo.splitlines():
        limpa = linha.lstrip()
        if limpa.startswith(("```", "~~~")):
            if not cerca:
                cerca = limpa[:3]
            elif limpa.startswith(cerca):
                cerca = ""
            continue
        if cerca:
            continue
        titulo = TITULO.match(linha)
        if titulo:
            secao = " ".join(_palavras(titulo[1])) if linha.startswith("##") else ""
        for rotulo, destino in LINK.findall(linha):
            nome = " ".join(_palavras(rotulo))
            caminho = _caminho(dossie, destino)
            extensao = PurePosixPath(unquote(destino.strip("<>").split("#", 1)[0])).suffix.lower()
            if extensao not in FORMATOS.values():
                continue
            identifica = bool(IDENTIFICADORES.intersection(nome.split()))
            atual = secao.startswith(ATUAIS)
            if _historico(nome) or _historico(secao):
                if caminho is not None:
                    historicos.add(caminho)
                continue
            if atual and (identifica or extensao == ".pdf" and nome.startswith("pdf ")):
                prioridade = 0
            elif identifica and (
                nome.startswith(ATUAIS) or "editavel" in nome.split()
                or secao in ("materiais", "materiais para revisao", "evidencias e materiais", "")
            ):
                prioridade = 1
            else:
                continue
            referencias[extensao, prioridade].add(caminho)
    return referencias, historicos


def _identifica_pdf(path: Path, processo: dict, enviado: bool = False) -> bool:
    nome = _palavras(path.stem)
    if not nome or not IDENTIFICADORES.intersection(nome):
        return False
    if enviado:
        return True
    if _historico(path.stem) or (nome[-1] in {"final", "revisado"} and len(nome) <= 2):
        return False
    if nome in (["curriculo"], ["cv"], ["resume"]):
        return True
    empresa = _palavras(processo["empresa"])
    slug = _palavras(processo["id"].split("/")[0])
    cargo = set(_palavras(processo["titulo"])) - PALAVRAS_COMUNS
    indice = next(i for i, palavra in enumerate(nome) if palavra in IDENTIFICADORES)
    alvo = nome[indice + 1:]
    return indice > 0 and (
        alvo in (empresa, slug)
        or bool(set(alvo).intersection(set(empresa + slug) - PALAVRAS_COMUNS))
        and bool(set(alvo).intersection(cargo))
    )


def _unico(candidatos) -> Path | None:
    unicos = set(candidatos)
    return next(iter(unicos)) if len(unicos) == 1 else None


def resolver_curriculos(processo: dict, conteudo: bytes) -> dict[str, Curriculo]:
    """Retorna cada formato em separado, apenas se a versão for inequívoca."""
    dossie = processo["_path"].parent.resolve()
    referencias, historicos = _referencias(dossie, conteudo)
    escolhidos = {}
    citados = {}
    pdf_atual_ambiguo = False
    for formato, extensao in FORMATOS.items():
        for prioridade in (0, 1):
            links = referencias.get((extensao, prioridade))
            if links:
                if formato == "pdf":
                    pdf_atual_ambiguo = len(links) > 1
                caminho = _unico(links)
                if caminho in historicos or (caminho and _historico(caminho.stem)):
                    caminho = None
                citados[formato] = caminho
                if validado := _arquivo(dossie, caminho):
                    escolhidos[formato] = Curriculo(validado)
                break

    if "markdown" not in citados:
        pdf = citados.get("pdf")
        if pdf:
            nomes = (pdf.with_suffix(".md"), pdf.with_name("curriculo.md"))
        else:
            nomes = () if "pdf" in citados else (dossie / "curriculo.md",)
        for caminho in nomes:
            if caminho not in historicos and (validado := _arquivo(dossie, caminho)):
                escolhidos["markdown"] = Curriculo(validado)
                break

    if "pdf" not in citados:
        markdown = escolhidos.get("markdown")
        fonte = markdown.caminho if markdown else citados.get("markdown")
        pasta = fonte.parent if fonte else dossie if "markdown" not in citados else None
        caminho = fonte.with_suffix(".pdf") if fonte else None
        validado = None
        if caminho not in historicos:
            validado = _arquivo(dossie, caminho)
        if not validado and pasta is not None and pasta.is_dir():
            candidatos = {
                arquivo for path in pasta.iterdir()
                if path.suffix.lower() == ".pdf" and path not in historicos
                and _identifica_pdf(path, processo) and (arquivo := _arquivo(dossie, path))
            }
            pdf_atual_ambiguo = len(candidatos) > 1
            validado = _unico(candidatos)
        if validado:
            escolhidos["pdf"] = Curriculo(validado)

    if "pdf" not in escolhidos and not pdf_atual_ambiguo:
        enviado = _unico(
            arquivo for path in (dossie / "envios").rglob("*")
            if path.suffix.lower() == ".pdf" and _identifica_pdf(path, processo, enviado=True)
            and (arquivo := _arquivo(dossie, path, enviado=True))
        )
        if enviado:
            escolhidos["pdf"] = Curriculo(enviado, enviado=True)
    return escolhidos
