"""Valida os registros oficiais e gera painel/relatório. Sem rede ou envio externo."""
from __future__ import annotations
import argparse
import datetime as dt
import json
from pathlib import Path
import re
from urllib.parse import unquote
import yaml

ESTADOS = {'aberto', 'pausado', 'encerrado'}
ETAPAS = {'identificada', 'em_avaliacao', 'em_preparacao', 'candidatura_enviada',
          'triagem', 'entrevista_tecnica', 'entrevista_gestao', 'oferta'}
RESULTADOS = {'contratado', 'reprovado', 'desistencia', 'vaga_cancelada', 'descartado_na_avaliacao'}
LINK = re.compile(r'\]\((<[^>]+>|[^)]+)\)')

def metadata(path, *, text=None):
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

def check_source(root, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Fonte de evidência ausente')
    if value.startswith(('https://', 'http://')):
        return
    target = (root / unquote(value.split('#', 1)[0])).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        raise ValueError(f'Fonte local inexistente ou fora de carreira: {value}')

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


def validate_process(root, path, d):
    for key in ('id', 'empresa', 'titulo', 'estado', 'etapa', 'prioridade',
                'proxima_acao', 'responsavel', 'fonte_estado'):
        if not isinstance(d.get(key), str) or not d[key].strip():
            raise ValueError(f'{path}: campo obrigatório {key}')
    expected = path.parent.relative_to(root / 'oportunidades').as_posix()
    if d['id'] != expected:
        raise ValueError(f'ID não corresponde à pasta: {d["id"]} / {expected}')
    if d['estado'] not in ESTADOS or d['etapa'] not in ETAPAS:
        raise ValueError(f'{path}: estado/etapa inválido')
    if d['prioridade'] not in {'alta', 'media', 'baixa'}:
        raise ValueError(f'{path}: prioridade inválida')
    if d['responsavel'] not in {'candidato', 'assistente', 'empresa'}:
        raise ValueError(f'{path}: responsável inválido')
    if d['estado'] == 'encerrado':
        if d.get('resultado') not in RESULTADOS:
            raise ValueError(f'{path}: encerramento sem resultado válido')
    elif d.get('resultado') is not None or d.get('encerrada_em') is not None:
        raise ValueError(f'{path}: processo não encerrado com resultado/data final')
    if not isinstance(d.get('candidatura_confirmada'), bool):
        raise ValueError(f'{path}: candidatura_confirmada deve ser booleano')
    for field in ('identificada_em', 'candidatura_em', 'atualizado_em', 'encerrada_em', 'prazo', 'revisar_em'):
        date(d.get(field), field)
    if not d.get('atualizado_em'):
        raise ValueError(f'{path}: atualização ausente')
    check_source(root, d['fonte_estado'])
    if d.get('disponibilidade_inscricao'):
        if d['disponibilidade_inscricao'] not in {'aberta_verificada', 'nao_confirmada', 'anuncio_expirado'}:
            raise ValueError(f'{path}: disponibilidade de inscrição inválida')
        check_source(root, d.get('fonte_disponibilidade_inscricao'))
    if d['candidatura_confirmada']:
        check_source(root, d.get('fonte_candidatura'))
    elif d.get('candidatura_em') or d.get('fonte_candidatura'):
        raise ValueError(f'{path}: data/fonte de envio sem confirmação')
    if d.get('prazo'):
        check_source(root, d.get('fonte_prazo'))
    for field in ('identificada_em', 'candidatura_em', 'encerrada_em'):
        if d.get(field) and d[field] > d['atualizado_em']:
            raise ValueError(f'{path}: {field} posterior à atualização')
    if d.get('candidatura_em') and d.get('encerrada_em') and d['encerrada_em'] < d['candidatura_em']:
        raise ValueError(f'{path}: encerramento anterior ao envio')
    events = d.get('eventos')
    if not isinstance(events, list) or not events:
        raise ValueError(f'{path}: histórico de eventos ausente')
    for event in events:
        date(event.get('data'), 'evento.data')
        date(event.get('registrado_em'), 'evento.registrado_em')
        if not event.get('registrado_em') or not event.get('descricao'):
            raise ValueError(f'{path}: evento incompleto')
        check_source(root, event.get('fonte'))


def _load_process(root, path, d):
    validate_process(root, path, d)
    d['_path'] = path
    d['_score'] = None
    scorefile = path.parent / 'avaliacao-validada.json'
    if scorefile.exists():
        score = json.loads(scorefile.read_text(encoding='utf-8'))
        if score.get('status') == 'scored':
            if not isinstance(score.get('final_score'), (float, int)) or not 0 <= score['final_score'] <= 10:
                raise ValueError(f'{scorefile}: score inválido')
            d['_score'] = score['final_score']
    return d


def load_process(root, processo_id, *, text=None):
    root = root.resolve()
    path = process_path(root, processo_id)
    if not path.is_file():
        raise ValueError('Processo não encontrado. Selecione um ID da lista de vagas.')
    return _load_process(root, path, metadata(path, text=text))


def load_processes(root):
    records, ids, aliases = [], set(), set()
    for path in sorted((root / 'oportunidades').glob('*/*/processo.md')):
        d = metadata(path)
        processo_id = d.get('id')
        if isinstance(processo_id, str) and processo_id in ids:
            raise ValueError(f'ID duplicado: {processo_id}')
        records.append(_load_process(root, path, d))
        ids.add(processo_id)
        for alias in d.get('ids_externos', []):
            if alias in aliases:
                raise ValueError(f'ID externo duplicado: {alias}')
            aliases.add(alias)
    return records


def validate_links(root, pending=()):
    """Verifica arquivos Markdown operacionais, relatórios e redirecionamentos."""
    paths = [root/'README.md', root/'AGENTS.md', root/'painel-vagas.md']
    for folder in ('oportunidades', 'empresas', 'monitoramento', 'relatorios', 'estrategia'):
        paths.extend((root/folder).rglob('*.md'))
    for path in paths:
        if not path.exists():
            continue
        # Entradas brutas são evidências imutáveis, não documentação operacional.
        if (root/'monitoramento/entradas') in path.parents:
            continue
        content = re.sub(r'```.*?```', '', path.read_text(encoding='utf-8'), flags=re.S)
        for link in LINK.findall(content):
            target = link.strip('<>')
            if re.match(r'^[a-zA-Z][\w+.-]*:', target) or target.startswith('#'):
                continue
            filepart = unquote(target.split('#', 1)[0])
            if filepart and (path.parent/filepart).resolve() not in pending and not (path.parent/filepart).exists():
                raise ValueError(f'Link quebrado em {path}: {target}')

def clean(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')

def process_link(root, d, prefix=''):
    return f'[{clean(d["empresa"])} — {clean(d["titulo"])}](<{prefix}{d["_path"].relative_to(root).as_posix()}>)'

def table(root, records):
    lines = ['| Vaga / processo | Etapa | Próxima ação / responsável | Prazo / revisão | Avaliação |',
             '|---|---|---|---|---|']
    for d in records:
        appraisal = d['_path'].parent/'avaliacao.md'
        label = f'{d["_score"]:.1f}/10' if d['_score'] is not None else 'sem score'
        ev = f'[{label} + cultura](<{appraisal.relative_to(root).as_posix()}>)' if appraisal.exists() else 'Ainda não avaliada'
        due = f'Prazo: {d["prazo"]}' if d.get('prazo') else 'Sem prazo informado'
        if d.get('revisar_em'):
            due += f'; revisão sugerida: {d["revisar_em"]}'
        phase = {'em_preparacao': 'em preparação', 'em_avaliacao': 'em avaliação', 'entrevista_tecnica': 'entrevista técnica', 'entrevista_gestao': 'entrevista de gestão'}.get(d['etapa'], d['etapa'].replace('_',' '))
        if d.get('resultado'):
            phase += ' / '+d['resultado'].replace('_',' ')
        lines.append(f'| {process_link(root,d)} | {phase} | {clean(d["proxima_acao"])} ({d["responsavel"]}) | {due} | {ev} |')
    return '\n'.join(lines) if records else 'Nenhum registro nesta categoria.'

def panel(root, records, today):
    records = sorted(records, key=lambda d: ({'alta':0,'media':1,'baixa':2}[d['prioridade']],d['empresa'],d['titulo']))
    lines = ['# Painel geral de vagas', '', f'Gerado em {today.isoformat()}. **Não editar estados aqui:** atualize `processo.md` e execute `python3 scripts/gestao_vagas.py gerar`.', '',
             f'{len(records)} oportunidades registradas; {sum(d["candidatura_confirmada"] for d in records)} candidaturas confirmadas no histórico (inclusive encerradas e sem data conhecida). Pistas e recibos sem cargo não contam como envios.', '',
             '[Preferências e pretensão](estrategia/referencias-candidaturas.md) · [Triagem de mensagens](monitoramento/triagem.md) · [Como manter](scripts/README.md)', '',
             'Scores preservados das avaliações validadas. Cultura e condições devem ser lidas com a avaliação; as datas de pesquisa constam dos dossiês.', '']
    for source in sorted({d['fonte_disponibilidade_inscricao'] for d in records if d.get('disponibilidade_inscricao')}):
        lines += [f'[Auditoria completa de disponibilidade](<{source}>): formulário acessível, anúncio expirado e disponibilidade não confirmada são separados da etapa pessoal. Pistas sem processo constam da auditoria.', '']
    due = [d for d in records if d['estado']=='aberto' and d.get('prazo')]
    overdue = [d for d in records if d['estado']!='encerrado' and d.get('revisar_em') and d['revisar_em'] <= today.isoformat()]
    groups = [('Ações com prazo informado',due),('Revisões sugeridas vencidas ou para hoje',overdue),
              ('Aguardando empresa',[d for d in records if d['estado']=='aberto' and d['responsavel']=='empresa']),
              ('Inscrições abertas verificadas — revisar condições',[d for d in records if d['estado']=='aberto' and d['responsavel']!='empresa' and d.get('disponibilidade_inscricao')=='aberta_verificada']),
              ('Disponibilidade não confirmada — conferir inscrição',[d for d in records if d['estado']=='aberto' and d['responsavel']!='empresa' and d.get('disponibilidade_inscricao')=='nao_confirmada']),
              ('A avaliar, preparar ou esclarecer',[d for d in records if d['estado']=='aberto' and d['responsavel']!='empresa' and not d.get('disponibilidade_inscricao')]),
              ('Anúncios expirados — sem nova candidatura',[d for d in records if d['estado']=='pausado' and d.get('disponibilidade_inscricao')=='anuncio_expirado']),
              ('Pausadas',[d for d in records if d['estado']=='pausado' and d.get('disponibilidade_inscricao')!='anuncio_expirado']),
              ('Encerradas',[d for d in records if d['estado']=='encerrado'])]
    for title, group in groups:
        lines.extend(['## '+title,'',table(root,group),''])
    lines += ['## Empresas de interesse e pendências sem vaga associada','',
              '[Triagem — recibos, duplicações e lacunas](monitoramento/triagem.md). Não altera automaticamente estados dos processos.','']
    for p in sorted((root/'empresas').glob('*/empresa.md')):
        if 'interesse_sem_vaga: true' in p.read_text(encoding='utf-8'):
            title = re.search(r'^# (.+)$', p.read_text(encoding='utf-8'), re.M)
            name = title.group(1) if title else p.parent.name
            lines.append(f'- [{name}](<{p.relative_to(root).as_posix()}>) — interesse sem vaga identificada.')
    return '\n'.join(lines)+'\n'

def monthly(root, records, month, today):
    if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])',month):
        raise ValueError('Mês deve ser AAAA-MM')
    if month > today.isoformat()[:7]:
        raise ValueError('Não gerar fechamento para mês futuro')
    def in_month(d): return isinstance(d,str) and d.startswith(month+'-')
    lines = [f'# Acompanhamento de {month}', '', f'Fotografia gerada em {today.isoformat()}; dados conhecidos nesta data. Não é reconstrução garantida do conhecimento disponível no passado.', '',
             '[Painel atual](../../painel-vagas.md)', '']
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
                lines.append(f'- {event["data"]} — {process_link(root,d,"../../")}: {event["descricao"]}')
    unknown = [d for d in records if d['candidatura_confirmada'] and not d.get('candidatura_em')]
    lines += ['', '## Limites de contagem','',f'{len(unknown)} candidatura(s) confirmada(s) sem data de envio conhecida; excluídas da contagem mensal. Eventos sem data também não são atribuídos ao mês de importação. Recibos sem cargo e pistas não contam como candidaturas.','']
    return '\n'.join(lines)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('acao',choices=['validar','gerar','relatorio'])
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--mes')
    parser.add_argument('--data',default=dt.date.today().isoformat(),help='Data de referência, AAAA-MM-DD')
    args=parser.parse_args()
    today=date(args.data,'data'); root=args.root.resolve()
    records=load_processes(root)
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
    try: main()
    except (ValueError, OSError, yaml.YAMLError) as e:
        raise SystemExit(str(e))
