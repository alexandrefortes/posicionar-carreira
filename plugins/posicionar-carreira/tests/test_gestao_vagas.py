import copy
import datetime as dt
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import yaml

SERVER = Path(__file__).resolve().parents[1] / 'server'
sys.path.insert(0, str(SERVER))
import gestao_vagas as g

class GestaoTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'dados-teste'; self.root.mkdir()
        (self.root/'fonte.md').write_text('Confirmação recebida',encoding='utf-8')
        self.data=dict(id='empresa/local-001',empresa='Empresa',titulo='Vaga',status='entrevistas',
            prioridade='alta',proxima_acao='Aguardar',responsavel='empresa',
            fonte_estado='fonte.md',candidatura_confirmada=True,fonte_candidatura='fonte.md',
            identificada_em='2026-09-04',candidatura_em='2026-09-05',atualizado_em='2026-10-06',
            encerrada_em=None,prazo=None,revisar_em=None,
            ids_externos=['linkedin:123'],eventos=[
                dict(data='2026-09-05',registrado_em='2026-09-05',descricao='Envio confirmado',fonte='fonte.md'),
                dict(data='2026-10-06',registrado_em='2026-10-06',descricao='Entrevista realizada',fonte='fonte.md',
                     alteracoes={'status': {'anterior': 'candidatura-enviada', 'atual': 'entrevistas'}})])
    def save(self,data=None,folder='empresa/local-001'):
        p=self.root/'oportunidades'/folder/'processo.md'; p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text('---\n'+yaml.safe_dump(data or self.data,allow_unicode=True)+'---\n# Processo\n',encoding='utf-8')
    def test_duplicate_id(self):
        self.save(); self.save(folder='empresa/local-002')
        with self.assertRaisesRegex(ValueError,'ID duplicado'): g.load_processes(self.root)

    def test_lint_reune_erros_independentes_sem_gravar(self):
        self.data.update(status='legado', prazo='amanhã', fonte_estado='ausente.pdf')
        self.save()
        outro = self.root / 'oportunidades/outra/local-002/processo.md'
        outro.parent.mkdir(parents=True)
        outro.write_text('---\ninvalido: [\n---\n', encoding='utf-8')
        (self.root / 'README.md').write_text('[A](a.md) e [B](b.md)', encoding='utf-8')
        def arquivos():
            return {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        antes = arquivos()
        resultado = g.lint(self.root)
        self.assertEqual(resultado['dossies'], 2)
        self.assertEqual(len(resultado['erros']), 7)
        self.assertEqual({Path(e['arquivo']).name for e in resultado['erros']}, {'processo.md', 'README.md'})
        self.assertTrue(all(e['sugestao'] for e in resultado['erros']))
        self.assertEqual(arquivos(), antes)

    def test_lint_fontes_compartilhadas_e_material_arquivado(self):
        self.data['eventos'][0]['descricao'] = 'Recebido e-mail'
        self.save()
        outro = copy.deepcopy(self.data)
        outro.update(id='empresa/local-002', ids_externos=[])
        outro['eventos'][0]['descricao'] = 'Entrevista de arquitetura confirmada para sexta-feira'
        self.save(outro, folder=outro['id'])
        arquivo = self.root / 'archive/anuncio.md'
        arquivo.parent.mkdir()
        arquivo.write_text('Anúncio original', encoding='utf-8')
        vaga = self.root / 'oportunidades' / self.data['id'] / 'vaga.md'
        vaga.write_text('# Vaga\n\n[Anúncio](../../../archive/anuncio.md)\n', encoding='utf-8')
        historico = self.root / 'oportunidades' / outro['id'] / 'vaga.md'
        historico.write_text('# Vaga\nDescrição atual.\n[Pesquisa histórica](../../../archive/anuncio.md)', encoding='utf-8')
        resultado = g.lint(self.root)
        self.assertEqual(resultado['erros'], [])
        self.assertEqual(len(resultado['avisos']), 2)
        self.assertEqual({Path(a['arquivo']) for a in resultado['avisos']}, {vaga.parent / 'processo.md'})
        self.data.update(status='reprovado')
        self.save()
        self.assertEqual(len(g.lint(self.root)['avisos']), 1)

    def test_cli_lint_erros_avisos_e_nome_do_comando(self):
        self.save()
        def rodar(acao):
            return subprocess.run([sys.executable, '-X', 'utf8', '-B', str(SERVER/'gestao_vagas.py'),
                                   acao, '--root', str(self.root)], capture_output=True, encoding='utf-8', timeout=10)
        arquivo = self.root / 'archive/oportunidades/empresa/local-001/vaga.md'
        arquivo.parent.mkdir(parents=True)
        arquivo.write_text('Anúncio', encoding='utf-8')
        aviso = rodar('lint')
        self.assertEqual(aviso.returncode, 0, aviso.stderr)
        self.assertIn('Erros: 0. Avisos: 1.', aviso.stdout)
        self.data['prazo'] = 'ontem'
        self.save()
        erro = rodar('lint')
        self.assertEqual(erro.returncode, 1, erro.stdout + erro.stderr)
        self.assertIn('Avisos: 1.', erro.stdout)
        self.assertEqual(rodar('validar').returncode, 2)

    def test_lint_mostra_cada_grupo_de_originais_e_pendencias(self):
        outro = copy.deepcopy(self.data)
        outro.update(id='empresa/local-002', ids_externos=[])
        for i, evento in enumerate(self.data['eventos']):
            a, b = f'original-{i}.md', f'copia-{i}.md'
            for nome in (a, b):
                (self.root / nome).write_text(f'Comprovante {i}', encoding='utf-8')
            evento.update(fonte=a, triagem=[g.triagem.chave(f'- Mensagem {i}')])
            outro['eventos'][i]['fonte'] = b
        self.save()
        self.save(outro, folder=outro['id'])
        triagem = self.root / 'monitoramento/triagem.md'
        triagem.parent.mkdir()
        triagem.write_text('- [Resolvida](../oportunidades/empresa/local-002/processo.md) · Mensagem 0\n'
                           '- Mensagem 1\n- Mensagem ainda ambígua\n', encoding='utf-8')
        erros = g.lint(self.root)['erros']
        self.assertEqual(len(erros), 4)
        self.assertEqual(sum('Fonte repetida' in e['problema'] for e in erros), 2)
        self.assertTrue(any('pendência aberta' in e['problema'] for e in erros))
        self.assertTrue(any('evento está em empresa/local-001' in e['problema'] and
                            Path(e['arquivo']) == triagem for e in erros))
    def test_rejects_unknown_status_and_legacy_fields(self):
        self.data['status']='encerrado'; self.save()
        with self.assertRaisesRegex(ValueError,'status inválido'): g.load_processes(self.root)
        self.data.update(status='reprovado', resultado='reprovado'); self.save()
        with self.assertRaisesRegex(ValueError,'único campo status'): g.load_processes(self.root)
    def test_confirmed_without_source(self):
        self.data['fonte_candidatura']=None; self.save()
        with self.assertRaisesRegex(ValueError,'Fonte de evidência ausente'): g.load_processes(self.root)
    def test_months_are_distinct(self):
        self.save(); records=g.load_processes(self.root)
        text=g.monthly(self.root,records,'2026-10',dt.date(2026,10,6))
        self.assertIn('Candidaturas confirmadas enviadas no mês (0)',text)
        self.assertIn('Entrevista realizada (candidatura-enviada → entrevistas)',text)
        self.assertNotIn('Envio confirmado',text)
        sept=g.monthly(self.root,records,'2026-09',dt.date(2026,10,6))
        self.assertIn('Candidaturas confirmadas enviadas no mês (1)',sept)
    def test_unconfirmed_not_counted(self):
        self.data.update(status='identificada',candidatura_confirmada=False,candidatura_em=None,fonte_candidatura=None)
        self.save(); text=g.monthly(self.root,g.load_processes(self.root),'2026-09',dt.date(2026,9,6))
        self.assertIn('Candidaturas confirmadas enviadas no mês (0)',text)
    def test_unknown_submission_date(self):
        self.data['candidatura_em']=None; self.save()
        text=g.monthly(self.root,g.load_processes(self.root),'2026-09',dt.date(2026,9,6))
        self.assertIn('1 candidatura(s) confirmada(s) sem data',text)
    def test_deadline_requires_source(self):
        self.data['prazo']='2026-10-09'; self.save()
        with self.assertRaisesRegex(ValueError,'Fonte de evidência ausente'): g.load_processes(self.root)
    def test_external_id_duplicate(self):
        self.save(); other=copy.deepcopy(self.data); other['id']='empresa/local-002'; self.save(other,'empresa/local-002')
        with self.assertRaisesRegex(ValueError,'ID externo duplicado'): g.load_processes(self.root)
    def test_local_broken_link(self):
        (self.root/'README.md').write_text('[destino](ausente.md)',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Link quebrado'): g.validate_links(self.root)
    def test_link_validation_skips_historical_reports_and_checks_generated_reports(self):
        month=self.root/'relatorios/2026-09'
        month.mkdir(parents=True)
        (month/'migracao-concluida.md').write_text('[Guia anterior](../../scripts/README.md)',encoding='utf-8')
        g.validate_links(self.root)
        generated=month/'acompanhamento-gerado-2026-10-06.md'
        generated.write_text('[Painel atual](../../painel-vagas.md)',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'acompanhamento-gerado'): g.validate_links(self.root)
    def test_named_responsibility_comes_from_the_workspace(self):
        self.data['responsavel']='Paula'
        self.save()
        with self.assertRaisesRegex(ValueError,'responsável inválido'): g.load_processes(self.root)
        (self.root/'config.json').write_text('{"responsavel":"Paula"}',encoding='utf-8')
        records=g.load_processes(self.root)
        self.assertIn('- **Responsável:** Paula',g.panel(self.root,records,dt.date(2026,10,6)))
    def test_closed_not_waiting(self):
        self.data.update(status='reprovado',encerrada_em='2026-10-06'); self.save()
        text=g.panel(self.root,g.load_processes(self.root),dt.date(2026,10,6))
        job=text.split('### Empresa — Vaga')[1].split('\n### ')[0].split('\n## ')[0]
        self.assertIn('- **Status:** reprovado',job)
        self.assertGreater(text.index('### Empresa — Vaga'),text.index('## Encerradas'))
        self.assertEqual(text.count('### Empresa — Vaga\n'),1)

    def test_panel_uses_job_sections(self):
        self.save()
        text=g.panel(self.root,g.load_processes(self.root),dt.date(2026,10,6))
        self.assertIn('### Empresa — Vaga\n',text)
        self.assertIn('- **Processo:** [Abrir processo](<oportunidades/empresa/local-001/processo.md>)',text)
        self.assertIn('- **Prioridade:** alta',text)
        self.assertIn('- **Status:** entrevistas',text)
        self.assertIn('- **Próxima ação:** Aguardar',text)
        self.assertIn('- **Responsável:** empresa',text)
        self.assertNotIn('| Vaga / processo |',text)

    def test_panel_groups_by_status_with_availability_separate(self):
        self.save()
        for suffix, status, availability, confirmed in [
            ('expirada', 'identificada', 'anuncio_expirado', False),
            ('encerrada', 'reprovado', None, True),
            ('enviada', 'candidatura-enviada', 'anuncio_expirado', True),
        ]:
            other=copy.deepcopy(self.data)
            other.update(id='empresa/'+suffix,titulo=suffix,status=status,
                encerrada_em='2026-10-06' if status=='reprovado' else None,ids_externos=[],
                candidatura_confirmada=confirmed,disponibilidade_inscricao=availability,
                fonte_disponibilidade_inscricao='fonte.md' if availability else None)
            if not confirmed: other.update(candidatura_em=None,fonte_candidatura=None)
            self.save(other,'empresa/'+suffix)
        text=g.panel(self.root,g.load_processes(self.root),dt.date(2026,10,6))
        active, finished=text.split('## Em andamento')[1].split('## Encerradas')
        for name in ('Vaga','expirada','enviada'):
            self.assertIn('### Empresa — '+name+'\n',active)
            self.assertNotIn('### Empresa — '+name+'\n',finished)
        self.assertIn('### Empresa — encerrada\n',finished)
        self.assertEqual(text.count('### Empresa — encerrada\n'),1)
        self.assertEqual(active.count('**Disponibilidade da inscrição:** anúncio expirado'),2)

    def test_salary_benchmark_is_visible_without_changing_process_or_score(self):
        self.save()
        folder=self.root/'oportunidades/empresa/local-001'
        (folder/'avaliacao.md').write_text('# Avaliação',encoding='utf-8')
        (folder/'benchmark-salarial.md').write_text(
            '---\npesquisado_em: "2026-11-01"\nresumo: "Comparável BR; faixa não é oferta"\n---\n# Fontes\n',encoding='utf-8')
        (folder/'avaliacao-validada.json').write_text('{"status":"scored","final_score":8.1}',encoding='utf-8')
        records=g.load_processes(self.root)
        before=copy.deepcopy(records)
        text=g.panel(self.root,records,dt.date(2026,11,1))
        self.assertIn('Comparável BR; faixa não é oferta',text)
        self.assertIn('oportunidades/empresa/local-001/benchmark-salarial.md',text)
        self.assertIn('8.1/10',text)
        self.assertEqual(records,before)

    def test_salary_research_gap_does_not_hide_opportunity(self):
        self.save()
        text=g.panel(self.root,g.load_processes(self.root),dt.date(2026,11,1))
        self.assertIn('### Empresa — Vaga\n',text)
        self.assertIn('- **Benchmark salarial:** Pesquisa pendente.',text)

    def test_painel_aceita_pesquisa_legada_sem_resumo(self):
        self.save()
        pasta = self.root / "oportunidades/empresa/local-001"
        pesquisa = pasta / "benchmark-salarial.md"
        for original in ("---\npesquisado_em: '2026-11-01'\n---\nFontes históricas.\n", "# Pesquisa anterior\n"):
            with self.subTest(original=original):
                pesquisa.write_text(original, encoding="utf-8")
                painel = g.panel(self.root, g.load_processes(self.root), dt.date(2026, 11, 1))
                self.assertIn("oportunidades/empresa/local-001/benchmark-salarial.md", painel)
                self.assertIn("### Empresa — Vaga", painel)
                self.assertEqual(pesquisa.read_text(encoding="utf-8"), original)

    def test_panel_preserves_manual_review_tail_across_generations(self):
        self.save()
        path=self.root/'painel-vagas.md'
        tail='\n## Revisões recebidas — 01/11/2026\n\nParecer da pessoa titular.\n\n| Pista | Pendência |\n|---|---|\n| Outra vaga | Confirmar identidade |\n'
        path.write_text('# Painel anterior\n'+tail,encoding='utf-8')
        records=g.load_processes(self.root)
        for _ in range(2):
            text=g.panel(self.root,records,dt.date(2026,11,1))
            self.assertTrue(text.endswith(tail))
            self.assertEqual(text.count('Parecer da pessoa titular.'),1)
            path.write_text(text,encoding='utf-8')

    def test_first_generation_and_report_versions(self):
        self.save()
        def run(*args):
            career = self.root/'ausente' if '--root' in args else self.root
            result = subprocess.run(
                [sys.executable, '-X', 'utf8', '-B', str(SERVER/'gestao_vagas.py'), *args, '--data', '2026-10-06'],
                cwd=self.tmp.name, env={**os.environ, 'CARREIRA_ROOT': str(career)},
                capture_output=True, encoding='utf-8', timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return result.stdout
        run('relatorio','--mes','2026-08')
        painel = self.root/'painel-vagas.md'
        self.assertFalse(painel.exists())
        relatorio=self.root/'relatorios/2026-08/acompanhamento-gerado-2026-10-06.md'
        self.assertNotIn('painel-vagas.md',relatorio.read_text(encoding='utf-8'))
        (self.root/'README.md').write_text('[Painel](painel-vagas.md)',encoding='utf-8')
        run('gerar', '--root', str(self.root))
        self.assertIn('consulte Gestão de oportunidades no guia do Posicionar Carreira',
                      painel.read_text(encoding='utf-8'))
        self.assertIn('Dossiês examinados: 1. Erros: 0. Avisos: 0.', run('lint'))
        self.assertFalse((self.root/'scripts').exists())
        run('relatorio','--mes','2026-09')
        first=self.root/'relatorios/2026-09/acompanhamento-gerado-2026-10-06.md'
        original=first.read_bytes()
        run('relatorio','--mes','2026-09')
        self.assertEqual(first.read_bytes(),original)
        second=first.with_name('acompanhamento-gerado-2026-10-06-r2.md')
        self.assertEqual(second.read_bytes(),original)

    def test_panel_links_to_checkout_guide_when_present(self):
        self.save()
        guide=self.root.parent/'plugins/posicionar-carreira/README.md'
        guide.parent.mkdir(parents=True)
        guide.write_text('## Gestão de oportunidades',encoding='utf-8')
        text=g.panel(self.root,g.load_processes(self.root),dt.date(2026,10,6))
        self.assertIn('[Como manter](../plugins/posicionar-carreira/README.md#gestão-de-oportunidades)',text)

    def test_availability_keeps_status_and_separates_queue(self):
        self.save()
        other=copy.deepcopy(self.data)
        other.update(id='empresa/local-002',titulo='Nova vaga',responsavel='titular',status='identificada',
            candidatura_confirmada=False,candidatura_em=None,fonte_candidatura=None,
            ids_externos=[],disponibilidade_inscricao='nao_confirmada',
            fonte_disponibilidade_inscricao='fonte.md')
        self.save(other,'empresa/local-002')
        records=g.load_processes(self.root)
        text=g.panel(self.root,records,dt.date(2026,10,16))
        waiting=text.split('### Empresa — Vaga')[1].split('\n### ')[0].split('\n## ')[0]
        uncertain=text.split('### Empresa — Nova vaga')[1].split('\n### ')[0].split('\n## ')[0]
        self.assertIn('- **Responsável:** empresa',waiting)
        self.assertIn('- **Responsável:** titular',uncertain)
        self.assertIn('- **Disponibilidade da inscrição:** não confirmada',uncertain)
        self.assertEqual(records[0]['status'],'entrevistas')
        self.assertEqual(sum(d['candidatura_confirmada'] for d in records),1)

    def test_current_plan_groups_keep_public_evidence_separate_from_submission(self):
        self.save()
        for suffix, group in [('compatible', 'plano_modalidade_compativel'), ('clarify', 'plano_esclarecimento')]:
            other=copy.deepcopy(self.data)
            other.update(id='empresa/'+suffix,titulo=suffix,responsavel='titular',status='identificada',
                candidatura_confirmada=False,candidatura_em=None,fonte_candidatura=None,
                ids_externos=[],grupo_plano_atual=group,abertura_publica='candidatura_publica_disponivel',
                disponibilidade_inscricao='nao_confirmada',fonte_disponibilidade_inscricao='fonte.md',
                fonte_plano='fonte.md' if suffix == 'compatible' else 'ausente.md')
            self.save(other,'empresa/'+suffix)
        records=g.load_processes(self.root)
        text=g.panel(self.root,records,dt.date(2026,10,30))
        compatible=text.split('### Empresa — compatible')[1].split('\n### ')[0].split('\n## ')[0]
        clarify=text.split('### Empresa — clarify')[1].split('\n### ')[0].split('\n## ')[0]
        self.assertIn('- **Plano atual:** modalidade compatível',compatible)
        self.assertIn('- **Plano atual:** esclarecer antes de candidatar',clarify)
        self.assertIn('- **Disponibilidade da inscrição:** não confirmada',clarify)
        self.assertIn('[Fonte do plano atual](<fonte.md>)',text)
        self.assertNotIn('ausente.md',text)
        self.assertEqual(text.count('### Empresa — clarify\n'),1)
        self.assertEqual(sum(d['candidatura_confirmada'] for d in records),1)
        self.assertEqual(next(d for d in records if d['titulo']=='clarify')['status'],'identificada')

if __name__=='__main__': unittest.main()
