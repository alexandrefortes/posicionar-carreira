# Posicionar Carreira

Plugin local do Codex para cadastrar vagas e acompanhar processos seletivos. Abra uma vaga para consultar histórico, materiais e próximos passos, editar os campos oficiais, registrar um evento, encerrar ou reabrir o processo. Os atalhos de avaliação, currículo, candidatura e entrevista levam o ID da vaga e o caminho do processo à conversa.

## Instalar e abrir

Use Python 3.10 ou posterior. Na pasta do plugin, instale a [dependência PyYAML](requirements-gestao-vagas.txt) com `python -m pip install -r requirements-gestao-vagas.txt`. O Codex precisa encontrar esse Python pelo comando `python`. Configure uma pasta de dados conforme [Fonte local](#fonte-local). Registre o diretório do marketplace distribuído e instale o plugin.

Ao compartilhar o plugin, envie o marketplace e a pasta do plugin. Cada pessoa configura sua própria pasta de dados.

```powershell
codex plugin marketplace add "<pasta-do-marketplace>"
codex plugin add posicionar-carreira@carreira-local
```

Abra uma conversa local no Codex desktop, selecione **Posicionar Carreira** e peça **Abra as boas-vindas de Posicionar Carreira**. Essa tela orienta a verificação da base e o acesso ao painel. Se o cliente não exibir MCP Apps, peça **Verifique a configuração da minha carreira** e continue pelo texto. Quando a base estiver pronta, peça **Abra o painel de vagas** ou consulte a lista e os detalhes pelo chat.

O painel depende de MCP Apps habilitado na conversa e disponível na janela do desktop. O recurso experimental `enable_mcp_apps` do Codex pode variar por conversa. A consulta em texto está disponível pelas ferramentas `listar_vagas` e `detalhar_vaga`.

## Fonte local

Escolha uma pasta existente fora do plugin para guardar seus dados. Salve o caminho absoluto da pasta de dados em uma única linha de `~/.config/posicionar-carreira/data-root.txt`. A pasta de dados contém `oportunidades/`. A resolução segue esta ordem:

1. O caminho explícito passado à ferramenta que aceita `pasta` ou ao comando que aceita `--root`.
2. `CARREIRA_ROOT`, que aponta diretamente para a pasta de dados.
3. `POSICIONAR_CARREIRA_ROOT` e depois `PAPAO_ROOT`, que apontam para a pasta que contém `carreira/`.
4. `~/.config/posicionar-carreira/data-root.txt`, com o caminho direto da pasta de dados.
5. `~/.posicionar-carreira-raiz`, com o caminho da pasta que contém `carreira/`.
6. `~/PosicionarCarreira/carreira`, se já existir.

Na atualização de uma edição anterior, use a mesma base e confirme a pasta em uso pelas boas-vindas ou com `python -B server/servidor.py --carreira-root`. O comando legado `--raiz` continua disponível para quem usava uma pasta que contém `carreira/`.

`verificar_configuracao` consulta a base configurada ou recebe um caminho absoluto opcional em `pasta`. A ferramenta informa quais materiais e fluxos estão prontos. Se você autorizar a preparação de uma pasta, `inicializar_carreira` recebe seu caminho absoluto em `pasta` e cria `oportunidades/`, se necessário. Isso basta para cadastrar vagas. A inicialização preserva arquivos existentes e a configuração do caminho.

Quando quiser começar a reunir dados profissionais, solicite modelos iniciais. O campo opcional `modelos` aceita `perfil`, `preferencias`, `curriculo` e `portfolio`. Revise os rascunhos com seus próprios dados antes de usá-los. A verificação aceita `estrategia/objetivos.md` quando falta um arquivo preenchido de objetivos e preferências em `estrategia/referencias-candidaturas.md`. Evidências, currículos, objetivos e materiais de portfólio podem ser acrescentados à base conforme cada fluxo exigir.

Para cadastrar vagas com seu nome como responsável, salve um `config.json` na pasta de dados com `{ "responsavel": "Pessoa Exemplo" }`, usando seu nome no lugar do exemplo. Sem esse campo, o cadastro usa `titular`. As opções `assistente` e `empresa` representam os outros responsáveis do processo.

```powershell
python -B server/dados.py
```

O comando mostra a pasta de dados configurada. Se existir um `painel-vagas.md` nessa pasta, a lista segue a ordem de seus links. Vagas fora do índice aparecem ao final, por atualização. O painel do plugin lê estado, etapa e resultado do registro oficial e mantém intacto o Markdown de curadoria.

Para experimentar outra base pela configuração em arquivo, guarde uma cópia de `data-root.txt` se já existir e troque a linha pelo caminho absoluto de uma pasta de teste. Confira a pasta indicada pela verificação e reabra o painel antes de cadastrar qualquer vaga. O aplicativo pode permanecer aberto porque o plugin relê o arquivo a cada consulta. Ao terminar, restaure a cópia ou retire o arquivo criado só para o teste. A troca pelo arquivo funciona quando as variáveis de ambiente estão ausentes.

No detalhe, **Abrir currículo em Markdown** abre a fonte editável no aplicativo associado a `.md` pelo Windows. **Abrir currículo em PDF** abre o arquivo já gerado no visualizador padrão. Cada botão aparece quando o arquivo correspondente é identificado no dossiê. Se a única versão identificada estiver em `envios/`, o botão a identifica como enviada.

**Monitorar novas vagas** leva ao chat a configuração de uma busca por e-mail conforme seus critérios. **Monitorar esta vaga** leva o ID do dossiê para acompanhar retornos daquele processo. Use a conta de e-mail conectada e o agendamento nativo do Codex. Tarefas com arquivos locais precisam do computador ligado e do aplicativo aberto. [Tarefas agendadas](https://learn.chatgpt.com/docs/automations)

**Pesquisar vagas na web** pede ao agente que encontre oportunidades usando seus objetivos e perfil. Ele consulta portais relevantes e páginas de carreira. Pode abrir os anúncios no navegador para conferir os detalhes. Os resultados trazem links, aderência, situação da inscrição e pontos a esclarecer. Peça o cadastro das vagas que escolher. [Fluxo de pesquisa](skills/posicionar-carreira/references/busca-vagas.md)

**Planejar busca no LinkedIn** prepara termos e filtros para configurar o alerta oficial por e-mail. [Alertas de vagas do LinkedIn](https://www.linkedin.com/help/linkedin/answer/a508396)

Se já usa o Dot, peça ao plugin um texto copiável para atualizar o monitor e revise antes de colar na conversa do Dot. Informe o texto atual e o que quer mudar. Quando gostar de uma vaga do monitor, peça separadamente ao Dot para encaminhá-la a uma conversa local do Codex. [Dot e computadores conectados](https://learn.chatgpt.com/docs/dots/computers-and-apps#connect-your-computers)

## Montar ou atualizar o portfólio

Coloque na pasta do projeto a apresentação, o vídeo, a captura ou o áudio exportado que quiser usar. No chat com o plugin, indique o material e peça para criar ou atualizar um caso. A skill confere o portfólio existente, usa as ferramentas disponíveis para examinar o material e referencia o slide, o trecho ou o arquivo que sustenta cada afirmação. O caso fica na base local e a publicação depende de pedido próprio.

A geração de currículos em PDF usa os [requisitos da skill md-to-cv](skills/md-to-cv/SKILL.md). O [fluxo de entrevistas](skills/posicionar-carreira/references/entrevistas.md#entrevista-gravada) trabalha com gravações fornecidas pela pessoa quando houver meios de analisá-las ou transcrevê-las. Dossiês e materiais ficam na pasta de dados configurada.

## Gestão de oportunidades

O registro oficial é `oportunidades/<empresa>/<id>/processo.md` na pasta de dados. Mantenha o mesmo ID e dossiê ao mudar de mês, corrigir o título ou encerrar o processo. Compare IDs externos, URLs, empresa, cargo e escopo antes de cadastrar. Uma nova requisição comprovada pode ter seu próprio dossiê. Recibos sem associação segura ficam em `monitoramento/triagem.md`, com a entrada original preservada.

No painel, use os formulários de cadastro, edição e eventos. Agentes usam exclusivamente as operações MCP abaixo para gravações autorizadas no registro oficial, inclusive quando trabalham em várias vagas.

- `criar_vaga` cadastra uma oportunidade com empresa, título e fonte. Informe o ID externo quando confirmado ou deixe a ferramenta atribuir um ID local.
- `atualizar_vaga` altera os campos aceitos em `mudancas` e registra seus valores anteriores e atuais no evento. Use `mudancas.titulo` para corrigir o título mantendo o mesmo ID e caminho.
- `registrar_evento` acrescenta evidência ou uma nota ao histórico. Para corrigir informação anterior, registre a correção no histórico e ajuste os campos atuais quando aplicável.

Para atualizar ou registrar um evento, use o ID e a revisão retornados por `detalhar_vaga`. Informe descrição, fonte e data do acontecimento quando conhecida. Se houver conflito, recarregue e confira as mudanças antes de tentar novamente. Se o MCP ou a operação necessária estiver indisponível, informe a lacuna e deixe o registro oficial intacto. Descrições de vagas, avaliações, currículos e planos de entrevista são materiais editáveis do dossiê e aparecem no detalhe quando armazenados nele.

Estado indica se o processo está aberto, pausado ou encerrado. Etapa registra o avanço real e resultado é obrigatório ao encerrar. Preserve a etapa alcançada e o histórico. Sem resposta ou com feedback positivo, mantenha o estado sustentado pela evidência. Confirme candidatura só com evidência de envio e preserve em `envios/` as versões exatas identificadas como submetidas.

Use URLs ou caminhos de arquivos relativos à pasta de dados para as fontes. Envie datas conhecidas em `AAAA-MM-DD` e use `null` para datas desconhecidas. `registrado_em` indica quando o evento entrou no histórico. Prazo informado exige `fonte_prazo`. `revisar_em` sugere uma revisão local.

A disponibilidade da inscrição tem fonte própria e admite `aberta_verificada`, `nao_confirmada` ou `anuncio_expirado`. Informe `fonte_disponibilidade_inscricao` ao definir ou mudar esse status. Envie `disponibilidade_inscricao: null` para limpar os dois campos. A disponibilidade pública descreve o anúncio e não comprova acesso autenticado, envio ou encerramento do processo pessoal.

O painel Markdown mostra os grupos do plano atual para processos abertos sem envio confirmado. Os valores de `grupo_plano_atual` identificam as vagas a avaliar (`plano_modalidade_compativel`) e as que exigem esclarecimento (`plano_esclarecimento`). `lote_plano`, `fonte_plano` e os demais campos de evidência preservam a origem da classificação.

### Avaliação e remuneração

O painel Markdown lê o score de `avaliacao-validada.json` sem recalcular. Mantenha esse resultado coerente com `avaliacao.md`, que reúne aderência, cultura, condições, recomendação e links para pesquisas datadas. Para reavaliar, siga a [avaliação determinística da skill](skills/posicionar-carreira/SKILL.md#avaliação-determinística). Para avaliar a empresa, siga o [roteiro de pesquisa de clima](skills/posicionar-carreira/references/clima-organizacional.md).

Ao mapear uma vaga, siga o [procedimento de pesquisa salarial](skills/posicionar-carreira/references/benchmark-salarial.md). O painel Markdown mostra a síntese e o link para vagas abertas e pausadas e sinaliza pesquisa pendente quando o arquivo está ausente.

### Validação, painel Markdown e relatórios

A partir da pasta do plugin, use os comandos abaixo para ler os dossiês. O padrão é a pasta configurada em [Fonte local](#fonte-local). Para usar outra pasta, passe `--root <caminho-absoluto-da-pasta-de-dados>`.

```powershell
python -B server/gestao_vagas.py validar
python -B server/gestao_vagas.py gerar
python -B server/gestao_vagas.py relatorio --mes AAAA-MM
```

`validar` confere registros e destinos de links locais. A validação cobre os arquivos, e URLs externas e âncoras exigem conferência própria. `gerar` valida os registros e substitui apenas o painel Markdown derivado, preservando a seção **Revisões recebidas**. Use a geração deliberadamente, fora de uma sessão de curadoria manual. Os formulários e as ferramentas MCP atualizam a vista do plugin sem depender da geração do Markdown.

`relatorio` cria uma fotografia datada com vagas identificadas, candidaturas confirmadas e eventos do mês. Repetições criam revisões `-r2`, `-r3` e seguintes. `--data AAAA-MM-DD` define a data de referência e o mês selecionado deve ser igual ou anterior a ela. Envios comprovados sem data conhecida entram no total histórico. As contagens mensais exigem data de envio. Pistas e recibos sem associação ficam fora dessas contagens.

## Manutenção humana em lote

Para manutenção humana deliberada, `server/lote.py` usa o mesmo serviço de cadastro, alteração e histórico do MCP. Agentes usam o [fluxo MCP](#gestão-de-oportunidades), inclusive em lote. Na pasta do plugin, consulte a revisão de cada processo antes de montar uma entrada de manutenção.

```powershell
python -B server/lote.py --detalhar empresa/local-001
```

Monte um JSON com uma lista de operações. Use `criar_vaga` com empresa, título e fonte. Para `registrar_evento` ou `atualizar_vaga`, use o ID e a revisão retornados pelo detalhe. Informe a descrição do evento, a fonte e a data quando conhecida. `atualizar_vaga` também recebe os campos que mudam em `mudancas`.

```json
[
  {
    "ferramenta": "atualizar_vaga",
    "argumentos": {
      "processo_id": "empresa/local-001",
      "revisao": "<revisao retornada pelo detalhe>",
      "descricao": "Empresa informou a data da entrevista",
      "fonte": "https://example.org/confirmacao",
      "mudancas": { "etapa": "entrevista_tecnica", "proxima_acao": "Preparar entrevista" }
    }
  }
]
```

```powershell
python -B server/lote.py entrada.json
python -B server/lote.py entrada.json --aplicar > resultado.json
python -B server/lote.py resultado.json --somente-falhas
```

A primeira execução mostra a prévia sem gravar. Aplique após revisar cada item. O relatório identifica operações aplicadas, repetidas, com conflito ou com erro. Para repetir apenas as falhas, revise a lista `falhas` no relatório, consulte de novo os processos em conflito e reconcilie a alteração. Execute com `--somente-falhas --aplicar` quando a prévia das falhas estiver correta. A execução preserva as revisões fornecidas. IDs gerados na prévia de cadastros são provisórios.

## Testes locais

Execute na pasta do plugin.

```powershell
python -X utf8 -B -m unittest discover -s tests -v
```

Os testes usam dossiês sintéticos para operações MCP, validação, geração do painel e relatórios. O teste do painel usa Playwright para Python e Chrome. O navegador executa a interface entregue pelo servidor MCP e um host de teste recebe a mensagem da vaga selecionada.
