# Posicionar Carreira

Cadastre vagas, acompanhe processos e prepare currículos e entrevistas no Codex. Abra uma vaga para ver o histórico, os materiais e a próxima ação. Os atalhos enviam o ID e o caminho do dossiê ao chat.

## Instalar e abrir

1. Na pasta do plugin, instale o PyYAML com `python -m pip install -r requirements-gestao-vagas.txt`. O comando `python` deve usar a versão 3.10 ou posterior.
2. [Configure a pasta de dados](#fonte-local).
3. Registre a pasta do marketplace. Para instalar, use o nome do marketplace registrado. Neste repositório, é `carreira-local`.

```powershell
codex plugin marketplace add "<pasta-do-marketplace>"
codex plugin add posicionar-carreira@carreira-local
```

4. Em uma conversa local do Codex desktop, selecione **Posicionar Carreira** e peça **Abra as boas-vindas de Posicionar Carreira**.
5. Confira a base na tela de boas-vindas. Quando estiver pronta, peça **Abra o painel de vagas**.

Se o painel não aparecer, peça **Verifique a configuração da minha carreira**. A interface requer MCP Apps na janela e na conversa (`enable_mcp_apps`). Use `listar_vagas` e `detalhar_vaga` para consultar pelo chat.

Para compartilhar o plugin, envie as pastas do marketplace e do plugin. Cada pessoa configura a própria base.

### Atualizar uma base anterior à versão 0.8.0

1. Feche o plugin e guarde uma cópia da base.
2. Em cada `oportunidades/<empresa>/<id>/processo.md`, substitua `estado`, `etapa` e `resultado` no cabeçalho YAML por um único `status`. Guarde os valores anteriores no histórico. Preserve as evidências, próximas ações, datas conhecidas e demais conteúdos do dossiê.
3. Escolha o status pela evidência de cada processo.

| Registro anterior | Novo `status` |
|---|---|
| Em andamento, antes do envio | `identificada` |
| `candidatura_enviada` | `candidatura-enviada` |
| Entrevista ou oferta registrada | `entrevistas` ou `oferta`, conforme o último marco |
| Pausa ou triagem | Último marco comprovado |
| `vaga_cancelada` | `cancelada-pela-empresa` |
| `descartado_na_avaliacao` ou `desistencia` | `descartada` |
| `contratado` ou `reprovado` | Mantenha o valor |

4. [Valide a base](#validação-painel-markdown-e-relatórios) antes de reabrir o plugin. Bases novas já usam o formato atual.

## Dashboard

Peça **Dashboard** para ver o total de vagas e a contagem por status, em andamento ou encerradas. **Atualizar** relê a base. **Ver vagas** permite filtrar, consultar e editar dossiês. **Dashboard** volta à visão geral.

## Fonte local

Escolha uma pasta existente fora do plugin para guardar seus dados. Salve o caminho absoluto da pasta de dados em uma única linha de `~/.config/posicionar-carreira/data-root.txt`. A pasta de dados contém `oportunidades/`. A resolução segue esta ordem:

1. O caminho explícito passado à ferramenta que aceita `pasta` ou ao comando que aceita `--root`.
2. `CARREIRA_ROOT`, que aponta diretamente para a pasta de dados.
3. `POSICIONAR_CARREIRA_ROOT` e depois `PAPAO_ROOT`, que apontam para a pasta que contém `carreira/`.
4. `~/.config/posicionar-carreira/data-root.txt`, com o caminho direto da pasta de dados.
5. `~/.posicionar-carreira-raiz`, com o caminho da pasta que contém `carreira/`.
6. `~/PosicionarCarreira/carreira`, se já existir.

Na atualização de uma edição anterior, use a mesma base e confirme a pasta em uso pelas boas-vindas ou com `python -B server/servidor.py --carreira-root`. O comando legado `--raiz` continua disponível para quem usava uma pasta que contém `carreira/`.

`verificar_configuracao` mostra os materiais e fluxos disponíveis. Para conferir outra pasta, passe o caminho absoluto em `pasta`. Autorize `inicializar_carreira` a criar `oportunidades/` para começar a cadastrar vagas. Seus arquivos e a configuração do caminho são preservados.

Para criar rascunhos, peça os `modelos` desejados: `perfil`, `preferencias`, `curriculo` ou `portfolio`. Revise-os com seus dados. A verificação também reconhece `estrategia/objetivos.md` de bases anteriores. Acrescente evidências e materiais conforme precisar.

Para usar seu nome como responsável, salve `{ "responsavel": "Seu nome" }` em `config.json` na pasta de dados. O padrão é `titular`. Os outros responsáveis possíveis são `assistente` e `empresa`.

Na pasta do plugin, confira qual base está em uso:

```powershell
python -B server/dados.py
```

Para testar outra base via `data-root.txt`, deixe as variáveis de ambiente de carreira sem definir. Guarde o arquivo anterior e informe o caminho de teste. Confira a pasta antes de reabrir o painel e cadastrar vagas. O plugin relê o caminho a cada consulta. Ao terminar, restaure o arquivo anterior ou remova o de teste.

## Encontrar e acompanhar vagas

| No painel ou no chat | O que fazer |
|---|---|
| **Pesquisar vagas na web** | Informe seus objetivos. Confira links, aderência, situação da inscrição e dúvidas nos anúncios de portais e páginas de carreira. Peça o cadastro das vagas escolhidas. [Pesquisa de vagas](skills/posicionar-carreira/references/busca-vagas.md) |
| **Planejar busca no LinkedIn** | Use os termos e filtros sugeridos para configurar o [alerta oficial por e-mail](https://www.linkedin.com/help/linkedin/answer/a508396). |
| **Monitorar novas vagas** ou **Monitorar esta vaga** | O primeiro atalho prepara uma busca por e-mail com seus critérios. O segundo inclui o ID da vaga para acompanhar os retornos. Use a conta conectada e o agendamento do Codex. Tarefas com arquivos locais exigem computador ligado e aplicativo aberto. [Tarefas agendadas](https://learn.chatgpt.com/docs/automations) |
| Monitor existente no Dot | Informe o texto atual e a mudança desejada. Revise a sugestão do plugin e cole-a no Dot. Para encaminhar uma vaga a uma conversa local do Codex, faça um pedido separado ao Dot. [Computadores conectados ao Dot](https://learn.chatgpt.com/docs/dots/computers-and-apps#connect-your-computers) |

## Montar ou atualizar o portfólio

Coloque a apresentação, o vídeo, a captura ou o áudio exportado na pasta do projeto. Indique o arquivo no chat e peça para criar ou atualizar um caso no portfólio existente. Cada afirmação deve citar o slide, o trecho ou o arquivo que a sustenta. O caso fica na base local. Peça a publicação separadamente.

## Gestão de oportunidades

Cada vaga tem um registro oficial em `oportunidades/<empresa>/<id>/processo.md`. Mantenha o ID e o caminho ao corrigir o título, mudar de mês ou encerrar o processo. Antes de cadastrar, compare IDs externos, URLs, empresa, cargo e escopo. Uma nova requisição comprovada pode ter outro dossiê. Guarde recibos de associação incerta em `monitoramento/triagem.md` e preserve a entrada original.

Use os formulários do painel ou peça ao agente uma das operações abaixo. O agente grava no registro oficial somente pelo MCP, com autorização, inclusive em lote.

| Operação | Quando usar |
|---|---|
| `criar_vaga` | Informe empresa, título e fonte. O status inicial é `identificada`. Use o ID externo confirmado ou deixe a ferramenta atribuir um ID local. |
| `atualizar_vaga` | Envie os campos em `mudancas`, como `mudancas.status` ou `mudancas.titulo`. O histórico guarda os valores anteriores e atuais. |
| `registrar_evento` | Acrescente uma evidência, nota ou correção. Se a correção mudar um campo atual, atualize-o também. |

**Resolver uma pendência.** Identifique a vaga antes de encerrar a triagem. Ao registrar o evento ou atualizar a vaga, cole a linha completa de `monitoramento/triagem.md` em **Pendência da triagem a encerrar** (`pendencia_triagem`). O plugin registra o fato e a fonte no dossiê e marca a linha como resolvida, com link para o processo. Se a gravação da triagem falhar, repita a operação com a mesma linha e os mesmos dados.

**Usar uma fonte em várias vagas.** Guarde o original uma vez, conforme o assunto: uma mensagem em `monitoramento/entradas/`, uma pesquisa da empresa em `empresas/<empresa>/pesquisas/` ou uma pesquisa de mercado em `estrategia/`. Se o original estiver na web, use a URL. Em cada dossiê, registre o que ele comprova para aquela vaga e use a mesma URL ou caminho em `fonte`. Ao cadastrar vagas com o mesmo anúncio, marque **Esta fonte identifica várias vagas** (`fonte_compartilhada`). Preserve em `envios/` as cópias exatas dos materiais submetidos.

Para editar ou registrar um evento, obtenha o ID e a revisão em `detalhar_vaga`. Informe descrição, fonte e data conhecida do fato. Se houver conflito, confira a revisão atual antes de repetir. Se faltar a operação MCP, o agente informa a limitação e preserva o registro.

Edite a descrição, a avaliação, o currículo e o plano de entrevista no dossiê. No Windows, **Abrir currículo em Markdown** e **Abrir currículo em PDF** usam o aplicativo padrão de cada formato disponível. O botão indica **enviado** quando a única versão identificada está em `envios/`.

Para gerar o PDF, consulte os [requisitos de conversão](skills/md-to-cv/SKILL.md). Para analisar ou transcrever uma gravação fornecida por você, consulte os [materiais de entrevista](skills/posicionar-carreira/references/entrevistas.md#entrevista-gravada).

### Status e evidência

Durante a pesquisa, a avaliação e o preparo dos materiais, mantenha `identificada`. O plugin valida as mudanças de `status` no YAML. Consulte as opções em `transicoes_status`.

| Status atual | Próximos status permitidos |
|---|---|
| `identificada` | `candidatura-enviada`, `descartada`, `cancelada-pela-empresa` |
| `candidatura-enviada` | `entrevistas`, `oferta`, `contratado`, `reprovado`, `cancelada-pela-empresa` |
| `entrevistas` | `oferta`, `contratado`, `reprovado`, `cancelada-pela-empresa` |
| `oferta` | `contratado`, `reprovado`, `cancelada-pela-empresa` |
| `descartada`, `cancelada-pela-empresa`, `contratado`, `reprovado` | Fim do processo. Os demais campos e o histórico ainda aceitam atualizações. |

- Registre o motivo e a etapa alcançada. Para passar de `identificada` a `candidatura-enviada`, informe `candidatura_confirmada: true` e a `fonte_candidatura` que comprova o envio. Guarde as versões exatas em `envios/`. Silêncio ou feedback positivo, por si só, não justificam mudar o status.
- Use a URL original ou o caminho da evidência relativo à pasta de dados. Relatórios de lote podem acrescentar contexto. Uma fonte local nova ou alterada precisa existir. Se uma fonte antiga mudar de lugar, ainda é possível listar e editar a vaga.
- Informe a data do fato em `AAAA-MM-DD` ou `null` quando desconhecida. `registrado_em` indica a data do registro. Um prazo exige `fonte_prazo`. `revisar_em` indica quando rever o processo.
- Para registrar a disponibilidade pública do anúncio, informe `aberta_verificada`, `nao_confirmada` ou `anuncio_expirado` e a `fonte_disponibilidade_inscricao`. Envie `disponibilidade_inscricao: null` para limpar ambos os campos. A situação do anúncio não comprova acesso autenticado, envio ou encerramento do processo pessoal.

### Avaliação e remuneração

O painel lê o score de `avaliacao-validada.json`. Mantenha `avaliacao.md` coerente com esse valor e registre aderência, cultura, condições, recomendação e fontes datadas. Para recalcular, siga a [avaliação determinística](skills/posicionar-carreira/SKILL.md#avaliação-determinística).

Ao mapear uma vaga, siga a [pesquisa salarial](skills/posicionar-carreira/references/benchmark-salarial.md). Para vagas em andamento, o painel Markdown opcional mostra a síntese e o link ou indica pesquisa pendente.

### Validação, painel Markdown e relatórios

Na pasta do plugin, execute o comando desejado. Para usar outra base, acrescente `--root <caminho-absoluto-da-pasta-de-dados>`.

```powershell
python -B server/gestao_vagas.py lint
python -B server/gestao_vagas.py gerar
python -B server/gestao_vagas.py relatorio --mes AAAA-MM
```

- Peça **rode o lint da base** para examinar os dossiês, a triagem, as fontes compartilhadas e os links locais. Cada erro ou aviso indica o arquivo e sugere uma correção. O lint apenas lê a base. No terminal, erros retornam código 1 e avisos isolados retornam 0. Verifique URLs externas e âncoras à parte.
- `gerar` valida a base e cria ou substitui `painel-vagas.md`, preservando **Revisões recebidas**. Execute apenas se quiser esse arquivo, fora de uma edição manual. O painel do plugin lê os dossiês por atualização mais recente. Se houver índice, mostra primeiro as vagas na ordem dos links.
- `relatorio` registra vagas identificadas, envios confirmados e eventos do mês. Use `--data AAAA-MM-DD` para definir a data de referência. Escolha um mês até essa data. Novas execuções no mesmo dia criam revisões `-r2`, `-r3` e seguintes. Envios confirmados sem data contam só no total histórico. Pistas e recibos sem associação ficam fora da contagem.

No Markdown, `grupo_plano_atual` separa vagas identificadas sem envio confirmado: `plano_modalidade_compativel` para avaliar e `plano_esclarecimento` para esclarecer. `lote_plano` e `fonte_plano` registram a origem da classificação.

## Manutenção humana em lote

`server/lote.py` usa o mesmo serviço de gravação do MCP. Para agentes, siga o [fluxo de gestão de oportunidades](#gestão-de-oportunidades).

1. Consulte a revisão de cada processo que você quer alterar.

```powershell
python -B server/lote.py --detalhar empresa/local-001
```

2. Salve em `entrada.json` uma lista de operações com os campos do [fluxo de gestão](#gestão-de-oportunidades). Neste exemplo, uma vaga com candidatura enviada avança para entrevistas.

```json
[
  {
    "ferramenta": "atualizar_vaga",
    "argumentos": {
      "processo_id": "empresa/local-001",
      "revisao": "<revisao retornada pelo detalhe>",
      "descricao": "Empresa informou a data da entrevista",
      "fonte": "https://example.org/confirmacao",
      "mudancas": { "status": "entrevistas", "proxima_acao": "Preparar entrevista" }
    }
  }
]
```

3. Confira a prévia sem gravar. Os IDs de novos cadastros são provisórios.

```powershell
python -B server/lote.py entrada.json
```

4. Depois de revisar cada item, aplique o lote e guarde o resultado.

```powershell
python -B server/lote.py entrada.json --aplicar > resultado.json
```

5. Confira as operações aplicadas, repetidas, com conflito ou com erro. Para tentar de novo, revise `falhas` no relatório. Consulte as revisões atuais dos processos em conflito e reconcilie as mudanças. A execução usa as revisões que você fornecer.
6. Confira a prévia das falhas. Acrescente `--aplicar` quando estiver correta.

```powershell
python -B server/lote.py resultado.json --somente-falhas
```

## Testes locais

Na pasta do plugin, execute os testes de operações MCP, validação, painel e relatórios. A suíte usa dossiês fictícios. Para testar a interface do servidor MCP e a mensagem da vaga selecionada, instale Playwright para Python e Chrome.

```powershell
python -X utf8 -B -m unittest discover -s tests -v
```
