"""Verificação e preparação opcional da pasta de dados de carreira."""
from pathlib import Path

from dados import resolver_carreira_root


MODELOS = {
    "perfil": ("perfil/perfil-profissional.md",
               "# Perfil profissional\n\n[preencher: experiências, formação e competências comprovadas]\n"),
    "preferencias": ("estrategia/referencias-candidaturas.md",
                     "# Objetivos e preferências\n\n[preencher: objetivos, funções e condições de trabalho]\n"),
    "curriculo": ("curriculos/base.md",
                  "# Currículo base\n\n[preencher: nome e trajetória que deseja apresentar]\n"),
    "portfolio": ("portfolio/README.md",
                  "# Portfólio\n\n[preencher: casos, contribuições e fontes que pode compartilhar]\n"),
}
PASTA_EVIDENCIAS = "perfil/evidencias"
PREFERENCIAS_LEGADAS = "estrategia/objetivos.md"
FLUXOS = {
    "gestao_de_vagas": ("oportunidades",),
    "perfil_e_objetivos": ("perfil", "preferencias"),
    "busca_e_monitoramento": ("oportunidades", "perfil", "preferencias"),
    "avaliacao": ("oportunidades", "perfil", "preferencias"),
    "candidatura": ("oportunidades", "perfil", "preferencias", "curriculo"),
    "portfolio": ("perfil", "portfolio"),
    "entrevistas": ("oportunidades", "perfil"),
}


def _pasta(pasta):
    if not isinstance(pasta, str) or not pasta.strip() or not Path(pasta).is_absolute():
        raise ValueError("Informe o caminho absoluto de uma pasta de dados existente.")
    return resolver_carreira_root(Path(pasta), exigir_oportunidades=False)


def _caminho_direto(raiz, relativo):
    caminho = raiz / relativo
    if caminho.resolve() != caminho:
        raise ValueError(f"Use um caminho direto dentro da pasta de dados para {relativo}.")
    return caminho


def _estado(raiz, relativo, *, pasta=False):
    try:
        caminho = _caminho_direto(raiz, relativo)
        if not caminho.exists():
            return "ausente"
        if pasta:
            return "disponivel" if caminho.is_dir() else "indisponivel"
        if not caminho.is_file():
            return "indisponivel"
        texto = caminho.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return "ausente"
    except (OSError, UnicodeError, ValueError):
        return "indisponivel"
    return "disponivel" if texto.strip() and "[preencher:" not in texto.casefold() else "rascunho"


def _caminho_modelo(raiz, nome):
    relativo = MODELOS[nome][0]
    if (raiz is not None and nome == "preferencias"
            and _estado(raiz, relativo) in {"ausente", "rascunho"}
            and _estado(raiz, PREFERENCIAS_LEGADAS) in {"disponivel", "rascunho"}):
        return PREFERENCIAS_LEGADAS
    return relativo


def _diagnostico(raiz):
    itens = {"oportunidades": "oportunidades", **{nome: _caminho_modelo(raiz, nome) for nome in MODELOS},
             "evidencias": PASTA_EVIDENCIAS}
    materiais = {
        nome: {"caminho": caminho,
               "estado": "nao_verificado" if raiz is None else
                         _estado(raiz, caminho, pasta=nome in {"oportunidades", "evidencias"})}
        for nome, caminho in itens.items()
    }
    materiais["evidencias"]["opcional"] = True
    if raiz is not None and materiais["portfolio"]["estado"] in {"ausente", "rascunho"}:
        try:
            candidatos = _caminho_direto(raiz, "portfolio").glob("*.md")
            tem_caso = any(path.name != "README.md" and
                           _estado(raiz, path.relative_to(raiz)) == "disponivel" for path in candidatos)
        except (ValueError, OSError):
            tem_caso = False
        if tem_caso:
            materiais["portfolio"] = {"caminho": "portfolio/", "estado": "disponivel"}
    fluxos = {
        fluxo: {"pendencias": [nome for nome in itens_necessarios if materiais[nome]["estado"] != "disponivel"]}
        for fluxo, itens_necessarios in FLUXOS.items()
    }
    for fluxo in fluxos.values():
        fluxo["estado"] = "fontes_pendentes" if fluxo["pendencias"] else "fontes_disponiveis"
    return {"pasta": str(raiz) if raiz is not None else None, "materiais": materiais, "fluxos": fluxos}


def verificar_configuracao(pasta=None):
    try:
        configurada = resolver_carreira_root(exigir_oportunidades=False)
    except (OSError, ValueError):
        configurada = None
    raiz = configurada if pasta is None else _pasta(pasta)
    resultado = _diagnostico(raiz)
    resultado["base_configurada"] = raiz is not None and raiz == configurada
    if raiz is None:
        resultado.update(estado="pasta_indisponivel",
                         proximo_passo="Escolha uma pasta existente e informe o caminho absoluto em pasta.")
    elif resultado["materiais"]["oportunidades"]["estado"] != "disponivel":
        resultado["proximo_passo"] = "Depois de confirmar a pasta, use inicializar_carreira."
    else:
        resultado["proximo_passo"] = (
            "Revise os materiais do fluxo escolhido. Configure CARREIRA_ROOT ou data-root.txt "
            "se esta pasta ainda não for a base configurada."
        )
    return resultado


def inicializar_carreira(pasta, modelos=()):
    raiz = _pasta(pasta)
    if (not isinstance(modelos, (list, tuple))
            or any(not isinstance(nome, str) or nome not in MODELOS for nome in modelos)
            or len(modelos) != len(set(modelos))):
        raise ValueError("Escolha modelos distintos entre perfil, preferencias, curriculo e portfolio.")

    oportunidades = _caminho_direto(raiz, "oportunidades")
    if oportunidades.exists() and not oportunidades.is_dir():
        raise ValueError("oportunidades precisa ser uma pasta.")
    caminhos = {nome: _caminho_modelo(raiz, nome) for nome in modelos}
    for relativo in caminhos.values():
        caminho = _caminho_direto(raiz, relativo)
        if (caminho.exists() and not caminho.is_file()) or (caminho.parent.exists() and not caminho.parent.is_dir()):
            raise ValueError(f"Confira o caminho para {relativo}.")

    criados = []
    try:
        oportunidades.mkdir()
        criados.append("oportunidades/")
    except FileExistsError:
        if not _caminho_direto(raiz, "oportunidades").is_dir():
            raise
    for nome, relativo in caminhos.items():
        texto = MODELOS[nome][1]
        caminho = _caminho_direto(raiz, relativo)
        caminho.parent.mkdir(exist_ok=True)
        try:
            with _caminho_direto(raiz, relativo).open("x", encoding="utf-8", newline="\n") as arquivo:
                arquivo.write(texto)
        except FileExistsError:
            if not _caminho_direto(raiz, relativo).is_file():
                raise
        else:
            criados.append(relativo)

    return {
        **verificar_configuracao(str(raiz)),
        "criados": criados,
        "proximo_passo": (
            "Configure CARREIRA_ROOT ou data-root.txt para usar esta base e preencha os rascunhos "
            "necessários ao fluxo escolhido, usando fatos e fontes próprias."
        ),
    }
