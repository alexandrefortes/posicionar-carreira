import re
from hashlib import sha256
from urllib.parse import quote, unquote


PREFIXO = r"(?:\|[ \t]*|(?:[-*+]|\d+[.)])[ \t]+(?:\[[ xX]\][ \t]+)?)?"
RESOLVIDA = re.compile(r"^(" + PREFIXO + r")\[Resolvida\]\(\.\./oportunidades/([^()]+)/processo\.md\) · (.*)$")


def chave(linha):
    return sha256(linha.encode("utf-8")).hexdigest()


def preparar(carreira, processo_id, pendencia):
    if not isinstance(pendencia, str) or not pendencia.strip() or len(pendencia.splitlines()) != 1:
        raise ValueError("Informe a linha completa de uma única pendência na triagem.")
    linha = pendencia.strip()
    prefixo = re.match(PREFIXO, linha)[0]
    if (linha.startswith(("#", "```", "---")) or not linha[len(prefixo):].strip(" |-:")
            or RESOLVIDA.match(linha) or "[x]" in prefixo.lower()):
        raise ValueError("Selecione a entrada pendente na triagem.")
    destino = quote(processo_id, safe="/")
    marcada = prefixo.replace("[ ]", "[x]") + f"[Resolvida](../oportunidades/{destino}/processo.md) · " + linha[len(prefixo):]
    caminho = carreira / "monitoramento" / "triagem.md"
    if caminho.resolve() != caminho or not caminho.is_file():
        raise ValueError("Não foi possível localizar monitoramento/triagem.md na base.")
    original = caminho.read_bytes()
    linhas = original.decode("utf-8-sig").splitlines(keepends=True)
    indices = [i for i, item in enumerate(linhas) if item.strip() in (linha, marcada)]
    if len(indices) != 1:
        raise ValueError("A pendência mudou, é ambígua ou pertence a outro processo. Confira a triagem.")
    i = indices[0]
    if linhas[i].strip() == marcada:
        return caminho, original, original
    linhas[i] = linhas[i].replace(linha, marcada, 1)
    encoding = "utf-8-sig" if original.startswith(b"\xef\xbb\xbf") else "utf-8"
    return caminho, original, "".join(linhas).encode(encoding)


def validar(carreira, registros):
    vinculados = {}
    for processo in registros:
        for evento in processo["eventos"]:
            pendencias = evento.get("triagem", [])
            if not isinstance(pendencias, list):
                raise ValueError(f"Vínculo de triagem inválido em {processo['id']}.")
            for ident in pendencias:
                if not isinstance(ident, str) or not re.fullmatch(r"[0-9a-f]{64}", ident) or ident in vinculados:
                    raise ValueError(f"Vínculo de triagem inválido ou duplicado em {processo['id']}.")
                vinculados[ident] = processo["id"]
    arquivo = carreira / "monitoramento" / "triagem.md"
    linhas = arquivo.read_text(encoding="utf-8-sig").splitlines() if arquivo.is_file() else []
    for linha in linhas:
        marca = RESOLVIDA.match(linha.strip())
        if marca:
            prefixo, destino, corpo = marca.groups()
            ident = chave(prefixo.replace("[x]", "[ ]") + corpo)
            if vinculados.pop(ident, None) != unquote(destino):
                raise ValueError(f"Pendência marcada como resolvida sem evento correspondente: {destino}.")
    if vinculados:
        raise ValueError(f"Evento registrado com pendência aberta ou ausente na triagem: {next(iter(vinculados.values()))}.")
