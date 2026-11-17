# Posicionar Carreira

Plugin local para cadastrar vagas, acompanhar processos e preparar currículos, candidaturas e entrevistas no Codex. Os dados ficam em uma pasta da pessoa que usa o plugin. Este repositório inclui uma base fictícia e uma vaga para experimentar.

## Instalar no Windows

Extraia o ZIP ou clone este repositório e abra o PowerShell na raiz da pasta. Você precisa do Codex desktop e do Python 3.10 ou posterior disponível como `python`.

```powershell
python -m pip install -r requirements.txt
codex plugin marketplace add .
codex plugin add posicionar-carreira@carreira-local
```

## Verificar e preparar a base

1. No Codex desktop, abra uma conversa local e selecione **Posicionar Carreira** do catálogo **Carreira local**.
2. Envie **“Abra as boas-vindas de Posicionar Carreira.”** A tela mostra a pasta em uso, os arquivos encontrados e quais fluxos ainda precisam de dados.
3. Se você ainda não tem base, escolha uma pasta existente fora do repositório e informe o caminho absoluto. Peça para preparar a pasta e indique se quer modelos de perfil, objetivos e preferências, currículo ou portfólio. O preparo cria a pasta `oportunidades/` e os modelos escolhidos, preserva arquivos existentes e mantém a pasta em uso. Para passar a usar a pasta nova, siga [Usar uma pasta própria](#usar-uma-pasta-própria).

Se a conversa não exibir a tela, peça **“Verifique a configuração da minha carreira.”**

## Abrir o painel de vagas

1. No Codex desktop, abra uma conversa local.
2. Selecione **Posicionar Carreira** do catálogo **Carreira local**.
3. Envie **“Abra o painel de vagas.”**

No painel **Vagas**, você pode filtrar os processos, usar **Nova vaga** para cadastrar uma oportunidade ou pedir ao agente para **Pesquisar vagas na web**. Ao selecionar uma vaga, você vê a etapa, a disponibilidade da inscrição, a próxima ação, o histórico e os materiais. Pelo detalhe, pode editar o processo, corrigir o título mantendo o mesmo dossiê, registrar um evento, preparar uma candidatura ou entrevista e abrir o currículo em Markdown ou PDF, quando disponível.

Para experimentar, [instale a base fictícia](#ler-o-exemplo-da-zelda) e abra **Conselho de Rotas de Hyrule — Cartógrafa de Rotas**. Os botões do currículo abrem os arquivos fictícios nos aplicativos associados no Windows. Você também pode registrar um evento de teste.

Use um chat por vaga que quiser acompanhar. Depois de cadastrar uma vaga pelo painel, clique em **Usar vaga neste chat** para iniciar a conversa com ela. Ao trabalhar na vaga, o agente dá ao chat um título como `candidatura conselho de rotas de hyrule - em preparação` e atualiza o status conforme o processo avança.

O painel depende do suporte a MCP Apps na conversa. Se a interface não aparecer, peça **“Liste minhas vagas”** ou **“Mostre os detalhes da vaga de Cartógrafa de Rotas”** no chat. Para gerar novos PDFs, instale as dependências indicadas na [skill de conversão](plugins/posicionar-carreira/skills/md-to-cv/SKILL.md).

## Dashboard

No chat do Codex, selecione **@Posicionar Carreira** e envie **Dashboard**. A visão geral mostra o total de vagas, quantas estão abertas, pausadas ou encerradas, as etapas das abertas e pausadas e os resultados dos processos encerrados.

Use **Atualizar** para reler a base local. Para filtrar vagas, abrir dossiês ou editar processos, clique em **Ver vagas**. No painel detalhado, o botão **Dashboard** abre a visão geral.

## Usar uma pasta própria

Escolha uma pasta de dados fora do clone. `CARREIRA_ROOT` e `~/.config/posicionar-carreira/data-root.txt` apontam diretamente para a pasta que contém `oportunidades/`. O exemplo abaixo prepara uma pasta nova e grava a configuração persistente. Se já houver um seletor, guarde o conteúdo atual antes de trocá-lo.

```powershell
$pastaCarreira = Join-Path $env:USERPROFILE 'MinhaCarreira'
python -B exemplo/inicializar.py --carreira-root $pastaCarreira
$seletor = Join-Path $env:USERPROFILE '.config/posicionar-carreira/data-root.txt'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $seletor) | Out-Null
Set-Content -LiteralPath $seletor -Value $pastaCarreira -Encoding utf8
python -B plugins/posicionar-carreira/server/servidor.py --carreira-root
```

Se você já usava a edição anterior, continue com a mesma pasta. `POSICIONAR_CARREIRA_ROOT` e `~/.posicionar-carreira-raiz` continuam apontando para a pasta acima de `carreira/`. A edição também reconhece a base existente em `~/PosicionarCarreira/carreira`. Confira qual pasta está em uso antes de cadastrar ou editar vagas. As variáveis de ambiente têm prioridade sobre os arquivos seletores. [Ordem de resolução e opções de configuração](plugins/posicionar-carreira/README.md#fonte-local)

Mantenha a base pessoal fora do repositório. Dentro de cada dossiê, `processo.md` contém estado, etapa, resultado, histórico e próxima ação. O painel e o chat usam os mesmos registros. Os materiais enviados ficam em `envios/`. Os atalhos de preparação levam o contexto da vaga à conversa. Revise qualquer material antes de autorizar submissão.

## Preparar seus dados no chat

Selecione **Posicionar Carreira** e peça **“Quero montar minha base de carreira do zero. Me guie pelo perfil, objetivos, currículo e portfólio.”** Você pode começar com um currículo que já usa ou descrever sua experiência na conversa. A skill vai pedir o que falta e mostrar os rascunhos antes de gravar. Você também pode começar cadastrando uma vaga pelo painel e completar o perfil depois.

| Material | O que incluir |
|---|---|
| Perfil profissional | Histórico, responsabilidades, competências e resultados que você consegue sustentar. |
| Objetivos | Cargos de interesse, tipo de trabalho, localização, modalidade e critérios para escolher vagas. |
| Currículo base | Versão geral revisada, com os dados de contato que você quer usar em candidaturas. |
| Evidências e portfólio | Projetos que você pode apresentar, sua contribuição e resultados verificáveis. Indique materiais confidenciais e o que pode ser divulgado. |
| Primeiras vagas | Empresa, cargo e fonte para cada vaga que quiser acompanhar. |

O modelo de objetivos e preferências usa `estrategia/referencias-candidaturas.md`. Você também pode continuar usando o `estrategia/objetivos.md` da edição anterior. A conversa ajuda a organizar o conteúdo pessoal conforme você fornece e aprova os dados.

## Ler o exemplo da Zelda

Para instalar a base fictícia, rode `python -B exemplo/inicializar.py --com-exemplo` com a base de destino vazia. Em uma primeira instalação, o exemplo fica em `~/PosicionarCarreira/carreira`. Se você já usa uma base, instale a demonstração em outra pasta vazia com `--carreira-root <pasta-do-exemplo>`. Para ver a demonstração no painel, configure essa pasta como indicado em [Usar uma pasta própria](#usar-uma-pasta-própria).

Na demonstração, Zelda de Hyrule prepara uma candidatura a Cartógrafa de Rotas. Seu projeto no Arquivo Real organiza cadernos de remessas da Vila Kakariko e da Cidade Goron. Perfil, portfólio e currículo reaproveitam as evidências desse trabalho inventado. [Inspiração em The Legend of Zelda: Ocarina of Time](https://www.nintendo.com/pt-br/store/products/the-legend-of-zelda-ocarina-of-time-switch-2/)

| Material | Como usar como referência |
|---|---|
| [Perfil profissional](exemplo/base/perfil/perfil-profissional.md) | Organize a trajetória, as competências e os projetos. Vincule a [evidência](exemplo/base/perfil/evidencias/mapa-de-entregas-de-hyrule.md) que sustenta cada afirmação relevante. |
| [Objetivos](exemplo/base/estrategia/objetivos.md) | Registre o que você busca, o que é requisito e o que ainda pode negociar. |
| [Portfólio](exemplo/base/portfolio/mapa-de-entregas-de-hyrule.md) | Apresente o problema, sua contribuição, como você conferiu o resultado e quais limites permanecem. |
| [Currículo base](exemplo/base/curriculos/base.md) | Selecione os fatos e as entregas que podem ser reaproveitados em candidaturas. |
| [Dossiê da vaga](exemplo/modelo/processo.md) | Veja como o [anúncio](exemplo/modelo/vaga.md) orienta a [avaliação](exemplo/modelo/avaliacao.md), a [pesquisa salarial](exemplo/modelo/benchmark-salarial.md), o [currículo específico](exemplo/modelo/curriculo.md) e a [carta](exemplo/modelo/carta.md). |

Use a organização dos exemplos e substitua o conteúdo pelas suas fontes. Você pode pedir ao plugin para revisar um documento de cada vez e apontar o que ainda falta comprovar.

## Pesquisar remuneração e preparar uma candidatura

Ao mapear uma vaga pelo chat, o plugin pesquisa a faixa anunciada e referências de mercado e registra as fontes em `benchmark-salarial.md`. A pesquisa indica o que falta confirmar e usa os critérios da sua base. O exemplo fictício inclui esse arquivo para você consultar nos materiais do dossiê. [Pesquisa salarial](plugins/posicionar-carreira/skills/posicionar-carreira/references/benchmark-salarial.md)

Ao montar o dossiê ou usar **Avaliar vaga**, o agente também pesquisa o clima da empresa em avaliações públicas de funcionários, como Glassdoor e Indeed, e em outras fontes pertinentes. A avaliação registra os achados, seus limites e perguntas para a entrevista. [Roteiro de pesquisa de clima](plugins/posicionar-carreira/skills/posicionar-carreira/references/clima-organizacional.md)

Para preparar uma candidatura, peça a revisão das evidências, do currículo e da carta. O plugin pode gerar um PDF com nome descritivo, conferir o conteúdo e preparar as respostas para sua revisão. O envio requer sua autorização. [Fluxo de candidatura](plugins/posicionar-carreira/skills/posicionar-carreira/references/candidaturas.md)

Para criar ou otimizar o currículo de uma vaga, use **Preparar currículo** no painel ou peça no chat. O agente mostra quais evidências sustentam os requisitos antes de editar, compara o resultado com a versão anterior e registra as lacunas e o motivo para encerrar. Se a versão atual já estiver adequada, a revisão pode terminar preservando o texto. [Ciclo de otimização](plugins/posicionar-carreira/skills/posicionar-carreira/references/candidaturas.md#ciclo-de-otimização-por-vaga)

Você também pode pedir ao **Humanizer** que revise um texto mantendo a voz e os fatos do original. Para usar suas preferências de escrita, indique-as no pedido ou forneça uma amostra. [Humanizer](plugins/posicionar-carreira/skills/humanizer/SKILL.md)

## Preparar ou revisar entrevistas

Use **Preparar entrevista** no detalhe da vaga para ensaiar perguntas e revisar casos. Você também pode fornecer uma gravação ou transcrição e pedir uma análise das respostas reais. O agente preserva o material original, identifica trechos incertos e apresenta sugestões de melhoria à parte. [Roteiro de entrevistas](plugins/posicionar-carreira/skills/posicionar-carreira/references/entrevistas.md)

## Montar ou atualizar o portfólio

Coloque na pasta do projeto um PowerPoint, um vídeo de palestra ou demonstração, uma captura de tela ou um áudio exportado. No chat com **Posicionar Carreira**, indique o arquivo e peça para transformar o material em um caso ou atualizar um que já exista.

A skill consulta o portfólio, examina as fontes com as ferramentas disponíveis e separa contexto, contribuição pessoal e resultado verificável. O caso indica de onde vêm as afirmações e sinaliza o que ainda precisa de confirmação. Você pode revisar o rascunho ou pedir que ele seja salvo na base local. A publicação depende de um pedido separado. [Fluxo de portfólio](plugins/posicionar-carreira/skills/posicionar-carreira/references/portfolio.md)

Para guardar uma entrega, decisão ou feedback, peça um registro com contexto, contribuição, fonte e limites. Você decide depois onde aproveitar esse material no perfil, no currículo ou no portfólio. [Roteiro de evidências](plugins/posicionar-carreira/skills/posicionar-carreira/references/evidencias.md)

## Pesquisar vagas na web

No painel, use **Pesquisar vagas na web**, ou peça a pesquisa no chat. O agente usa os objetivos da sua base para consultar páginas de carreira, portais como Vagas.com, Gupy e Indeed e fontes específicas da área. Pode navegar pelos anúncios públicos quando o navegador estiver disponível. Você recebe links, aderência, situação da inscrição e pontos a esclarecer. Peça o cadastro das vagas que escolher. [Fluxo de pesquisa](plugins/posicionar-carreira/skills/posicionar-carreira/references/busca-vagas.md)

## Monitorar vagas por e-mail

No painel, escolha **Monitorar novas vagas** para buscar alertas compatíveis com seus objetivos, ou **Monitorar esta vaga** no dossiê para acompanhar retornos daquele processo. Você também pode pedir diretamente no chat. Conecte a conta de e-mail que quer consultar e indique a frequência e o horário. O Codex usa o conector e o agendamento do próprio aplicativo.

A busca de novas vagas usa seu perfil e seus objetivos locais. O acompanhamento de um processo usa o dossiê para distinguir convites, prazos e retornos, inclusive prazos já conhecidos sem e-mail novo. A tarefa avisa no chat com a fonte e o próximo passo sugerido. O cadastro de vagas e as alterações no dossiê continuam disponíveis quando você pedir.

Para uma tarefa com arquivos locais, deixe o computador ligado e o aplicativo aberto. Confira a tarefa e suas execuções na área de agendamentos do aplicativo. [Tarefas agendadas](https://learn.chatgpt.com/docs/automations)

### Receber alertas do LinkedIn e acompanhar no Dot

No painel, use **Planejar busca no LinkedIn** para obter termos e filtros de acordo com seus objetivos. Abra a busca no LinkedIn e ative o alerta por e-mail. Você também pode trazer anúncios selecionados ao chat para análise e pedir o cadastro das vagas que quiser acompanhar. [Alertas de vagas do LinkedIn](https://www.linkedin.com/help/linkedin/answer/a508396)

Se você já usa o Dot, peça **“Gere um bloco para copiar e atualizar meu monitor de vagas no Dot.”** Informe o texto atual e o ajuste que quer fazer. A skill usa os critérios confirmados e entrega o texto para você revisar e colar na conversa do Dot. Uma vaga de interesse pode ser encaminhada em um pedido separado ao Dot, se o computador com o Codex estiver conectado. [Dot e computadores conectados](https://learn.chatgpt.com/docs/dots/computers-and-apps#connect-your-computers)

## Validar, gerar painel Markdown e criar relatórios

Com a base configurada, rode os comandos abaixo a partir da raiz do repositório. Use `--root <pasta-de-dados>` se quiser apontar diretamente para outra base.

```powershell
python -B plugins/posicionar-carreira/server/gestao_vagas.py validar
python -B plugins/posicionar-carreira/server/gestao_vagas.py gerar
python -B plugins/posicionar-carreira/server/gestao_vagas.py relatorio --mes AAAA-MM
```

`validar` confere os processos e links locais. `gerar` atualiza o arquivo `painel-vagas.md` e preserva a seção **Revisões recebidas**. `relatorio` cria uma fotografia mensal com candidaturas e eventos. [Regras dos relatórios](plugins/posicionar-carreira/README.md#validação-painel-markdown-e-relatórios)

## Operações locais em lote

Use `python -B plugins/posicionar-carreira/server/lote.py --detalhar empresa/local-001` para consultar o registro e sua revisão. A entrada JSON do lote é uma lista de objetos com `ferramenta` (`criar_vaga`, `atualizar_vaga` ou `registrar_evento`) e `argumentos`, os mesmos da ferramenta MCP. Uma atualização recebe o ID, a revisão, a descrição, a fonte e os campos em `mudancas`.

```powershell
python -B plugins/posicionar-carreira/server/lote.py entrada.json
python -B plugins/posicionar-carreira/server/lote.py entrada.json --aplicar
```

A primeira chamada mostra a prévia. Use `--aplicar` para gravar após revisar. Para repetir apenas falhas, salve a saída como JSON, confira os itens e use `--somente-falhas` com esse arquivo. Releia qualquer processo em conflito antes de reaplicar. Para operações pedidas ao agente no chat, o plugin usa as ferramentas MCP.

## Testes

```powershell
python -X utf8 -B -m unittest discover -s tests -v
python -X utf8 -B -m unittest discover -s plugins/posicionar-carreira/tests -v
```

Os testes de navegador usam Playwright para Python e Chrome.
