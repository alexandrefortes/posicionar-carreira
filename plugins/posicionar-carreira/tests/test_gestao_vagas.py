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
        self.data=dict(id='empresa/local-001',empresa='Empresa',titulo='Vaga',estado='aberto',
            etapa='triagem',prioridade='alta',proxima_acao='Aguardar',responsavel='empresa',
            fonte_estado='fonte.md',candidatura_confirmada=True,fonte_candidatura='fonte.md',
            identificada_em='2026-09-04',candidatura_em='2026-09-05',atualizado_em='2026-10-06',
            encerrada_em=None,resultado=None,prazo=None,revisar_em=None,
            ids_externos=['linkedin:123'],eventos=[
                dict(data='2026-09-05',registrado_em='2026-09-05',descricao='Envio confirmado',fonte='fonte.md'),
                dict(data='2026-10-06',registrado_em='2026-10-06',descricao='Entrevista realizada',fonte='fonte.md')])
    def save(self,data=None,folder='empresa/local-001'):
        p=self.root/'oportunidades'/folder/'processo.md'; p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text('---\n'+yaml.safe_dump(data or self.data,allow_unicode=True)+'---\n# Processo\n',encoding='utf-8')
    def test_duplicate_id(self):
        self.save(); self.save(folder='empresa/local-002')
        with self.assertRaisesRegex(ValueError,'ID duplicado'): g.load_processes(self.root)
    def test_closed_without_outcome(self):
        self.data['estado']='encerrado'; self.save()
        with self.assertRaisesRegex(ValueError,'encerramento sem resultado'): g.load_processes(self.root)
    def test_confirmed_without_source(self):
        self.data['fonte_candidatura']=None; self.save()
        with self.assertRaisesRegex(ValueError,'Fonte de evidência ausente'): g.load_processes(self.root)
    def test_months_are_distinct(self):
        self.save(); records=g.load_processes(self.root)
        text=g.monthly(self.root,records,'2026-10',dt.date(2026,10,6))
        self.assertIn('Candidaturas confirmadas enviadas no mês (0)',text)
        self.assertIn('Entrevista realizada',text); self.assertNotIn('Envio confirmado',text)
        sept=g.monthly(self.root,records,'2026-09',dt.date(2026,10,6))
        self.assertIn('Candidaturas confirmadas enviadas no mês (1)',sept)
    def test_unconfirmed_not_counted(self):
        self.data.update(candidatura_confirmada=False,candidatura_em=None,fonte_candidatura=None)
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
        self.data.update(estado='encerrado',resultado='reprovado',encerrada_em='2026-10-06'); self.save()
        text=g.panel(self.root,g.load_processes(self.root),dt.date(2026,10,6))
        job=text.split('### Empresa — Vaga')[1].split('\n### ')[0].split('\n## ')[0]
        self.assertIn('- **Estado:** encerrado',job)
        self.assertIn('reprovado',job)
        self.assertEqual(text.count('### Empresa — Vaga\n'),1)

    def test_panel_uses_job_sections(self):
        self.save()
        text=g.panel(self.root,g.load_processes(self.root),dt.date(2026,10,6))
        self.assertIn('### Empresa — Vaga\n',text)
        self.assertIn('- **Processo:** [Abrir processo](<oportunidades/empresa/local-001/processo.md>)',text)
        self.assertIn('- **Prioridade:** alta',text)
        self.assertIn('- **Etapa / resultado:** triagem',text)
        self.assertIn('- **Próxima ação:** Aguardar',text)
        self.assertIn('- **Responsável:** empresa',text)
        self.assertNotIn('| Vaga / processo |',text)

    def test_panel_separates_expired_and_closed_without_hiding_active_applications(self):
        self.save()
        for suffix, state, availability, confirmed, outcome in [
            ('expirada', 'pausado', 'anuncio_expirado', False, None),
            ('pausada', 'pausado', None, False, None),
            ('encerrada', 'encerrado', None, True, 'reprovado'),
            ('enviada', 'aberto', 'anuncio_expirado', True, None),
        ]:
            other=copy.deepcopy(self.data)
            other.update(id='empresa/'+suffix,titulo=suffix,estado=state,resultado=outcome,
                encerrada_em='2026-10-06' if outcome else None,ids_externos=[],
                candidatura_confirmada=confirmed,disponibilidade_inscricao=availability,
                fonte_disponibilidade_inscricao='fonte.md' if availability else None)
            if not confirmed: other.update(candidatura_em=None,fonte_candidatura=None)
            self.save(other,'empresa/'+suffix)
        text=g.panel(self.root,g.load_processes(self.root),dt.date(2026,10,6))
        active, finished=text.split('## Em andamento ou pausadas')[1].split('## Anúncios expirados ou processos encerrados')
        for name in ('Vaga','pausada','enviada'):
            self.assertIn('### Empresa — '+name+'\n',active)
            self.assertNotIn('### Empresa — '+name+'\n',finished)
        for name in ('expirada','encerrada'):
            self.assertIn('### Empresa — '+name+'\n',finished)
            self.assertEqual(text.count('### Empresa — '+name+'\n'),1)

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

    def test_legacy_salary_research_without_summary_remains_linked(self):
        self.save()
        relative = 'oportunidades/empresa/local-001/benchmark-salarial.md'
        path = self.root / relative
        for content in (
            '# Fontes registradas antes da migração\n',
            '---\npesquisado_em: "2026-11-01"\n---\n# Fontes\n',
            '---\nresumo: 100\n---\n# Fontes\n',
            '---\nresumo: [\n---\n# Fontes\n',
        ):
            with self.subTest(content=content):
                path.write_text(content, encoding='utf-8')
                text = g.panel(self.root, g.load_processes(self.root), dt.date(2026,11,1))
                self.assertIn(f'- **Benchmark salarial:** [fontes e limites](<{relative}>)', text)
                self.assertEqual(path.read_text(encoding='utf-8'), content)

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
        self.assertIn('1 processos validados', run('validar'))
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

    def test_availability_keeps_personal_stage_and_separates_queue(self):
        self.save()
        other=copy.deepcopy(self.data)
        other.update(id='empresa/local-002',titulo='Nova vaga',responsavel='titular',
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
        self.assertEqual(records[0]['etapa'],'triagem')
        self.assertEqual(sum(d['candidatura_confirmada'] for d in records),1)

    def test_current_plan_groups_keep_public_evidence_separate_from_submission(self):
        self.save()
        for suffix, group in [('compatible', 'plano_modalidade_compativel'), ('clarify', 'plano_esclarecimento')]:
            other=copy.deepcopy(self.data)
            other.update(id='empresa/'+suffix,titulo=suffix,responsavel='titular',
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
        self.assertEqual(next(d for d in records if d['titulo']=='clarify')['etapa'],'triagem')

if __name__=='__main__': unittest.main()
