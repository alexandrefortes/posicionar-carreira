from __future__ import annotations

import os
import re
import tempfile
import unicodedata
from contextlib import contextmanager, ExitStack
from datetime import date
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit

import yaml

import gestao_vagas
import triagem
from dados import formatar_detalhe, ler_processo, responsavel_pessoal


CAMPOS_EDITAVEIS = frozenset((
    "titulo", "status", "prioridade", "proxima_acao", "responsavel",
    "prazo", "fonte_prazo", "revisar_em", "encerrada_em",
    "candidatura_confirmada", "candidatura_em", "fonte_candidatura",
    "disponibilidade_inscricao", "fonte_disponibilidade_inscricao",
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
    gravar_bytes(path, conteudo, original)
    return conteudo


def gravar_bytes(path, conteudo, original):
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


def _slug(nome):
    ascii_nome = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_nome).strip("-")[:72].rstrip("-") or "empresa"


def _criar(carreira, empresa, titulo, fonte, processo_id, previa, fonte_compartilhada):
    descricao = f"A fonte identifica a vaga {titulo} em {empresa}." if fonte_compartilhada else "Oportunidade cadastrada"
    entrada = evento(carreira, descricao, fonte, None)
    fonte = entrada["fonte"]
    existentes = gestao_vagas.load_processes(carreira)
    urls = [fonte] if not fonte_compartilhada and fonte.startswith(("http://", "https://")) else []
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
    arquivo = gestao_vagas.arquivo_original(carreira, fonte)
    if arquivo:
        gestao_vagas.validar_originais(carreira, existentes, {arquivo}, processo_id)
    registro = {
        "id": processo_id, "empresa": empresa, "titulo": titulo, "status": "identificada",
        "prioridade": "media",
        "proxima_acao": "Avaliar a vaga", "responsavel": responsavel_pessoal(carreira), "fonte_estado": fonte,
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
    return formatar_detalhe(carreira, {**registro, "_path": path}, conteudo)


def criar_vaga(carreira, empresa, titulo, fonte, processo_id=None, *, previa=False, fonte_compartilhada=False):
    carreira = carreira.resolve()
    empresa = texto(empresa, "a empresa")
    titulo = texto(titulo, "o título da vaga")
    if not isinstance(fonte_compartilhada, bool):
        raise ValueError("Indique se a fonte do cadastro é compartilhada.")
    if previa:
        return _criar(carreira, empresa, titulo, fonte, processo_id, previa, fonte_compartilhada)
    with trava(carreira / "oportunidades", ".posicionar-carreira-cadastro.lock"):
        return _criar(carreira, empresa, titulo, fonte, processo_id, previa, fonte_compartilhada)


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
    if "titulo" in mudancas:
        mudancas["titulo"] = texto(mudancas["titulo"], "o título da vaga")
    if mudancas.keys() & {"disponibilidade_inscricao", "fonte_disponibilidade_inscricao"}:
        anterior = registro.get("disponibilidade_inscricao") or None
        disponibilidade = mudancas.get("disponibilidade_inscricao", anterior)
        fonte_disponibilidade = mudancas.get("fonte_disponibilidade_inscricao")
        if disponibilidade is None:
            if fonte_disponibilidade is not None:
                raise ValueError("Informe a disponibilidade de inscrição para registrar sua fonte.")
            mudancas["fonte_disponibilidade_inscricao"] = None
        elif disponibilidade not in gestao_vagas.DISPONIBILIDADES_INSCRICAO:
            raise ValueError("Disponibilidade de inscrição inválida.")
        elif (disponibilidade != anterior or "fonte_disponibilidade_inscricao" in mudancas) and not fonte_disponibilidade:
            raise ValueError("Informe a fonte da disponibilidade de inscrição.")
    for campo in ("fonte_prazo", "fonte_candidatura", "fonte_disponibilidade_inscricao"):
        if mudancas.get(campo) is not None:
            mudancas[campo] = fonte_valida(carreira, mudancas[campo])
    for campo in ("prazo", "revisar_em", "encerrada_em", "candidatura_em"):
        valor = gestao_vagas.date(mudancas.get(campo), campo)
        if valor and campo in ("encerrada_em", "candidatura_em") and valor > date.today():
            raise ValueError(f"A data de {campo} não pode estar no futuro.")
    if mudancas.get("prazo") and not mudancas.get("fonte_prazo"):
        raise ValueError("Informe a fonte do prazo.")
    if "prazo" in mudancas and mudancas["prazo"] is None:
        mudancas["fonte_prazo"] = None
    confirmada = mudancas.get("candidatura_confirmada", registro["candidatura_confirmada"])
    if registro["candidatura_confirmada"] and not confirmada:
        raise ValueError("O envio confirmado deve permanecer no histórico do processo.")
    if confirmada and not registro["candidatura_confirmada"] and not mudancas.get("fonte_candidatura"):
        raise ValueError("Informe a fonte que comprova o envio da candidatura.")
    anterior = registro["status"]
    status = mudancas.get("status", anterior)
    if status != anterior:
        if status not in gestao_vagas.TRANSICOES_STATUS[anterior]:
            raise ValueError(f"Transição de status inválida: {anterior} → {status}.")
        if status == "candidatura-enviada" and not confirmada:
            raise ValueError("Confirme o envio da candidatura e informe a evidência.")
        mudancas["fonte_estado"] = entrada["fonte"]
    return {campo: valor for campo, valor in mudancas.items() if registro.get(campo) != valor}


def _editar(carreira, processo_id, revisao, entrada, campos, previa, triagem_id=None):
    registro, original = ler_processo(carreira, processo_id)
    historico = registro["eventos"]
    mesmas_chaves = ("data", "descricao", "fonte")
    repetido = next((e for e in historico if all(e.get(k) == entrada[k] for k in mesmas_chaves)), None)
    if repetido and triagem_id and campos is not None:
        valores = {**registro, **{k: v["atual"] for k, v in repetido.get("alteracoes", {}).items()}}
        if not campos or any(k not in CAMPOS_EDITAVEIS or valores.get(k) != v for k, v in campos.items()):
            raise ValueError("A resolução anterior registrou outras alterações.")
    if triagem_id and repetido and triagem_id in repetido.get("triagem", []):
        if previa:
            return {"id": processo_id, "revisao": sha256(original).hexdigest(), "evento": repetido}
        return formatar_detalhe(carreira, registro, original)
    if sha256(original).hexdigest() != revisao:
        raise ValueError(CONFLITO)
    if repetido and not triagem_id:
        raise ValueError(EVENTO_REPETIDO)
    mudancas = _mudancas(carreira, registro, campos, entrada) if campos is not None and not repetido else {}
    if campos is not None and not repetido and not mudancas:
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
    if triagem_id:
        (repetido or entrada).setdefault("triagem", []).append(triagem_id)
    if not repetido:
        historico.append(entrada)
    gestao_vagas.validate_process(carreira, path, registro)
    if previa:
        return {"id": processo_id, "revisao": revisao, "mudancas": mudancas, "evento": entrada}
    conteudo = gravar(path, registro, original)
    return formatar_detalhe(carreira, {**registro, "_path": path}, conteudo)


def _operar(carreira, processo_id, revisao, descricao, fonte, data, campos, previa, pendencia):
    carreira = carreira.resolve()
    entrada = evento(carreira, descricao, fonte, data)
    path = gestao_vagas.process_path(carreira, processo_id)
    if not path.is_file():
        raise ValueError("Processo não encontrado. Selecione um ID da lista de vagas.")
    fontes = {entrada["fonte"]}
    if campos:
        fontes.update(fonte_valida(carreira, campos[k]) for k in gestao_vagas.CAMPOS_FONTE if campos.get(k))
    arquivos = {gestao_vagas.arquivo_original(carreira, fonte) for fonte in fontes} - {None}
    ident = None
    with ExitStack() as locks:
        if (arquivos or pendencia is not None) and not previa:
            locks.enter_context(trava(carreira / "oportunidades", ".posicionar-carreira-cadastro.lock"))
        if not previa:
            locks.enter_context(trava(path.parent, ".posicionar-carreira.lock"))
        if arquivos or pendencia is not None:
            registros = gestao_vagas.load_processes(carreira)
        if arquivos:
            gestao_vagas.validar_originais(carreira, registros, arquivos, processo_id)
        if pendencia is not None:
            caminho, original, fechado = triagem.preparar(carreira, processo_id, pendencia)
            ident = triagem.chave(pendencia.strip())
            for r in registros:
                for e in r["eventos"]:
                    if ident in e.get("triagem", []) and (r["id"] != processo_id or any(
                        e.get(k) != entrada[k] for k in ("data", "descricao", "fonte")
                    )):
                        raise ValueError("A pendência já está vinculada a outro fato. Confira o dossiê.")
        resultado = _editar(carreira, processo_id, revisao, entrada, campos, previa, ident)
        if pendencia is not None and not previa and fechado != original:
            try:
                gravar_bytes(caminho, fechado, original)
            except (OSError, ValueError) as exc:
                raise ValueError("Fato registrado. Confira a triagem e repita a resolução para encerrá-la.") from exc
        return resultado


def registrar_evento(carreira, processo_id, revisao, descricao, fonte, data=None, *, previa=False, pendencia_triagem=None):
    return _operar(carreira, processo_id, revisao, descricao, fonte, data, None, previa, pendencia_triagem)


def atualizar_vaga(carreira, processo_id, revisao, descricao, fonte, mudancas, data=None, *, previa=False, pendencia_triagem=None):
    if not isinstance(mudancas, dict):
        raise ValueError("Informe os campos editáveis do processo.")
    return _operar(carreira, processo_id, revisao, descricao, fonte, data, mudancas, previa, pendencia_triagem)


OPERACOES = {
    "criar_vaga": criar_vaga,
    "registrar_evento": registrar_evento,
    "atualizar_vaga": atualizar_vaga,
}


def executar_operacao(root, name, argumentos, *, previa=False):
    return OPERACOES[name](root, **argumentos, previa=previa)
