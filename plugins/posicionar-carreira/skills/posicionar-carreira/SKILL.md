---
name: posicionar-carreira
description: >-
  Ajuda a montar a base de carreira e o portfólio, buscar e cadastrar vagas, configurar alertas e monitoramento, preparar candidaturas e ensaiar entrevistas. Use também para criar ou revisar casos a partir de apresentações, imagens, vídeos e áudios fornecidos.
---

# Posicionar Carreira

## Painel e dossiês

Use `abrir_painel` quando a pessoa pedir o painel. Para consulta em texto, use `listar_vagas` e `detalhar_vaga`. Nos pedidos vindos do painel, use o **ID do processo** para identificar a vaga e confira o **Arquivo oficial** com `detalhar_vaga`.

Se precisar trabalhar com arquivos, resolva `PLUGIN_DIR` como dois níveis acima deste `SKILL.md`. Execute `python -B "<PLUGIN_DIR>/server/servidor.py" --raiz` para localizar a pasta de dados e defina `CARREIRA_DIR` como o diretório `carreira/` nessa pasta. A configuração local usa `POSICIONAR_CARREIRA_ROOT`. Confirme o caminho retornado por `detalhar_vaga` antes de editar o dossiê se a raiz do painel e a do terminal divergirem.

Em `carreira/oportunidades/<empresa>/<id>/`, use `processo.md` para estado, eventos e próxima ação, e `vaga.md` para os requisitos quando existir. Consulte as fontes profissionais autorizadas, como `perfil/perfil-profissional.md`, `perfil/evidencias/` e `curriculos/base.md`, quando disponíveis. Concilie o currículo com as correções mais recentes da pessoa. Use somente experiências, datas, contribuições e resultados que ela possa sustentar. Identifique lacunas em vez de inferir fatos.

## Começar do zero

Quando a pessoa pedir ajuda para montar a base de carreira, confirme a pasta de dados e pergunte se já tem um currículo, perfil ou portfólio que queira usar. Aproveite o material autorizado e faça perguntas em etapas sobre o que estiver faltando. Comece pelos objetivos profissionais, pelo histórico de trabalho e por uma ou duas entregas que a pessoa possa descrever com clareza.

- Organize o histórico, as competências e os resultados confirmados em `perfil/perfil-profissional.md`. Use `perfil/evidencias/` para fontes e detalhes de entregas. Identifique as restrições de divulgação.
- Registre cargos de interesse e critérios de escolha em `estrategia/objetivos.md`. Pergunte apenas pelas preferências que ajudem a selecionar vagas.
- Proponha `curriculos/base.md` a partir do perfil conferido. Inclua só os dados de contato que a pessoa queira compartilhar nas candidaturas.
- Organize casos autorizados em `portfolio/`, com contexto, contribuição pessoal e resultado sustentado. Confirme o que pode ser apresentado a terceiros.
- Se a pessoa já tiver vagas em mente, peça empresa, cargo e fonte para cada uma. Use `criar_vaga` quando ela pedir o cadastro.

Mostre os rascunhos antes de gravar dados pessoais. Salve os documentos aprovados na base configurada e conserve materiais existentes. Uma pessoa pode cadastrar e acompanhar vagas enquanto o perfil e o portfólio ainda estão em preparação.

## Montar ou atualizar o portfólio

Para criar ou atualizar um caso a partir de arquivos de projeto, apresentações, imagens, vídeos, gravações ou áudios exportados, siga [Portfólio a partir de evidências](references/portfolio.md). Consulte os casos que já existem antes de criar um novo. Distinga o que a fonte demonstra, a contribuição da pessoa e o que ainda precisa ser confirmado.

## Gestão de processos

Para gravações autorizadas, use `criar_vaga`, `registrar_evento` ou `atualizar_vaga`. Consulte o detalhe antes de editar e informe o ID e a revisão atuais. Em caso de conflito, leia a nova versão e reconcilie a edição antes de tentar novamente.

Ao mapear uma vaga no chat, registre em `vaga.md` a descrição disponível, a fonte e a data da consulta. Deixe a síntese e a análise em `avaliacao.md`. Siga o [procedimento de pesquisa salarial](references/benchmark-salarial.md) para registrar a faixa anunciada e os comparáveis, inclusive quando o anúncio omitir a faixa.

Preserve o histórico e mantenha estado, etapa e resultado separados. Confirme a identidade da vaga pelo ID, anúncio ou evidência antes de cadastrar ou registrar retorno. Uma mensagem sem vínculo confirmado não altera nenhum dossiê. Confirme evidência antes de registrar envio, encerramento ou avanço de etapa. Um formulário preenchido ainda requer submissão. Uma indicação de revisão tem finalidade de acompanhamento e não agenda lembrete.

Para lotes ou sessões sem MCP, use `python -B "<PLUGIN_DIR>/server/lote.py"`. Confira a prévia por dossiê antes de aplicar um lote e reconcilie as falhas antes de repetir. Preserve `painel-vagas.md` como índice de ordenação, se existir. Guarde o conteúdo produzido no dossiê e use as operações estruturadas para alterar o registro do processo.

## Avaliar vaga

Compare as responsabilidades e os requisitos com as evidências profissionais e as preferências da pessoa. Separe aderência, condições, cultura e lacunas. Cite as fontes pertinentes e indique quando uma informação precisa de confirmação. Para uma avaliação com nota, siga o [contrato de pontuação](references/scoring.md) e execute o validador empacotado. Uma nota expressa aderência ao objetivo informado. Quando faltar informação essencial, registre as lacunas e deixe a nota em branco.

Consulte o [benchmark salarial](references/benchmark-salarial.md) antes de recomendar próximos passos ou preparar negociação. Use somente critérios confirmados pela pessoa. A remuneração é informativa por padrão.

## Monitorar vagas por e-mail

Quando a pessoa pedir para buscar novas vagas compatíveis ou acompanhar retornos de uma vaga pelo e-mail, siga [Monitoramento por e-mail](references/monitoramento-email.md). Use a vaga selecionada e os objetivos da base local conforme a modalidade. Configure a recorrência pela ferramenta nativa do Codex quando a pessoa pedir para ativar.

Para encontrar vagas na internet ou cadastrar anúncios selecionados, siga [Pesquisar vagas na web](references/busca-vagas.md). Para preparar alertas do LinkedIn, siga [Alertas do LinkedIn](references/busca-linkedin.md). Quando a pessoa pedir um prompt para copiar para o Dot, siga [Atualizar o monitor do Dot](references/atualizar-monitor-dot.md).

## Preparar currículo e candidatura

Siga [Candidaturas](references/candidaturas.md). Consulte as evidências, revise o currículo e a carta em Markdown, gere e confira o PDF e apresente o formulário para revisão. Execute as etapas solicitadas e autorizadas. Registre o envio somente quando confirmado e preserve as versões identificadas em `envios/`. Envio de candidatura, contato com recrutador e publicação exigem autorização para a ação específica.

Ao revisar prosa de currículo, carta ou respostas, use [Humanizer](../humanizer/SKILL.md) em modo embutido para corrigir trechos que prejudiquem a clareza ou a voz da pessoa. Preserve fatos, contribuições e resultados.

## Preparar entrevista

Use o estágio real da vaga para escolher casos, simular perguntas e identificar pontos a esclarecer. Estruture os exemplos com contexto, contribuição pessoal, decisões, validação e resultado. Marque perguntas de ensaio como simulações. Trabalhe na conversa e salve um plano no dossiê quando a pessoa pedir. Preserve as gravações e os materiais originais, identificando incertezas de transcrição. Registre feedback e avanços conforme a evidência disponível.

Se a conversa incluir remuneração ou negociação, consulte o benchmark da vaga e confirme quais condições a pessoa quer esclarecer.
