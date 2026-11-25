from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from configuracao import MODELOS, inicializar_carreira, verificar_configuracao
from dados import detalhar, ler_processo, listar, resolver_carreira_root
from gestao_vagas import DISPONIBILIDADES_INSCRICAO, TRANSICOES_STATUS, lint
from diagnosticos import formatar_lint


VERSION = "0.10.1"
UI_URI = "ui://posicionar-carreira-local/painel-v8.html"
WELCOME_URI = "ui://posicionar-carreira-local/boas-vindas.html"
DASHBOARD_URI = "ui://posicionar-carreira-local/dashboard.html"
UI_MIME = "text/html;profile=mcp-app"
UI_FILE = Path(__file__).resolve().parents[1] / "ui" / "painel.html"
PROTOCOLS = ("2025-11-25", "2025-06-18", "2025-03-26")
RESOURCE = {"uri": UI_URI, "name": "Painel de vagas", "mimeType": UI_MIME}
WELCOME_RESOURCE = {"uri": WELCOME_URI, "name": "Boas-vindas ao Posicionar Carreira", "mimeType": UI_MIME}
DASHBOARD_RESOURCE = {"uri": DASHBOARD_URI, "name": "Dashboard", "mimeType": UI_MIME}
EMPTY_INPUT = {"type": "object", "properties": {}, "additionalProperties": False}
STRING = {"type": "string", "minLength": 1}
PASTA_ABSOLUTA = {**STRING, "description": "Caminho absoluto de uma pasta de dados existente."}
TOOLS = [
    {
        "name": "abrir_boas_vindas",
        "title": "Abrir boas-vindas do Posicionar Carreira",
        "description": "Abre a primeira configuração e mostra os fluxos do plugin. "
                       "Em um chat sem painel, use verificar_configuracao.",
        "inputSchema": EMPTY_INPUT,
        "_meta": {
            "ui": {"resourceUri": WELCOME_URI, "visibility": ["model"], "preferredModelDisplayMode": "inline"},
            "openai/ui": {"entrypoints": [{"type": "thread"}]},
        },
    },
    {
        "name": "abrir_painel",
        "title": "Abrir painel de vagas",
        "description": "Abre o painel de vagas no chat. Use listar_vagas se precisar da lista em texto.",
        "inputSchema": EMPTY_INPUT,
        "_meta": {
            "ui": {"resourceUri": UI_URI, "visibility": ["model"], "preferredModelDisplayMode": "inline"},
            "openai/ui": {"entrypoints": [{"type": "thread"}]},
        },
    },
    {
        "name": "abrir_dashboard",
        "title": "Dashboard",
        "description": "Abre a visão geral dos processos por status, agrupados em andamento e encerrados.",
        "inputSchema": EMPTY_INPUT,
        "_meta": {
            "ui": {"resourceUri": DASHBOARD_URI, "visibility": ["model"], "preferredModelDisplayMode": "inline"},
            "openai/ui": {"entrypoints": [{"type": "thread"}]},
        },
    },
    {
        "name": "lint",
        "title": "Conferir a base de vagas",
        "description": "Examina os dossiês, a triagem, as fontes e os links locais. Retorna erros e avisos com arquivo e sugestão de correção.",
        "inputSchema": EMPTY_INPUT,
    },
    {
        "name": "listar_vagas",
        "title": "Listar vagas",
        "description": "Retorna ID, empresa, cargo, status e as transições de status permitidas.",
        "inputSchema": EMPTY_INPUT,
    },
    {
        "name": "detalhar_vaga",
        "title": "Consultar processo",
        "description": "Retorna status, transições permitidas, histórico, materiais, próximo passo, "
                       "caminho oficial e titulo_chat da vaga pelo ID.",
        "inputSchema": {
            "type": "object",
            "properties": {"processo_id": {"type": "string", "minLength": 1}},
            "required": ["processo_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "verificar_configuracao",
        "title": "Verificar configuração de carreira",
        "description": "Verifica arquivos esperados e pendências por fluxo. Informe uma pasta absoluta para "
                       "inspecioná-la ou omita para usar a base configurada.",
        "inputSchema": {
            "type": "object", "properties": {"pasta": PASTA_ABSOLUTA}, "additionalProperties": False,
        },
    },
]
for tool in TOOLS:
    tool["annotations"] = {"readOnlyHint": True, "openWorldHint": False}

OPTIONAL_DATE = {"type": ["string", "null"], "format": "date"}
NULLABLE = {"type": ["string", "null"]}
EVENT_INPUT = {
    "processo_id": STRING, "revisao": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "descricao": STRING, "fonte": STRING, "data": OPTIONAL_DATE,
    "pendencia_triagem": {**STRING, "description": "Linha completa de monitoramento/triagem.md. "
                         "Ao confirmar a associação, registre o fato e encerre essa pendência."},
}
EDIT_INPUT = {
    "titulo": STRING,
    "status": {**STRING, "enum": list(TRANSICOES_STATUS)}, "prioridade": STRING,
    "proxima_acao": STRING, "responsavel": STRING, "prazo": OPTIONAL_DATE,
    "fonte_prazo": NULLABLE, "revisar_em": OPTIONAL_DATE, "encerrada_em": OPTIONAL_DATE,
    "candidatura_confirmada": {"type": "boolean"}, "candidatura_em": OPTIONAL_DATE,
    "fonte_candidatura": NULLABLE,
    "disponibilidade_inscricao": {**NULLABLE, "enum": [*sorted(DISPONIBILIDADES_INSCRICAO), None]},
    "fonte_disponibilidade_inscricao": NULLABLE,
}
for name, title, description, props, required in (
    (
        "criar_vaga", "Cadastrar vaga",
        "Cria o dossiê local com status identificada. Use a URL do anúncio ou uma fonte relativa à pasta carreira.",
        {"empresa": STRING, "titulo": STRING, "fonte": STRING, "processo_id": STRING,
         "fonte_compartilhada": {"type": "boolean", "description": "O original identifica várias vagas. "
                                "Reutilize sua URL ou caminho em cada dossiê."}},
        ["empresa", "titulo", "fonte"],
    ),
    (
        "registrar_evento", "Registrar evento",
        "Registra o fato comprovado para esta vaga. Use a revisão de detalhar_vaga e a fonte original. "
        "Se a fonte cobrir várias vagas, use o mesmo link em cada evento.",
        EVENT_INPUT, ["processo_id", "revisao", "descricao", "fonte"],
    ),
    (
        "atualizar_vaga", "Atualizar processo",
        "Atualiza os campos informados e registra um evento com fonte. Use a revisão de detalhar_vaga. "
        "Use mudancas.titulo para corrigir o título da vaga mantendo o mesmo ID. "
        "Para confirmar envio, informe candidatura_confirmada e fonte_candidatura. "
        "Para definir ou mudar disponibilidade_inscricao, informe fonte_disponibilidade_inscricao "
        "(URL ou arquivo relativo a carreira). Use disponibilidade_inscricao null para limpar os dois campos. "
        "Para alterar prazo, informe fonte_prazo. Para mudar o status, use uma das transições "
        "informadas em transicoes_status ao consultar a vaga.",
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
    "name": "inicializar_carreira",
    "title": "Preparar pasta de carreira",
    "description": "Cria oportunidades/ e somente os modelos solicitados que estiverem ausentes. "
                   "Use após a pessoa confirmar a pasta e os modelos. A configuração da base fica separada.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "pasta": PASTA_ABSOLUTA,
            "modelos": {"type": "array", "items": {"type": "string", "enum": list(MODELOS)}, "uniqueItems": True},
        },
        "required": ["pasta"],
        "additionalProperties": False,
    },
    "annotations": {"readOnlyHint": False, "destructiveHint": False,
                    "idempotentHint": True, "openWorldHint": False},
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
    processo, conteudo = ler_processo(root, processo_id)
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
    if name == "abrir_boas_vindas":
        return tool_result(message="Boas-vindas ao Posicionar Carreira. Para configurar por texto, use verificar_configuracao.")
    if name == "abrir_dashboard":
        return tool_result(message="Dashboard dos processos. Para obter o panorama por texto, use listar_vagas.")

    try:
        if name == "verificar_configuracao":
            return tool_result(verificar_configuracao(**arguments))
        if name == "inicializar_carreira":
            return tool_result(inicializar_carreira(**arguments))
        root = resolver_carreira_root()
        if name == "lint":
            resultado = lint(root)
            return tool_result(resultado, message=formatar_lint(resultado))
        if name == "listar_vagas":
            return tool_result({"vagas": listar(root), "transicoes_status": TRANSICOES_STATUS})
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
        return {"resources": [RESOURCE, WELCOME_RESOURCE, DASHBOARD_RESOURCE]}
    if method == "resources/templates/list":
        return {"resourceTemplates": []}
    if method == "resources/read":
        uri = params.get("uri")
        modos = {UI_URI: "vagas", WELCOME_URI: "boas-vindas", DASHBOARD_URI: "dashboard"}
        if not isinstance(uri, str) or uri not in modos:
            raise RpcError(-32002, "Recurso desconhecido.")
        html = UI_FILE.read_text(encoding="utf-8").replace('data-inicio="vagas"', f'data-inicio="{modos[uri]}"', 1)
        return {"contents": [{
            "uri": uri,
            "mimeType": UI_MIME,
            "text": html,
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
    if sys.argv[1:] in (["--carreira-root"], ["--papao-root"], ["--raiz"]):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            carreira = resolver_carreira_root()
            print(carreira if sys.argv[1] == "--carreira-root" else carreira.parent)
        except OSError as exc:
            raise SystemExit(str(exc)) from exc
        return
    for line in sys.stdin.buffer:
        response = respond(line)
        if response is not None:
            sys.stdout.buffer.write(json.dumps(response, ensure_ascii=False).encode("utf-8") + b"\n")
            sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
