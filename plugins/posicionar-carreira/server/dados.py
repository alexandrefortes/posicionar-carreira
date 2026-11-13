"""Leitura local do registro oficial de oportunidades."""
from __future__ import annotations

import os
from hashlib import sha256
from pathlib import Path
from urllib.parse import unquote


def resolver_raiz(root: Path | None = None) -> Path:
    if root is None:
        configurado = os.environ.get("POSICIONAR_CARREIRA_ROOT")
        if not configurado:
            seletor = Path.home() / ".posicionar-carreira-raiz"
            if seletor.is_file():
                configurado = seletor.read_text(encoding="utf-8-sig").strip()
        root = Path(configurado) if configurado else Path.home() / "PosicionarCarreira"
    root = root.expanduser()
    if not root.is_absolute():
        raise ValueError("Informe um caminho absoluto para a pasta de dados.")
    root = root.resolve()
    if not (root / "carreira" / "oportunidades").is_dir():
        raise FileNotFoundError("Inicialize a pasta de dados ou configure a raiz da base existente. Consulte o guia de instalação.")
    return root


def _processos(raiz: Path) -> list[dict]:
    import gestao_vagas

    return gestao_vagas.load_processes(raiz / "carreira")


def _resumo(processo: dict) -> dict:
    campos = ("id", "empresa", "titulo", "estado", "etapa", "resultado", "atualizado_em")
    return {campo: processo.get(campo) for campo in campos}


def _ordem_painel(carreira: Path) -> list[str]:
    import gestao_vagas

    try:
        texto = (carreira / "painel-vagas.md").read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return []

    ordem = []
    secao_de_vagas = False
    for linha in texto.splitlines():
        if linha.startswith("## "):
            titulo = linha[3:].strip().casefold()
            secao_de_vagas = not titulo.startswith(
                ("revisão recebida", "revisões recebidas", "empresas de interesse e pendências")
            )
        if not secao_de_vagas:
            continue
        for link in gestao_vagas.LINK.findall(linha):
            destino = unquote(link.strip().strip("<>").split("#", 1)[0]).removeprefix("./")
            partes = destino.split("/")
            if len(partes) == 4 and partes[0] == "oportunidades" and partes[-1] == "processo.md":
                ordem.append("/".join(partes[1:3]))
    return ordem


def listar(raiz: Path) -> list[dict]:
    processos = sorted(
        _processos(raiz), key=lambda processo: processo["atualizado_em"], reverse=True
    )
    por_id = {processo["id"]: processo for processo in processos}
    ordenados = [
        por_id.pop(processo_id)
        for processo_id in _ordem_painel(raiz / "carreira")
        if processo_id in por_id
    ]
    ordenados.extend(por_id.values())
    return [_resumo(processo) for processo in ordenados]


def ler_processo(carreira: Path, processo_id: str) -> tuple[dict, bytes]:
    import gestao_vagas

    arquivo = gestao_vagas.process_path(carreira, processo_id)
    try:
        conteudo = arquivo.read_bytes()
    except FileNotFoundError as exc:
        raise ValueError("Processo não encontrado. Selecione um ID da lista de vagas.") from exc
    return gestao_vagas.load_process(carreira, processo_id, text=conteudo.decode("utf-8")), conteudo


def detalhar(raiz: Path, processo_id: str) -> dict:
    processo, conteudo = ler_processo(raiz / "carreira", processo_id)
    return formatar_detalhe(processo, conteudo)


def formatar_detalhe(processo: dict, conteudo: bytes) -> dict:
    from curriculos import resolver_curriculos

    arquivo = processo["_path"]
    dossie = arquivo.parent
    tipos = {"envios": "envio", "entrevistas": "entrevista"}
    materiais = []
    for item in sorted(dossie.rglob("*")):
        if item == arquivo or item.name == ".posicionar-carreira.lock" or (
            item.name.startswith(".processo-") and item.suffix == ".tmp"
        ) or not item.is_file() or not item.resolve().is_relative_to(dossie):
            continue
        relativo = item.relative_to(dossie)
        materiais.append({
            "caminho": relativo.as_posix(),
            "tipo": tipos.get(relativo.parts[0], "material"),
        })

    return {
        **_resumo(processo),
        "processo": str(arquivo),
        "revisao": sha256(conteudo).hexdigest(),
        **{campo: processo.get(campo) for campo in (
            "proxima_acao", "responsavel", "prioridade", "prazo", "fonte_prazo", "revisar_em",
            "encerrada_em", "candidatura_confirmada", "candidatura_em", "fonte_candidatura",
        )},
        "eventos": [
            {campo: evento[campo] for campo in ("data", "registrado_em", "descricao", "fonte", "alteracoes")
             if campo in evento}
            for evento in processo["eventos"]
        ],
        "materiais": materiais,
        "curriculos": {
            tipo: {"nome": curriculo.caminho.name, "enviado": curriculo.enviado}
            for tipo, curriculo in resolver_curriculos(processo, conteudo).items()
        },
    }


if __name__ == "__main__":
    print(resolver_raiz())
