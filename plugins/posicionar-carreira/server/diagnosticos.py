import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote


def falhar(arquivo, problema, sugestao):
    raise ValueError(f'{arquivo}: {problema}. {sugestao}')


def destino_fonte(root, fonte):
    if not isinstance(fonte, str) or not fonte.strip():
        return None
    alvo = fonte.split('#', 1)[0]
    if alvo.startswith(('http://', 'https://')):
        return alvo
    try:
        caminho = (root / unquote(alvo)).resolve()
    except (ValueError, OSError, RuntimeError):
        return None
    return caminho if caminho.is_relative_to(root) else None


def anuncio_arquivado(root, processo, fonte):
    anuncio = processo.parent / 'vaga.md'
    arquivo = root / 'archive'
    if not anuncio.is_file():
        anterior = arquivo / anuncio.relative_to(root)
        if anterior.is_file():
            return anterior
        original = destino_fonte(root, fonte)
        if isinstance(original, Path) and original.is_relative_to(arquivo) and re.search(
                r'\b(vaga|an[uú]ncio|job[- ]description)\b', original.stem.replace('_', ' '), re.I):
            return original
        return None
    try:
        linhas = anuncio.read_text(encoding='utf-8-sig').splitlines()
    except (OSError, UnicodeError):
        return None
    destino = None
    for linha in linhas:
        if not linha.strip() or linha.lstrip().startswith('#'):
            continue
        link = re.fullmatch(r'\s*[-*]?\s*\[([^\]]*)\]\((<[^>]+>|[^)]+)\)\s*', linha)
        if not link:
            return None
        alvo = link[2].strip('<>')
        if re.match(r'^[a-zA-Z][\w+.-]*:', alvo):
            return None
        original = destino_fonte(root, (anuncio.parent.relative_to(root) / alvo).as_posix())
        if not isinstance(original, Path) or not original.is_relative_to(arquivo) or not re.search(
                r'an[uú]ncio|vaga|descrição', link[1], re.I):
            return None
        destino = original
    return destino


def avisos_contexto(root, registros, transicoes, avisar):
    por_fonte = defaultdict(list)
    for registro in registros:
        processo = registro['_path']
        eventos = registro.get('eventos')
        if not isinstance(eventos, list) or not eventos:
            continue
        for evento in eventos:
            if not isinstance(evento, dict) or not isinstance(evento.get('descricao'), str):
                continue
            fonte = destino_fonte(root, evento.get('fonte'))
            if fonte is not None:
                por_fonte[fonte].append((processo, evento['descricao']))
        status = registro.get('status')
        if not isinstance(status, str) or not transicoes.get(status):
            continue
        fonte = eventos[0].get('fonte') if isinstance(eventos[0], dict) else None
        original = anuncio_arquivado(root, processo, fonte)
        if original is not None:
            avisar(processo, f'Anúncio de vaga em andamento localizado em {original.relative_to(root).as_posix()}',
                   'Confira o anúncio atual e registre-o em vaga.md com o link para o original.')

    for fonte, eventos in por_fonte.items():
        if len({processo for processo, _ in eventos}) < 2:
            continue
        for processo, descricao in eventos:
            if re.fullmatch(r'(?:e-?mail|mensagem|retorno|contato) (?:recebid[oa]|registrad[oa])|'
                            r'recebid[oa] (?:e-?mail|mensagem|retorno|contato)|oportunidade cadastrada',
                            descricao.strip(' .').casefold()):
                avisar(processo, f'Fonte compartilhada com descrição genérica «{descricao}» ({fonte})',
                       'Especifique o que a fonte comprova para esta vaga.')


def formatar_lint(resultado):
    linhas = [f"Dossiês examinados: {resultado['dossies']}. Erros: {len(resultado['erros'])}. "
              f"Avisos: {len(resultado['avisos'])}."]
    for chave, tipo in [('erros', 'Erro'), ('avisos', 'Aviso')]:
        for item in resultado[chave]:
            linhas.append(f"{tipo} | {item['arquivo']} | {item['problema']} | {item['sugestao']}")
    return '\n'.join(linhas)
