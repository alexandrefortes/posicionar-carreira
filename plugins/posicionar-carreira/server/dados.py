"""Configuração e leitura local dos registros de carreira."""
from __future__ import annotations

import json
import os
from hashlib import sha256
from pathlib import Path
from urllib.parse import unquote


def _caminho_configurado(arquivo: Path) -> str:
    try:
        return arquivo.read_text(encoding="utf-8-sig").strip()
    except FileNotFoundError:
        return ""


def _pasta_absoluta(root: Path) -> Path:
    root = root.expanduser()
    if not root.is_absolute():
        raise FileNotFoundError("Use um caminho absoluto na configuração da pasta de dados (CARREIRA_ROOT).")
    return root.resolve()


def caminho_carreira_configurado() -> Path:
    """Retorna o caminho de dados escolhido, ainda que a pasta não exista."""
    configurado = os.environ.get("CARREIRA_ROOT")
    if configurado:
        return _pasta_absoluta(Path(configurado))
    legado = os.environ.get("POSICIONAR_CARREIRA_ROOT") or os.environ.get("PAPAO_ROOT")
    if legado:
        return _pasta_absoluta(Path(legado) / "carreira")

    home = Path.home()
    configurado = _caminho_configurado(home / ".config/posicionar-carreira/data-root.txt")
    if configurado:
        return _pasta_absoluta(Path(configurado))
    legado = _caminho_configurado(home / ".posicionar-carreira-raiz")
    return _pasta_absoluta((Path(legado) if legado else home / "PosicionarCarreira") / "carreira")


def resolver_carreira_root(root: Path | None = None, *, exigir_oportunidades: bool = True) -> Path:
    root = caminho_carreira_configurado() if root is None else _pasta_absoluta(root)
    if not root.is_dir() or (exigir_oportunidades and not (root / "oportunidades").is_dir()):
        raise FileNotFoundError("Aponte CARREIRA_ROOT para a pasta de dados que contém oportunidades/.")
    return root


def responsavel_pessoal(carreira: Path) -> str:
    try:
        configuracao = json.loads((carreira / "config.json").read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return "titular"
    nome = configuracao.get("responsavel", "titular") if isinstance(configuracao, dict) else None
    if not isinstance(nome, str) or not nome.strip() or nome.strip().casefold() in {"assistente", "empresa"}:
        raise ValueError("Use um nome para responsavel em config.json da pasta de dados.")
    return nome.strip()



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


def listar(carreira: Path) -> list[dict]:
    import gestao_vagas

    processos = sorted(
        gestao_vagas.load_processes(carreira), key=lambda processo: processo["atualizado_em"], reverse=True
    )
    por_id = {processo["id"]: processo for processo in processos}
    ordenados = [
        por_id.pop(processo_id)
        for processo_id in _ordem_painel(carreira)
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


def detalhar(carreira: Path, processo_id: str) -> dict:
    processo, conteudo = ler_processo(carreira, processo_id)
    return formatar_detalhe(carreira, processo, conteudo)


def formatar_detalhe(carreira: Path, processo: dict, conteudo: bytes) -> dict:
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
        "responsaveis": [responsavel_pessoal(carreira), "assistente", "empresa"],
        **{campo: processo.get(campo) for campo in (
            "proxima_acao", "responsavel", "prioridade", "prazo", "fonte_prazo", "revisar_em",
            "encerrada_em", "candidatura_confirmada", "candidatura_em", "fonte_candidatura",
            "disponibilidade_inscricao", "fonte_disponibilidade_inscricao",
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
    try:
        print(resolver_carreira_root())
    except OSError as exc:
        raise SystemExit(str(exc)) from None
