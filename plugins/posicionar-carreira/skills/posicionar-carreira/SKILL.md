---
name: posicionar-carreira
description: >-
  Apoia o desenvolvimento profissional com base nas evidências da pessoa. Use para avaliar vagas e empresas, preparar currículos, candidaturas e entrevistas, acompanhar processos, registrar evidências e atualizar portfólio. Ajuda a buscar e cadastrar vagas e preparar alertas do LinkedIn e monitoramento por e-mail ou pelo Dot.
---

# Posicionar carreira

Relacione o trabalho comprovado da pessoa aos seus objetivos profissionais. Use o fluxo pertinente ao pedido. Sugira o registro de evidências de outros projetos quando forem relevantes e peça autorização antes de registrá-las.

## Caminhos e fontes

Em uma primeira conversa de configuração, chame primeiro `abrir_boas_vindas` quando o cliente puder exibir MCP Apps. Se a tela estiver indisponível ou a pessoa pedir uma consulta em texto, use `verificar_configuracao` para conferir a base sem gravar. Use `inicializar_carreira` somente depois de a pessoa escolher uma pasta existente pelo caminho absoluto e autorizar o preparo. Peça autorização para os modelos iniciais que ela quiser. Com `oportunidades/` disponível, o registro de vagas pode começar. Consulte [Fonte local](../../README.md#fonte-local) para a configuração persistente e os modelos aceitos.

Resolva `SKILL_DIR` pelo diretório absoluto deste `SKILL.md` e `PLUGIN_DIR` por `SKILL_DIR/../..`. Para localizar arquivos da base configurada, obtenha `CARREIRA_DIR` executando `python -B "<PLUGIN_DIR>/server/dados.py"` com o caminho absoluto do script. O painel usa o mesmo resolvedor. Use somente os dados da pessoa nessa pasta ou que ela fornecer.

Siga os procedimentos desta skill e consulte as fontes pertinentes ao pedido.

| Fonte em `CARREIRA_DIR` | Responsabilidade |
|---|---|
| `perfil/perfil-profissional.md` e `perfil/evidencias/` | Fatos profissionais e evidências, incluindo correções posteriores identificadas |
| `perfil/voz-editorial.md`, quando existir | Preferências de escrita para revisão com Humanizer |
| `curriculos/base.md` | Currículo derivado; não prevalece sobre correção factual confirmada |
| `portfolio/` | Casos de entregas, implantação e adoção pertinentes à vaga |
| `estrategia/referencias-candidaturas.md` ou `estrategia/objetivos.md` | Objetivos e preferências de trabalho. Consulte respostas gerais aprovadas quando existirem e mantenha cada exceção no escopo da vaga |
| `oportunidades/<empresa>/<id>/vaga.md` | Descrição do anúncio, fonte e data, separadas da síntese e da análise. Siga o [registro da descrição](references/busca-e-triagem.md#registro-da-descrição) |
| `oportunidades/<empresa>/<id>/avaliacao.md` | Análise de aderência, cultura e condições |
| `oportunidades/<empresa>/<id>/benchmark-salarial.md` | Pesquisa salarial por vaga, com comparáveis, fontes, datas e limites |
| `oportunidades/<empresa>/<id>/processo.md` | Status, eventos, evidências de envio e próxima ação oficiais |
| `oportunidades/<empresa>/<id>/plano-preparacao-entrevista.md` | Preparo específico da vaga, com referências ao processo e ao repertório comum |
| `empresas/<empresa>/pesquisas/` | Pesquisas culturais datadas, interpretadas por vaga e time |
| `painel-vagas.md` e `monitoramento/triagem.md` | Visão derivada e entradas ainda sem associação confirmada |
| `perfil/linkedin-snapshot.md` | Fotografia do perfil publicado, não fonte factual prioritária |

Antes de redigir alegações profissionais, concilie o perfil, as evidências pertinentes e as correções explícitas mais recentes da pessoa. Não reutilize um número, período ou competência desatualizado só porque aparece no currículo base. Identifique contradições pendentes e esclareça somente o que afetar a resposta. Consulte [evidências](references/evidencias.md).

Quando a pessoa pedir ajuda para preencher os modelos iniciais, comece pelo histórico, pelos objetivos e por uma ou duas entregas comprovadas. Aproveite o currículo, o perfil ou o portfólio que ela autorizar consultar. Confirme os fatos, as preferências e os dados de contato e mostre os rascunhos antes de gravar. A pessoa pode cadastrar vagas enquanto prepara os demais materiais.

## Painel no chat

Quando a pessoa selecionar **Posicionar Carreira** e pedir **Dashboard** ou uma visão geral dos processos, chame `abrir_dashboard` diretamente. Se o cliente não exibir a interface, consulte `listar_vagas` e responda com o total e a contagem por status. Conte cada processo pelo ID.

Quando a pessoa pedir para abrir a lista de vagas no chat, chame `abrir_painel`. Para consultas em texto, use `listar_vagas` ou `detalhar_vaga` com `processo_id`.

Os atalhos do painel enviam um pedido com as linhas `ID do processo:` e `Arquivo oficial:`. Use esse ID como identidade da seleção. Confirme a seleção e o caminho oficial com `detalhar_vaga`.

Leia o processo e as fontes pertinentes. Para avaliar, siga [Busca e triagem](references/busca-e-triagem.md). Para preparar material de candidatura, siga [Candidaturas](references/candidaturas.md). Para preparar entrevista, siga [Entrevistas](references/entrevistas.md) e trabalhe na conversa, criando ou atualizando um plano quando a pessoa pedir a edição. Os atalhos mantêm as autorizações abaixo.

## Gestão de processos

No painel, use os formulários de cadastro, edição e eventos. Agentes usam somente as operações MCP `criar_vaga`, `atualizar_vaga` e `registrar_evento` para toda gravação autorizada em registros oficiais. Para editar ou registrar evento, obtenha ID e revisão com `detalhar_vaga` e informe a evidência. Se houver conflito, confira a nova versão antes de tentar novamente. Se o MCP ou a operação necessária estiver indisponível, informe a lacuna e deixe o registro oficial intacto. Consulte o [guia de gestão de oportunidades](../../README.md#gestão-de-oportunidades).

No cadastro, comece em `identificada` e reúna no dossiê a descrição da vaga, as fontes e as informações pertinentes já disponíveis. Registre as lacunas e a próxima ação. O levantamento, a avaliação e a preparação fazem parte de `identificada`. Para avançar, confira `transicoes_status` e use `mudancas.status` com evidência. Guarde os motivos e fatos do processo nos eventos.

Ao montar o dossiê, siga o [registro da descrição da vaga](references/busca-e-triagem.md#registro-da-descrição), registre o [benchmark salarial](references/benchmark-salarial.md) e inclua em `avaliacao.md` os achados e limites da [pesquisa de clima](references/clima-organizacional.md). Para corrigir o título, use `mudancas.titulo` sem trocar o ID. Para editar a disponibilidade de inscrição, use `mudancas.disponibilidade_inscricao` e a evidência em `mudancas.fonte_disponibilidade_inscricao`.

Descrições de vaga, avaliações, currículos, planos de entrevista e portfólio continuam editáveis. Mantenha uma versão de trabalho de cada material e use arquivos temporários fora do dossiê para prévias, logs e cópias para upload. Preserve versões enviadas e a revisão prévia exigida para submissão.

Para buscar novas vagas ou acompanhar retornos de uma vaga por e-mail, siga [Monitoramento por e-mail](references/monitoramento-email.md). Use os critérios da pessoa em `estrategia/referencias-candidaturas.md`, em `estrategia/objetivos.md` ou em outra fonte indicada por ela. Quando houver pedido de ativação, configure a recorrência pela ferramenta nativa do Codex.

Para encontrar vagas na internet ou cadastrar anúncios selecionados, siga [Pesquisar vagas na web](references/busca-vagas.md). Para preparar alertas do LinkedIn, siga [Alertas do LinkedIn](references/busca-linkedin.md). Para gerar um texto copiável para o Dot, siga [Atualizar o monitor do Dot](references/atualizar-monitor-dot.md).

Para montar ou atualizar o portfólio a partir de arquivos de projeto, apresentações, imagens, vídeos ou áudios exportados, siga [Portfólio a partir de evidências](references/portfolio.md). Consulte as evidências pertinentes e o índice de portfólio quando houver para localizar o caso e preservar a organização já adotada.

## Uma vaga por chat

Use um chat por vaga ao cadastrar, avaliar ou acompanhar uma oportunidade específica. Identifique a vaga pelo ID do processo ou pelo anúncio confirmado antes do cadastro. Se o chat já estiver dedicado a outra vaga, sugira outro chat e preserve o título, inclusive quando a empresa for a mesma.

Ao assumir a vaga no chat ou por um atalho do painel, consulte `detalhar_vaga`. Para um cadastro novo, use o retorno confirmado de `criar_vaga`. Use o campo `titulo_chat` como título do próprio chat do Codex. Chame a ferramenta nativa `set_thread_title` passando apenas `title`.

O título segue `candidatura - <empresa> | <cargo> - <status>`, todo em minúsculas, com espaços no lugar de pontos, traços e barras verticais que já venham nos nomes. Por exemplo, `candidatura - empresa | eng lead - entrevistas`. Use o sufixo de status fornecido em `titulo_chat`. O status `candidatura-enviada` aparece como `enviada`.

O Codex Desktop aceita até 60 unidades UTF-16 no título gravado, incluindo espaços e separadores. Preserve `candidatura - `, ` | ` e ` - <status>` por inteiro. Quando exceder o limite, abrevie apenas a empresa e o cargo, mantendo ambos reconhecíveis, como `engineering` para `eng`. Antes do cadastro, use a empresa e o cargo confirmados no anúncio para identificar a conversa. Acrescente o sufixo com o status quando houver dossiê.

Atualize o título do chat dedicado quando uma mudança confirmada alterar o `titulo_chat`. Use o novo valor retornado pelo MCP, que recalcula o espaço do miolo a partir do nome da empresa, do cargo original e do status atual. Uma prévia ou proposta não muda o título por si só. Preserve o título em buscas gerais, consultas de várias vagas ou quando a pessoa tiver pedido um título próprio. Se a ferramenta nativa estiver indisponível, informe o título para a pessoa aplicar.

## Modos de trabalho

| Quando usar | Procedimento |
|---|---|
| Reconhecer entregas, competências, feedbacks ou pontos de atenção em outro projeto | [Evidências](references/evidencias.md): sugerir captura sem desviar a tarefa; registrar quando autorizado |
| Buscar, triar ou avaliar vagas e empresas | [Busca e triagem](references/busca-e-triagem.md), [benchmark salarial](references/benchmark-salarial.md), [pesquisa de clima](references/clima-organizacional.md) e [scoring](references/scoring.md) quando houver informação suficiente |
| Preparar currículo, apresentação, respostas, PDF ou formulário | [Candidaturas](references/candidaturas.md), com matriz antes da edição e resumo da revisão antes da entrega do currículo. [md-to-cv](../md-to-cv/SKILL.md) para gerar PDF |
| Acompanhar candidaturas e retornos | [Continuidade](#continuidade) e [gestão de oportunidades](../../README.md#gestão-de-oportunidades) |
| Desenvolver posicionamento ou preparar entrevistas | [Entrevistas](references/entrevistas.md) para planos por vaga, vínculo no mapa geral, perguntas, simulação, transcrição e feedback; [limites LinkedIn](references/linkedin-boundaries.md) para perfil e conteúdo público |

Antes de criar ou otimizar um currículo pelo chat, pelo painel ou como parte de uma candidatura, leia `CARREIRA_DIR/estrategia/referencias-candidaturas.md`. Quando esse material faltar ou ainda for um modelo sem dados, consulte `CARREIRA_DIR/estrategia/objetivos.md`, se existir. Use as diretrizes da pessoa para escolher os destaques, inclusive a ênfase em liderança e trabalho técnico quando houver orientação sobre esses pontos. Se as fontes de estratégia estiverem indisponíveis, informe a lacuna e siga as preferências explícitas da conversa e as evidências disponíveis.

Para candidaturas, siga a [ordem de trabalho](references/candidaturas.md). Consulte evidências, revise currículo e carta em Markdown, gere e confira o PDF, revise o formulário com a pessoa e registre o envio quando confirmado. Execute as etapas autorizadas e releia os materiais após edições manuais.

Para perfil e conteúdo, preserve a voz da pessoa, sustente o posicionamento com evidências e trate alterações públicas como ação distinta da redação. Não prometa aprovação, ranking de busca ou resultado de ATS. Só consulte referências dos modos efetivamente acionados. Antes de apresentar prosa nova ou revisada de posicionamento, candidatura ou preparação de entrevista, aplique [humanizer](../humanizer/SKILL.md) em modo embutido.

## Autorização, persistência e ferramentas

- Análise ou proposta pedida no chat não implica edição de arquivos. Uma solicitação de preparar uma candidatura completa inclui criar e atualizar os documentos necessários do dossiê, incluindo PDF quando necessário ao formulário, sem confirmar novamente cada arquivo.
- Atualização autorizada de um documento inclui as alterações necessárias dentro desse escopo. Preservar material enviado e trabalho do usuário; a autorização não se estende automaticamente ao perfil, a todos os currículos ou a outros projetos.
- Captura incidental exige autorização para gravar, salvo quando já houver autorização aplicável ao registro. Registrar evidência não autoriza incorporá-la ao perfil, currículo ou conteúdo público.
- Antes de operar navegador ou conector, confirme a ferramenta disponível e leia suas instruções. Não prometa controle do Chrome sem verificá-lo. Use fontes públicas ou material fornecido quando não houver acesso apropriado.
- Formulários externos podem ser preenchidos quando autorizados e permitidos pelas ferramentas. Submissão exige revisão e autorização da pessoa para o envio. Respeite pedidos de upload manual, recusas de ferramenta e restrições da plataforma.
- Não envie mensagens a recrutadores nem publique ou altere sinalização pública de busca sem autorização explícita. Operações no LinkedIn seguem [seus limites específicos](references/linkedin-boundaries.md); autorização de candidatura não equivale a autorização para automação irrestrita da plataforma.

## Avaliação determinística

Com descrição suficiente, proponha dimensões e justificativas conforme [scoring](references/scoring.md) e execute `SKILL_DIR/scripts/validate_score.py` pelo caminho absoluto. Use caminhos absolutos para a entrada e `--output`. Se usar caminhos relativos, eles partem do diretório atual. Use saída nova ou temporária validada antes de substituir um resultado dentro de uma atualização autorizada.

Use apenas `final_score`, `label` e `disqualified` devolvidos pelo script. Guarde o resultado autorizado em `avaliacao-validada.json` junto de `avaliacao.md`. Sem informação suficiente, registre `informacao_insuficiente`, lacunas e fontes, sem nota. Preserve a versão anterior quando reavaliar. A nota expressa aderência aos objetivos. Mantenha separadas as notas das fontes de pesquisa de clima.

## Continuidade

Antes de agir, leia o processo existente e compare o alerta recebido com os eventos e fontes: um lembrete não prova nova pendência. Mensagem sem cargo e possível duplicação ficam em `monitoramento/triagem.md` até associação confirmada. Use IDs e caminhos permanentes; o mês não cria outra candidatura.

Registre mudanças confirmadas e autorizadas pelo [MCP](#gestão-de-processos). O painel do plugin consulta os processos oficiais e usa `painel-vagas.md` como índice de ordem. Preserve a curadoria manual no Markdown. Consulte o [guia de gestão](../../README.md#validação-painel-markdown-e-relatórios) para validação e relatórios mensais.

Guardar próximo passo ou data de revisão não agenda monitoramento. Quando houver pedido explícito de recorrência, use a capacidade de agendamento disponível e informe o que de fato foi configurado. `archive/` contém legado e fontes históricas, não instruções operacionais; consulte dossiês antigos quando houver pedido de histórico ou comparação.
