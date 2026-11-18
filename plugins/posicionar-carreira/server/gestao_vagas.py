"""Valida os registros oficiais e gera painel/relatório. Sem rede ou envio externo."""
from __future__ import annotations
import argparse
import datetime as dt
import json
from hashlib import sha256
from pathlib import Path
import re
from urllib.parse import unquote

from dados import _ordem_painel, resolver_carreira_root, responsavel_pessoal
from diagnosticos import avisos_contexto, destino_fonte, falhar, formatar_lint
import triagem

TRANSICOES_STATUS = {
    'identificada': ['candidatura-enviada', 'descartada', 'cancelada-pela-empresa'],
    'candidatura-enviada': ['entrevistas', 'oferta', 'contratado', 'reprovado', 'cancelada-pela-empresa'],
    'entrevistas': ['oferta', 'contratado', 'reprovado', 'cancelada-pela-empresa'],
    'oferta': ['contratado', 'reprovado', 'cancelada-pela-empresa'],
    'descartada': [],
    'cancelada-pela-empresa': [],
    'reprovado': [],
    'contratado': [],
}
STATUS_APOS_ENVIO = {'candidatura-enviada', 'entrevistas', 'oferta'}
DISPONIBILIDADES_INSCRICAO = {'aberta_verificada', 'nao_confirmada', 'anuncio_expirado'}
CAMPOS_FONTE = ('fonte_estado', 'fonte_candidatura', 'fonte_prazo', 'fonte_disponibilidade_inscricao')
LINK = re.compile(r'\]\((<[^>]+>|[^)]+)\)')


def metadata(path, *, text=None):
    import yaml

    if text is None:
        text = path.read_text(encoding='utf-8')
    else:
        text = text.replace('\r\n', '\n').replace('\r', '\n')
    if not text.startswith('---\n') or '\n---\n' not in text[4:]:
        raise ValueError(f'{path}: metadados YAML ausentes')
    data = yaml.safe_load(text.split('---\n', 2)[1])
    if not isinstance(data, dict):
        raise ValueError(f'{path}: metadados devem ser um mapa')
    return data

def date(value, field):
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError(f'{field}: data deve ser AAAA-MM-DD ou null')
    return dt.date.fromisoformat(value)

def check_source(root, value, *, exigir_arquivo=True):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Fonte de evidência ausente')
    if value.startswith(('https://', 'http://')):
        return
    target = destino_fonte(root.resolve(), value)
    if target is None or (exigir_arquivo and not target.is_file()):
        raise ValueError(f'Fonte local inexistente ou fora de carreira: {value}')


def arquivo_original(root, fonte):
    arquivo = destino_fonte(root.resolve(), fonte)
    if not isinstance(arquivo, Path):
        return None
    partes = arquivo.relative_to(root.resolve()).parts
    if len(partes) >= 5 and partes[0] == 'oportunidades' and partes[3] == 'envios':
        return None
    return arquivo


def validar_originais(root, registros, novas=(), processo_id=None, *, erro=falhar):
    por_arquivo = {}
    for registro in registros:
        eventos = registro.get('eventos')
        fontes = [e.get('fonte') for e in eventos if isinstance(e, dict)] if isinstance(eventos, list) else []
        fontes.extend(registro.get(campo) for campo in CAMPOS_FONTE)
        for fonte in sorted({s for s in fontes if isinstance(s, str) and s.strip()}):
            arquivo = arquivo_original(root, fonte)
            if arquivo:
                dossie = registro['_path'].parent.relative_to(root / 'oportunidades').as_posix()
                por_arquivo.setdefault(arquivo, set()).add(dossie)
    for arquivo in novas:
        por_arquivo.setdefault(arquivo, set()).add(processo_id)
    por_tamanho = {}
    tamanhos_novos = {p.stat().st_size for p in novas}
    for arquivo, ids in por_arquivo.items():
        try:
            if arquivo.is_file():
                tamanho = arquivo.stat().st_size
                if not novas or tamanho in tamanhos_novos:
                    por_tamanho.setdefault(tamanho, []).append((arquivo, ids))
        except OSError as exc:
            erro(arquivo, str(exc), 'Confira o acesso ao original.')
    for grupo in por_tamanho.values():
        if len(grupo) < 2:
            continue
        por_hash = {}
        for arquivo, ids in grupo:
            digest = sha256()
            try:
                with arquivo.open('rb') as stream:
                    for bloco in iter(lambda: stream.read(1024 * 1024), b''):
                        digest.update(bloco)
            except OSError as exc:
                erro(arquivo, str(exc), 'Confira o acesso ao original.')
                continue
            por_hash.setdefault(digest.digest(), []).append((arquivo, ids))
        for iguais in por_hash.values():
            if len(iguais) < 2 or (novas and not any(p in novas for p, _ in iguais)):
                continue
            if len(set.union(*(ids for _, ids in iguais))) > 1:
                caminhos = ', '.join(sorted(p.relative_to(root.resolve()).as_posix() for p, _ in iguais))
                erro(iguais[0][0], f'Fonte repetida entre vagas: {caminhos}',
                     'Vincule cada fato ao mesmo original.')

def process_path(root, processo_id):
    if (
        not isinstance(processo_id, str)
        or any(char in processo_id for char in ('\\', ':', '\x00'))
        or len(parts := processo_id.split('/')) != 2
        or any(part in ('', '.', '..') for part in parts)
    ):
        raise ValueError('Processo não encontrado. Selecione um ID da lista de vagas.')
    path = root.resolve() / 'oportunidades' / parts[0] / parts[1] / 'processo.md'
    if path.resolve() != path:
        raise ValueError('Processo não encontrado. Selecione um ID da lista de vagas.')
    return path


def validate_process(root, path, d, *, exigir_arquivos=False, erro=falhar):
    def problema(texto, sugestao):
        erro(path, texto, sugestao)

    if d.keys() & {'estado', 'etapa', 'resultado'}:
        problema('Campos de status antigos no YAML', 'Migre o cabeçalho para um único campo status.')
    for key in ('id', 'empresa', 'titulo', 'status', 'prioridade', 'proxima_acao', 'responsavel', 'fonte_estado'):
        if not isinstance(d.get(key), str) or not d[key].strip():
            problema(f'Campo obrigatório {key}', f'Preencha {key} no cabeçalho YAML.')
    expected = path.parent.relative_to(root / 'oportunidades').as_posix()
    if d.get('id') != expected:
        problema(f'ID não corresponde à pasta: {d.get("id")}', f'Confira o ID oficial {expected}.')
    status = d.get('status')
    if not isinstance(status, str) or status not in TRANSICOES_STATUS:
        problema('status inválido', 'Use um dos status oficiais: ' + ', '.join(TRANSICOES_STATUS) + '.')
    elif TRANSICOES_STATUS[status] and d.get('encerrada_em') is not None:
        problema('Processo em andamento com data de encerramento', 'Confira o status e a data de encerramento.')
    if d.get('prioridade') not in ('alta', 'media', 'baixa'):
        problema('Prioridade inválida', 'Use alta, media ou baixa.')
    if d.get('responsavel') not in ('titular', 'candidato', 'assistente', 'empresa'):
        try:
            titular = responsavel_pessoal(root)
        except (OSError, ValueError) as exc:
            erro(root / 'config.json', str(exc), 'Confira o responsável na configuração da base.')
        else:
            if d.get('responsavel') != titular:
                problema('responsável inválido', 'Informe quem deve executar a próxima ação.')
    if not isinstance(d.get('candidatura_confirmada'), bool):
        problema('candidatura_confirmada deve ser booleano', 'Informe true ou false conforme a evidência.')

    def conferir_data(valor, campo):
        try:
            return date(valor, campo)
        except ValueError:
            problema(f'{campo}: data inválida', 'Use uma data existente em AAAA-MM-DD entre aspas, ou null.')

    datas = {campo: conferir_data(d.get(campo), campo) for campo in
             ('identificada_em', 'candidatura_em', 'atualizado_em', 'encerrada_em', 'prazo', 'revisar_em')}
    if not d.get('atualizado_em'):
        problema('Data de atualização ausente', 'Informe atualizado_em.')

    def conferir_fonte(valor, campo):
        try:
            check_source(root, valor, exigir_arquivo=exigir_arquivos)
        except (ValueError, OSError) as exc:
            problema(f'{campo}: {exc}', 'Informe a URL original ou o caminho do arquivo relativo à base.')

    conferir_fonte(d.get('fonte_estado'), 'fonte_estado')
    if d.get('disponibilidade_inscricao'):
        if d['disponibilidade_inscricao'] not in tuple(DISPONIBILIDADES_INSCRICAO):
            problema('Disponibilidade de inscrição inválida', 'Confira a disponibilidade no anúncio.')
        conferir_fonte(d.get('fonte_disponibilidade_inscricao'), 'fonte_disponibilidade_inscricao')
    if d.get('candidatura_confirmada') is True:
        conferir_fonte(d.get('fonte_candidatura'), 'fonte_candidatura')
    elif isinstance(status, str) and status in STATUS_APOS_ENVIO:
        problema('Status exige candidatura confirmada', 'Confira o comprovante de envio e o status.')
    elif d.get('candidatura_em') or d.get('fonte_candidatura'):
        problema('Data/fonte de envio sem confirmação', 'Confira a confirmação do envio.')
    if d.get('prazo'):
        conferir_fonte(d.get('fonte_prazo'), 'fonte_prazo')
    for campo in ('identificada_em', 'candidatura_em', 'encerrada_em'):
        if datas[campo] and datas['atualizado_em'] and datas[campo] > datas['atualizado_em']:
            problema(f'{campo} posterior à atualização', 'Confira as datas do fato e da atualização.')
    if datas['candidatura_em'] and datas['encerrada_em'] and datas['encerrada_em'] < datas['candidatura_em']:
        problema('Encerramento anterior ao envio', 'Confira as datas de candidatura e encerramento.')
    aliases = d.get('ids_externos', [])
    if not isinstance(aliases, list) or any(not isinstance(alias, str) for alias in aliases):
        problema('ids_externos inválidos', 'Use uma lista de identificadores externos.')
    events = d.get('eventos')
    if not isinstance(events, list) or not events:
        problema('Histórico de eventos ausente', 'Registre os fatos com data, descrição e fonte.')
        return
    for indice, event in enumerate(events, 1):
        if not isinstance(event, dict):
            problema(f'Evento {indice} inválido', 'Use um registro com data, descrição e fonte.')
            continue
        conferir_data(event.get('data'), f'Evento {indice}, data')
        conferir_data(event.get('registrado_em'), f'Evento {indice}, registrado_em')
        if not event.get('registrado_em') or not isinstance(event.get('descricao'), str) or not event['descricao'].strip():
            problema(f'Evento {indice} incompleto', 'Preencha registrado_em e descreva o fato.')
        conferir_fonte(event.get('fonte'), f'Evento {indice}, fonte')


def _load_process(root, path, d, *, exigir_arquivos=False, erro=falhar):
    validate_process(root, path, d, exigir_arquivos=exigir_arquivos, erro=erro)
    d['_path'] = path
    d['_score'] = None
    scorefile = path.parent / 'avaliacao-validada.json'
    if scorefile.exists():
        try:
            score = json.loads(scorefile.read_text(encoding='utf-8'))
            if not isinstance(score, dict):
                raise ValueError('Avaliação inválida')
            if score.get('status') == 'scored':
                if not isinstance(score.get('final_score'), (float, int)) or not 0 <= score['final_score'] <= 10:
                    raise ValueError('score inválido')
                d['_score'] = score['final_score']
        except (OSError, ValueError) as exc:
            erro(scorefile, str(exc), 'Confira o JSON e a nota da avaliação.')
    return d


def load_process(root, processo_id, *, text=None):
    root = root.resolve()
    path = process_path(root, processo_id)
    if not path.is_file():
        raise ValueError('Processo não encontrado. Selecione um ID da lista de vagas.')
    return _load_process(root, path, metadata(path, text=text))


def load_processes(root, *, exigir_arquivos=False, erro=falhar, caminhos=None):
    import yaml

    records, ids, aliases = [], {}, {}
    if caminhos is None:
        caminhos = sorted((root / 'oportunidades').glob('*/*/processo.md'))
    for path in caminhos:
        try:
            d = metadata(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            erro(path, str(exc), 'Confira a leitura do arquivo e o cabeçalho YAML.')
            continue
        processo_id = d.get('id')
        if isinstance(processo_id, str):
            if processo_id in ids:
                erro(path, f'ID duplicado: {processo_id}', f'Confira o ID também em {ids[processo_id]}.')
            ids.setdefault(processo_id, path.relative_to(root))
        registro = _load_process(root, path, d, exigir_arquivos=exigir_arquivos, erro=erro)
        records.append(registro)
        externos = d.get('ids_externos')
        if isinstance(externos, list):
            for alias in externos:
                if isinstance(alias, str):
                    if alias in aliases:
                        erro(path, f'ID externo duplicado: {alias}', f'Confira o ID também em {aliases[alias]}.')
                    aliases.setdefault(alias, path.relative_to(root))
    return records


def validate_links(root, pending=(), *, erro=falhar):
    paths = [root/'README.md', root/'AGENTS.md', root/'painel-vagas.md']
    for folder in ('oportunidades', 'empresas', 'monitoramento', 'estrategia'):
        paths.extend(sorted((root/folder).rglob('*.md')))
    paths.extend(sorted((root/'relatorios').glob('*/acompanhamento-gerado-*.md')))
    for path in paths:
        if not path.exists() or (root/'monitoramento/entradas') in path.parents:
            continue
        try:
            content = re.sub(r'```.*?```', '', path.read_text(encoding='utf-8'), flags=re.S)
        except (OSError, UnicodeError) as exc:
            erro(path, str(exc), 'Confira a leitura do arquivo Markdown em UTF-8.')
            continue
        for link in LINK.findall(content):
            target = link.strip('<>')
            if re.match(r'^[a-zA-Z][\w+.-]*:', target) or target.startswith('#'):
                continue
            filepart = unquote(target.split('#', 1)[0])
            if not filepart:
                continue
            try:
                valido = (path.parent/filepart).resolve() in pending or (path.parent/filepart).exists()
            except (OSError, ValueError, RuntimeError):
                valido = False
            if not valido:
                erro(path, f'Link quebrado: {target}', 'Atualize o destino ou restaure o arquivo citado.')


def lint(root):
    root = root.resolve()
    oportunidades = root / 'oportunidades'
    caminhos = sorted(oportunidades.glob('*/*/processo.md'))
    resultado = {'dossies': len(caminhos), 'erros': [], 'avisos': []}

    def erro(arquivo, problema, sugestao):
        resultado['erros'].append(dict(arquivo=str(arquivo), problema=problema, sugestao=sugestao))

    def aviso(arquivo, problema, sugestao):
        resultado['avisos'].append(dict(arquivo=str(arquivo), problema=problema, sugestao=sugestao))

    if not oportunidades.is_dir():
        erro(oportunidades, 'Pasta de oportunidades ausente', 'Confira a pasta de dados configurada.')
        return resultado
    registros = load_processes(root, exigir_arquivos=True, erro=erro, caminhos=caminhos)
    sem_leitura = set(caminhos) - {r['_path'] for r in registros}
    triagem.validar(root, registros, erro=erro, sem_leitura={
        p.parent.relative_to(oportunidades).as_posix() for p in sem_leitura})
    validar_originais(root, registros, erro=erro)
    validate_links(root, erro=erro)
    avisos_contexto(root, registros, TRANSICOES_STATUS, aviso)
    return resultado


def clean(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')

def process_link(root, d, prefix=''):
    return f'[{clean(d["empresa"])} — {clean(d["titulo"])}](<{prefix}{d["_path"].relative_to(root).as_posix()}>)'

def sections(root, records):
    import yaml

    lines = []
    for d in records:
        appraisal = d['_path'].parent/'avaliacao.md'
        label = f'{d["_score"]:.1f}/10' if d['_score'] is not None else 'sem score'
        ev = f'[{label} + cultura](<{appraisal.relative_to(root).as_posix()}>)' if appraisal.exists() else 'Ainda não avaliada'
        due = f'Prazo: {d["prazo"]}' if d.get('prazo') else 'Sem prazo informado'
        if d.get('revisar_em'):
            due += f'; revisão sugerida: {d["revisar_em"]}'
        action = d['proxima_acao']
        if d.get('proxima_acao_plano') and d['proxima_acao_plano'] != action:
            action += ' Plano atual: '+d['proxima_acao_plano']
        title = f'{d["empresa"]} — {d["titulo"]}'.replace('\n', ' ')
        path = d['_path'].relative_to(root).as_posix()
        lines.extend([f'### {title}', '', f'- **Processo:** [Abrir processo](<{path}>)',
                      f'- **Status:** {d["status"]}', f'- **Prioridade:** {d["prioridade"]}',
                      f'- **Próxima ação:** {action}', f'- **Responsável:** {d["responsavel"]}',
                      f'- **Prazo / revisão:** {due}', f'- **Avaliação:** {ev}'])
        if TRANSICOES_STATUS[d['status']]:
            benchmark = d['_path'].parent/'benchmark-salarial.md'
            if benchmark.is_file():
                try:
                    resumo = metadata(benchmark).get('resumo')
                except (ValueError, yaml.YAMLError):
                    resumo = None
                detalhe = f'{clean(resumo.strip())} — ' if isinstance(resumo, str) and resumo.strip() else ''
                lines.append(f'- **Benchmark salarial:** {detalhe}[fontes e limites](<{benchmark.relative_to(root).as_posix()}>)')
            else:
                lines.append('- **Benchmark salarial:** Pesquisa pendente.')
        availability = d.get('disponibilidade_inscricao')
        if availability:
            labels = {'aberta_verificada':'aberta verificada', 'nao_confirmada':'não confirmada', 'anuncio_expirado':'anúncio expirado'}
            lines.append(f'- **Disponibilidade da inscrição:** {labels[availability]}')
        plan = d.get('grupo_plano_atual')
        if plan in {'plano_modalidade_compativel', 'plano_esclarecimento'} and d['status']=='identificada' and not d['candidatura_confirmada']:
            lines.append('- **Plano atual:** '+('modalidade compatível' if plan=='plano_modalidade_compativel' else 'esclarecer antes de candidatar'))
        lines.append('')
    return '\n'.join(lines) if records else 'Nenhum registro nesta categoria.'

def panel(root, records, today):
    ordem = {processo_id: i for i, processo_id in enumerate(dict.fromkeys(_ordem_painel(root)))}
    records = sorted(records, key=lambda d: (ordem.get(d['id'], len(ordem)),
        {'alta':0,'media':1,'baixa':2}[d['prioridade']], d['empresa'], d['titulo']))
    guide = '../plugins/posicionar-carreira/README.md'
    help_text = (f'[Como manter]({guide}#gestão-de-oportunidades)' if (root/guide).is_file()
                 else 'Como manter: consulte Gestão de oportunidades no guia do Posicionar Carreira.')
    links = [f'[{label}]({target})' for label, target in (
        ('Preferências e pretensão', 'estrategia/referencias-candidaturas.md'),
        ('Triagem de mensagens', 'monitoramento/triagem.md'),
    ) if (root/target).is_file()]
    lines = ['# Painel geral de vagas', '', f'Gerado em {today.isoformat()}. **Status e próxima ação oficiais:** consulte o processo de cada vaga e use as operações do Posicionar Carreira para atualizá-lo.', '',
             f'{len(records)} oportunidades registradas; {sum(d["candidatura_confirmada"] for d in records)} candidaturas confirmadas no histórico (inclusive encerradas e sem data conhecida). Pistas e recibos sem cargo não contam como envios.', '',
             ' · '.join([*links, help_text]), '',
             'Scores preservados das avaliações validadas. Cultura e condições devem ser lidas com a avaliação; as datas de pesquisa constam dos dossiês.', '']
    for source in sorted({d['fonte_disponibilidade_inscricao'] for d in records if d.get('disponibilidade_inscricao')}):
        lines += [f'[Auditoria completa de disponibilidade](<{source}>): situação das inscrições e pistas sem processo.', '']
    current = [d for d in records if d['status']=='identificada' and not d['candidatura_confirmada'] and d.get('grupo_plano_atual') in {'plano_modalidade_compativel', 'plano_esclarecimento'}]
    if current:
        lines += [f'{len(current)} famílias no plano atual: {sum(d["grupo_plano_atual"]=="plano_modalidade_compativel" for d in current)} candidaturas a avaliar e {sum(d["grupo_plano_atual"]=="plano_esclarecimento" for d in current)} a esclarecer antes de candidatar. Candidatura pública disponível não garante formulário autenticado ou submissão. Scores anteriores permanecem históricos, sem recálculo.', '']
        sources = {d['fonte_plano'] for d in current if isinstance(d.get('fonte_plano'), str)}
        for source in sorted(sources):
            try:
                check_source(root, source)
            except ValueError:
                continue
            lines += [f'[Fonte do plano atual](<{source}>)', '']
    if (root/'monitoramento/triagem.md').is_file():
        lines += ['[Triagem — recibos, duplicações e lacunas](monitoramento/triagem.md).','']
    for p in sorted((root/'empresas').glob('*/empresa.md')):
        if 'interesse_sem_vaga: true' in p.read_text(encoding='utf-8'):
            title = re.search(r'^# (.+)$', p.read_text(encoding='utf-8'), re.M)
            name = title.group(1) if title else p.parent.name
            lines.append(f'- [{name}](<{p.relative_to(root).as_posix()}>) — interesse sem vaga identificada.')
    active = [d for d in records if TRANSICOES_STATUS[d['status']]]
    finished = [d for d in records if not TRANSICOES_STATUS[d['status']]]
    lines += ['', '## Em andamento', '', sections(root, active),
              '', '## Encerradas', '', sections(root, finished)]
    existing = root/'painel-vagas.md'
    if existing.exists():
        previous = existing.read_text(encoding='utf-8')
        reviews = re.search(r'\n## Revis(?:ões|ão) recebidas? —', previous)
        if reviews:
            lines.append(previous[reviews.start():].rstrip())
    return '\n'.join(lines)+'\n'

def monthly(root, records, month, today):
    if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])',month):
        raise ValueError('Mês deve ser AAAA-MM')
    if month > today.isoformat()[:7]:
        raise ValueError('Não gerar fechamento para mês futuro')
    def in_month(d): return isinstance(d,str) and d.startswith(month+'-')
    lines = [f'# Acompanhamento de {month}', '', f'Fotografia gerada em {today.isoformat()}; dados conhecidos nesta data. Não é reconstrução garantida do conhecimento disponível no passado.', '']
    if (root/'painel-vagas.md').is_file():
        lines += ['[Painel atual](../../painel-vagas.md)', '']
    for title, filtered in [
        ('Vagas identificadas no mês',[d for d in records if in_month(d.get('identificada_em'))]),
        ('Candidaturas confirmadas enviadas no mês',[d for d in records if d['candidatura_confirmada'] and in_month(d.get('candidatura_em'))])]:
        lines += [f'## {title} ({len(filtered)})','']
        lines += [f'- {process_link(root,d,"../../")}' for d in filtered] or ['Nenhum registro com data confirmada.']
        lines.append('')
    lines += ['## Eventos ocorridos no mês','']
    for d in records:
        for event in d['eventos']:
            if in_month(event.get('data')):
                change = (event.get('alteracoes') or {}).get('status')
                status = f' ({change["anterior"]} → {change["atual"]})' if change else ''
                lines.append(f'- {event["data"]} — {process_link(root,d,"../../")}: {event["descricao"]}{status}')
    unknown = [d for d in records if d['candidatura_confirmada'] and not d.get('candidatura_em')]
    lines += ['', '## Limites de contagem','',f'{len(unknown)} candidatura(s) confirmada(s) sem data de envio conhecida; excluídas da contagem mensal. Eventos sem data também não são atribuídos ao mês de importação. Recibos sem cargo e pistas não contam como candidaturas.','']
    return '\n'.join(lines)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('acao',choices=['lint','gerar','relatorio'])
    parser.add_argument('--root',type=Path,help='Diretório de dados de carreira; usa CARREIRA_ROOT ou a configuração local quando omitido.')
    parser.add_argument('--mes')
    parser.add_argument('--data',default=dt.date.today().isoformat(),help='Data de referência, AAAA-MM-DD')
    args=parser.parse_args()
    today=date(args.data,'data')
    root=resolver_carreira_root() if args.root is None else args.root.expanduser().resolve()
    if args.acao == 'lint':
        resultado = lint(root)
        print(formatar_lint(resultado))
        raise SystemExit(1 if resultado['erros'] else 0)
    records=load_processes(root, exigir_arquivos=True)
    validar_originais(root, records)
    triagem.validar(root, records)
    if not records:
        raise ValueError('Nenhum processo encontrado; painel não será substituído')
    pending = {(root/'painel-vagas.md').resolve()} if args.acao=='gerar' else set()
    validate_links(root, pending=pending)
    if args.acao=='gerar':
        output=root/'painel-vagas.md'
        temp=output.with_suffix('.md.tmp')
        temp.write_text(panel(root,records,today),encoding='utf-8'); temp.replace(output)
    elif args.acao=='relatorio':
        if not args.mes: parser.error('--mes obrigatório para relatorio')
        text=monthly(root,records,args.mes,today)
        folder=root/'relatorios'/args.mes; folder.mkdir(parents=True,exist_ok=True)
        output=folder/f'acompanhamento-gerado-{today.isoformat()}.md'
        version=2
        while output.exists():
            output=folder/f'acompanhamento-gerado-{today.isoformat()}-r{version}.md'; version+=1
        with output.open('x',encoding='utf-8') as f: f.write(text)
        print(output)
    validate_links(root)
    print(f'{len(records)} processos validados; ação {args.acao} concluída.')

if __name__=='__main__':
    import yaml

    try: main()
    except (ValueError, OSError, yaml.YAMLError) as e:
        raise SystemExit(str(e))
