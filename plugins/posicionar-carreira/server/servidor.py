"""Servidor MCP de gestão dos dossiês, por stdio."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dados import detalhar, ler_processo, listar, resolver_raiz


VERSION = "0.5.0"
UI_URI = "ui://posicionar-carreira-local/painel-v5.html"
UI_MIME = "text/html;profile=mcp-app"
UI_FILE = Path(__file__).resolve().parents[1] / "ui" / "painel.html"
PROTOCOLS = ("2025-11-25", "2025-06-18", "2025-03-26")
RESOURCE = {"uri": UI_URI, "name": "Vagas", "mimeType": UI_MIME}
EMPTY_INPUT = {"type": "object", "properties": {}, "additionalProperties": False}
TOOLS = [
    {
        "name": "abrir_painel",
        "title": "Abrir vagas",
        "description": "Abre o painel de vagas no chat. Use listar_vagas se precisar da lista em texto.",
        "inputSchema": EMPTY_INPUT,
        "_meta": {
            "ui": {"resourceUri": UI_URI, "visibility": ["model"], "preferredModelDisplayMode": "inline"},
            "openai/ui": {"entrypoints": [{"type": "thread"}]},
        },
    },
    {
        "name": "listar_vagas",
        "title": "Listar vagas",
        "description": "Lê os processos oficiais e retorna ID, empresa, cargo, estado, etapa e resultado.",
        "inputSchema": EMPTY_INPUT,
    },
    {
        "name": "detalhar_vaga",
        "title": "Consultar processo",
        "description": "Lê histórico, materiais, próximo passo e caminho oficial pelo ID retornado por listar_vagas.",
        "inputSchema": {
            "type": "object",
            "properties": {"processo_id": {"type": "string", "minLength": 1}},
            "required": ["processo_id"],
            "additionalProperties": False,
        },
    },
]
for tool in TOOLS:
    tool["annotations"] = {"readOnlyHint": True, "openWorldHint": False}

STRING = {"type": "string", "minLength": 1}
OPTIONAL_DATE = {"type": ["string", "null"], "format": "date"}
NULLABLE = {"type": ["string", "null"]}
EVENT_INPUT = {
    "processo_id": STRING, "revisao": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "descricao": STRING, "fonte": STRING, "data": OPTIONAL_DATE,
}
EDIT_INPUT = {
    "estado": STRING, "etapa": STRING, "resultado": NULLABLE, "prioridade": STRING,
    "proxima_acao": STRING, "responsavel": STRING, "prazo": OPTIONAL_DATE,
    "fonte_prazo": NULLABLE, "revisar_em": OPTIONAL_DATE, "encerrada_em": OPTIONAL_DATE,
    "candidatura_confirmada": {"type": "boolean"}, "candidatura_em": OPTIONAL_DATE,
    "fonte_candidatura": NULLABLE,
}
for name, title, description, props, required in (
    (
        "criar_vaga", "Cadastrar vaga",
        "Cria um processo local identificado. Use a URL do anúncio ou uma fonte relativa à pasta carreira.",
        {"empresa": STRING, "titulo": STRING, "fonte": STRING, "processo_id": STRING},
        ["empresa", "titulo", "fonte"],
    ),
    (
        "registrar_evento", "Registrar evento",
        "Acrescenta uma nota ou retorno ao processo. Use a revisão de detalhar_vaga e informe data conhecida e fonte.",
        EVENT_INPUT, ["processo_id", "revisao", "descricao", "fonte"],
    ),
    (
        "atualizar_vaga", "Atualizar processo",
        "Atualiza os campos informados e registra um evento com fonte. Use a revisão de detalhar_vaga. "
        "Para confirmar envio, informe candidatura_confirmada e fonte_candidatura. "
        "Para alterar prazo, informe fonte_prazo. Encerrar exige resultado e reabrir usa estado aberto.",
        {**EVENT_INPUT, "mudancas": {"type": "object", "properties": EDIT_INPUT,
                                   "minProperties": 1, "additionalProperties": False}},
        ["processo_id", "revisao", "descricao", "fonte", "mudancas"],
    ),
):
    TOOLS.append({
        "name": name, "title": title, "description": description,
        "inputSchema": {"type": "object", "properties": props, "required": required,
                        "additionalProperties": False},
        "annotations": {"readOnlyHint": False, "destructiveHint": name == "atualizar_vaga",
                        "idempotentHint": False, "openWorldHint": False},
    })
TOOLS.append({
    "name": "abrir_curriculo",
    "title": "Abrir currículo no Windows",
    "description": "Abre o arquivo de currículo da vaga selecionada com o aplicativo associado no Windows.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "processo_id": STRING,
            "tipo": {"type": "string", "enum": ["markdown", "pdf"]},
            "enviado": {"type": "boolean"},
        },
        "required": ["processo_id", "tipo", "enviado"],
        "additionalProperties": False,
    },
    "_meta": {"ui": {"visibility": ["app"]}},
    "annotations": {"readOnlyHint": False, "destructiveHint": False,
                    "idempotentHint": False, "openWorldHint": False},
})
INPUTS = {tool["name"]: tool["inputSchema"] for tool in TOOLS}


class RpcError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def tool_result(data=None, *, message=None, error=False):
    if message is None:
        message = json.dumps(data, ensure_ascii=False)
    result = {"content": [{"type": "text", "text": message}]}
    if error:
        result["isError"] = True
    elif data is not None:
        result["structuredContent"] = data
    return result


def validar_argumentos(name, arguments):
    if not isinstance(name, str) or name not in INPUTS:
        raise ValueError("Ferramenta desconhecida.")
    schema = INPUTS[name]
    if (not isinstance(arguments, dict) or arguments.keys() - schema["properties"].keys()
            or not set(schema.get("required", ())) <= arguments.keys()):
        raise ValueError("Confira os argumentos da ferramenta.")


def abrir_curriculo(root, processo_id, tipo, enviado):
    from curriculos import resolver_curriculos

    if tipo not in ("markdown", "pdf") or not isinstance(enviado, bool):
        raise ValueError("Informe o formato e a versão do currículo.")
    processo, conteudo = ler_processo(root / "carreira", processo_id)
    curriculo = resolver_curriculos(processo, conteudo).get(tipo)
    if curriculo is None or curriculo.enviado != enviado:
        raise ValueError("O currículo disponível mudou. Reabra o detalhe da vaga.")
    if not hasattr(os, "startfile"):
        raise ValueError("A abertura de currículos requer o Codex local no Windows.")
    try:
        os.startfile(str(curriculo.caminho))
    except OSError as exc:
        formato = "Markdown" if tipo == "markdown" else "PDF"
        if getattr(exc, "winerror", None) == 1155:
            raise OSError(f"Associe um aplicativo aos arquivos {formato} nas configurações do Windows.") from exc
        raise OSError(f"O Windows não conseguiu abrir o currículo em {formato}.") from exc
    return {"nome": curriculo.caminho.name, "enviado": curriculo.enviado}


def call_tool(params):
    name = params.get("name")
    arguments = params.get("arguments", {})
    try:
        validar_argumentos(name, arguments)
    except ValueError as exc:
        raise RpcError(-32602, str(exc)) from exc

    if name == "abrir_painel":
        return tool_result(message="Painel de vagas. A consulta por texto está disponível em listar_vagas.")

    try:
        root = resolver_raiz()
        if name == "listar_vagas":
            return tool_result({"vagas": listar(root)})
        if name == "detalhar_vaga":
            return tool_result(detalhar(root, arguments["processo_id"]))
        if name == "abrir_curriculo":
            return tool_result(abrir_curriculo(root, **arguments))
        from operacoes import executar_operacao

        return tool_result(executar_operacao(root, name, arguments))
    except ModuleNotFoundError as exc:
        if exc.name == "yaml":
            return tool_result(message="Instale PyYAML 6 no Python usado pelo plugin.", error=True)
        raise
    except (ValueError, OSError) as exc:
        return tool_result(message=str(exc), error=True)


def dispatch(method, params):
    if method == "initialize":
        version = params.get("protocolVersion")
        return {
            "protocolVersion": version if version in PROTOCOLS else PROTOCOLS[0],
            "serverInfo": {"name": "posicionar-carreira-local", "version": VERSION},
            "capabilities": {"tools": {}, "resources": {}},
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        return call_tool(params)
    if method == "resources/list":
        return {"resources": [RESOURCE]}
    if method == "resources/templates/list":
        return {"resourceTemplates": []}
    if method == "resources/read":
        if params.get("uri") != UI_URI:
            raise RpcError(-32002, "Recurso desconhecido.")
        return {"contents": [{
            "uri": UI_URI,
            "mimeType": UI_MIME,
            "text": UI_FILE.read_text(encoding="utf-8"),
            "_meta": {"ui": {"csp": {"connectDomains": [], "resourceDomains": []}}},
        }]}
    raise RpcError(-32601, "Método desconhecido.")


def respond(line):
    envelope = {"jsonrpc": "2.0", "id": None}
    try:
        try:
            request = json.loads(line)
        except (ValueError, UnicodeError) as exc:
            raise RpcError(-32700, "JSON inválido.") from exc
        if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
            raise RpcError(-32600, "Requisição inválida.")
        method = request.get("method")
        if not isinstance(method, str):
            raise RpcError(-32600, "Requisição inválida.")
        if "id" not in request:
            return
        envelope["id"] = request["id"]
        params = request.get("params", {})
        if not isinstance(params, dict):
            raise RpcError(-32602, "Parâmetros inválidos.")
        envelope["result"] = dispatch(method, params)
    except RpcError as exc:
        envelope["error"] = {"code": exc.code, "message": str(exc)}
    except Exception as exc:
        print(f"Falha no MCP posicionar-carreira-local: {type(exc).__name__}", file=sys.stderr)
        envelope["error"] = {"code": -32603, "message": "Falha interna no servidor de carreira."}
    return envelope


def main():
    if sys.argv[1:] == ["--raiz"]:
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            print(resolver_raiz())
        except (OSError, ValueError) as exc:
            raise SystemExit(str(exc)) from exc
        return
    for line in sys.stdin.buffer:
        response = respond(line)
        if response is not None:
            sys.stdout.buffer.write(json.dumps(response, ensure_ascii=False).encode("utf-8") + b"\n")
            sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
