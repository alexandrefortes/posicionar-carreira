"""Operações de cadastro e acompanhamento compartilhadas pelo MCP e pelo terminal."""
from __future__ import annotations

import os
import re
import tempfile
import unicodedata
from contextlib import contextmanager
from datetime import date
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit

import yaml

import gestao_vagas
from dados import formatar_detalhe, ler_processo


CAMPOS_EDITAVEIS = frozenset((
    "estado", "etapa", "resultado", "prioridade", "proxima_acao", "responsavel",
    "prazo", "fonte_prazo", "revisar_em", "encerrada_em",
    "candidatura_confirmada", "candidatura_em", "fonte_candidatura",
))
CONFLITO = "O processo mudou desde a abertura. Recarregue o detalhe e revise os dados."
EVENTO_REPETIDO = "Este evento já foi registrado no processo."


def texto(valor, campo):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"Preencha {campo}.")
    return valor.strip()


def fonte_valida(carreira, fonte):
    fonte = texto(fonte, "a fonte")
    if fonte.startswith(("http://", "https://")):
        if not urlsplit(fonte).hostname:
            raise ValueError("Informe uma URL completa como fonte.")
    elif Path(fonte.split("#", 1)[0]).is_absolute():
        raise ValueError("Use uma fonte local relativa à pasta carreira.")
    gestao_vagas.check_source(carreira, fonte)
    return fonte


def evento(carreira, descricao, fonte, data):
    hoje = date.today()
    ocorrencia = gestao_vagas.date(data, "Data do evento")
    if ocorrencia and ocorrencia > hoje:
        raise ValueError("A data do evento não pode estar no futuro.")
    return {
        "data": data, "registrado_em": hoje.isoformat(),
        "descricao": texto(descricao, "a descrição do evento"), "fonte": fonte_valida(carreira, fonte),
    }


@contextmanager
def trava(pasta, nome):
    caminho = pasta / nome
    try:
        arquivo = caminho.open("xb")
    except FileExistsError as exc:
        raise ValueError("O processo está em gravação. Recarregue e tente novamente.") from exc
    try:
        arquivo.close()
        yield
    finally:
        caminho.unlink()


def gravar(path, registro, original=None):
    quebra = b"\r\n" if original and original.startswith(b"---\r\n") else b"\n"
    corpo = re.split(rb"(?:\r\n|\r|\n)---(?:\r\n|\r|\n)", original, maxsplit=1)[1] if original else b"# Processo\n"
    yaml_texto = yaml.safe_dump(registro, allow_unicode=True, sort_keys=False)
    prefixo = ("---\n" + yaml_texto + "---\n").encode("utf-8").replace(b"\n", quebra)
    conteudo = prefixo + corpo
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".processo-", suffix=".tmp", delete=False) as saida:
        temporario = Path(saida.name)
        try:
            saida.write(conteudo)
            saida.flush()
            os.fsync(saida.fileno())
            saida.close()
            if original is not None:
                if not path.is_file() or path.read_bytes() != original:
                    raise ValueError(CONFLITO)
                os.replace(temporario, path)
            else:
                os.link(temporario, path)
        finally:
            saida.close()
            temporario.unlink(missing_ok=True)
    return conteudo


def _slug(nome):
    ascii_nome = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_nome).strip("-")[:72].rstrip("-") or "empresa"


def _criar(carreira, empresa, titulo, fonte, processo_id, previa):
    entrada = evento(carreira, "Oportunidade cadastrada", fonte, None)
    fonte = entrada["fonte"]
    existentes = gestao_vagas.load_processes(carreira)
    urls = [fonte] if fonte.startswith(("http://", "https://")) else []
    if urls and any(fonte in r.get("urls", []) or
                    (r["eventos"] and r["eventos"][0]["fonte"] == fonte) for r in existentes):
        raise ValueError("Já existe um processo com esta URL. Abra o dossiê existente.")
    if not urls and processo_id is None and any(
        r["empresa"].casefold() == empresa.casefold()
        and r["titulo"].casefold() == titulo.casefold()
        and r["eventos"][0]["fonte"] == fonte for r in existentes
    ):
        raise ValueError("Já existe um processo com esta empresa, título e fonte. Confira o dossiê.")
    aliases = []
    if processo_id is not None:
        if not isinstance(processo_id, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*/[a-z0-9]+(?:-[a-z0-9]+)+", processo_id):
            raise ValueError("Use um ID no formato empresa/plataforma-identificador.")
        _, identificador = processo_id.split("/")
        if not identificador.startswith("local-"):
            plataforma, externo = identificador.split("-", 1)
            aliases = [f"{plataforma}:{externo}"]
            if any(aliases[0] in r.get("ids_externos", []) for r in existentes):
                raise ValueError("O identificador externo já pertence a outro processo.")
    else:
        pasta = carreira / "oportunidades" / _slug(empresa)
        locais = (re.fullmatch(r"local-(\d+)", item.name) for item in pasta.iterdir()) if pasta.is_dir() else ()
        numero = max((int(m.group(1)) for m in locais if m), default=0) + 1
        processo_id = f"{pasta.name}/local-{numero:03}"
    path = gestao_vagas.process_path(carreira, processo_id)
    if path.parent.is_reserved() or path.parent.parent.is_reserved():
        raise ValueError("O ID contém um nome reservado pelo sistema.")
    if path.parent.exists():
        raise ValueError("Já existe um dossiê com esse ID.")
    registro = {
        "id": processo_id, "empresa": empresa, "titulo": titulo, "estado": "aberto",
        "etapa": "identificada", "resultado": None, "prioridade": "media",
        "proxima_acao": "Avaliar a vaga", "responsavel": "candidato", "fonte_estado": fonte,
        "identificada_em": None, "atualizado_em": entrada["registrado_em"], "encerrada_em": None,
        "candidatura_confirmada": False, "candidatura_em": None, "fonte_candidatura": None,
        "prazo": None, "fonte_prazo": None, "revisar_em": None,
        "ids_externos": aliases, "urls": urls, "eventos": [entrada],
    }
    gestao_vagas.validate_process(carreira, path, registro)
    if previa:
        return {"id": processo_id, "acao": "cadastrar", "processo": registro}
    path.parent.mkdir(parents=True)
    try:
        conteudo = gravar(path, registro)
    except BaseException:
        if not any(path.parent.iterdir()):
            path.parent.rmdir()
        raise
    return formatar_detalhe({**registro, "_path": path}, conteudo)


def criar_vaga(raiz, empresa, titulo, fonte, processo_id=None, *, previa=False):
    carreira = (raiz / "carreira").resolve()
    empresa = texto(empresa, "a empresa")
    titulo = texto(titulo, "o título da vaga")
    if previa:
        return _criar(carreira, empresa, titulo, fonte, processo_id, previa)
    with trava(carreira / "oportunidades", ".posicionar-carreira-cadastro.lock"):
        return _criar(carreira, empresa, titulo, fonte, processo_id, previa)


def _mudancas(carreira, registro, campos, entrada):
    if not isinstance(campos, dict) or not campos or campos.keys() - CAMPOS_EDITAVEIS:
        raise ValueError("Informe apenas os campos editáveis do processo.")
    for campo, valor in campos.items():
        if campo == "candidatura_confirmada":
            if not isinstance(valor, bool):
                raise ValueError("Informe se o envio foi confirmado.")
        elif valor is not None and not isinstance(valor, str):
            raise ValueError(f"Valor inválido para {campo}.")
    mudancas = {campo: valor.strip() if isinstance(valor, str) else valor for campo, valor in campos.items()}
    for campo in ("fonte_prazo", "fonte_candidatura"):
        if mudancas.get(campo) is not None:
            mudancas[campo] = fonte_valida(carreira, mudancas[campo])
    for campo in ("prazo", "revisar_em", "encerrada_em", "candidatura_em"):
        valor = gestao_vagas.date(mudancas.get(campo), campo)
        if valor and campo in ("encerrada_em", "candidatura_em") and valor > date.today():
            raise ValueError(f"A data de {campo} não pode estar no futuro.")
    if registro["estado"] == "encerrado" and mudancas.get("estado", "encerrado") != "encerrado":
        if mudancas["estado"] != "aberto" or mudancas.get("resultado") or mudancas.get("encerrada_em"):
            raise ValueError("Para reabrir, selecione Aberto e deixe resultado e encerramento vazios.")
        mudancas.update(resultado=None, encerrada_em=None)
    if mudancas.get("prazo") and not mudancas.get("fonte_prazo"):
        raise ValueError("Informe a fonte do prazo.")
    if "prazo" in mudancas and mudancas["prazo"] is None:
        mudancas["fonte_prazo"] = None
    confirmada = mudancas.get("candidatura_confirmada", registro["candidatura_confirmada"])
    if registro["candidatura_confirmada"] and not confirmada:
        raise ValueError("O envio confirmado deve permanecer no histórico do processo.")
    if confirmada and not registro["candidatura_confirmada"] and not mudancas.get("fonte_candidatura"):
        raise ValueError("Informe a fonte que comprova o envio da candidatura.")
    if mudancas.get("etapa") == "candidatura_enviada" and not confirmada:
        raise ValueError("Confirme o envio da candidatura e informe a evidência.")
    if any(campo in mudancas and mudancas[campo] != registro.get(campo)
           for campo in ("estado", "etapa", "resultado")):
        mudancas["fonte_estado"] = entrada["fonte"]
    return {campo: valor for campo, valor in mudancas.items() if registro.get(campo) != valor}


def _editar(carreira, processo_id, revisao, entrada, campos, previa):
    registro, original = ler_processo(carreira, processo_id)
    if sha256(original).hexdigest() != revisao:
        raise ValueError(CONFLITO)
    historico = registro["eventos"]
    if any(all(anterior.get(k) == entrada[k] for k in ("data", "descricao", "fonte")) for anterior in historico):
        raise ValueError(EVENTO_REPETIDO)
    mudancas = _mudancas(carreira, registro, campos, entrada) if campos is not None else {}
    if campos is not None and not mudancas:
        raise ValueError("Nenhum campo mudou. Use Registrar evento para acrescentar uma nota.")
    path = registro.pop("_path")
    registro.pop("_score")
    if mudancas:
        entrada["alteracoes"] = {
            campo: {"anterior": registro.get(campo), "atual": valor}
            for campo, valor in mudancas.items() if campo != "fonte_estado"
        }
    registro.update(mudancas)
    registro["atualizado_em"] = max(registro["atualizado_em"], entrada["registrado_em"])
    historico.append(entrada)
    gestao_vagas.validate_process(carreira, path, registro)
    if previa:
        return {"id": processo_id, "revisao": revisao, "mudancas": mudancas, "evento": entrada}
    conteudo = gravar(path, registro, original)
    return formatar_detalhe({**registro, "_path": path}, conteudo)


def _operar(raiz, processo_id, revisao, descricao, fonte, data, campos, previa):
    carreira = (raiz / "carreira").resolve()
    entrada = evento(carreira, descricao, fonte, data)
    if previa:
        return _editar(carreira, processo_id, revisao, entrada, campos, previa)
    path = gestao_vagas.process_path(carreira, processo_id)
    if not path.is_file():
        raise ValueError("Processo não encontrado. Selecione um ID da lista de vagas.")
    with trava(path.parent, ".posicionar-carreira.lock"):
        return _editar(carreira, processo_id, revisao, entrada, campos, previa)


def registrar_evento(raiz, processo_id, revisao, descricao, fonte, data=None, *, previa=False):
    return _operar(raiz, processo_id, revisao, descricao, fonte, data, None, previa)


def atualizar_vaga(raiz, processo_id, revisao, descricao, fonte, mudancas, data=None, *, previa=False):
    if not isinstance(mudancas, dict):
        raise ValueError("Informe os campos editáveis do processo.")
    return _operar(raiz, processo_id, revisao, descricao, fonte, data, mudancas, previa)


OPERACOES = {
    "criar_vaga": criar_vaga,
    "registrar_evento": registrar_evento,
    "atualizar_vaga": atualizar_vaga,
}


def executar_operacao(root, name, argumentos, *, previa=False):
    return OPERACOES[name](root, **argumentos, previa=previa)
