# Evidência fictícia do painel de indicadores operacionais

## Origem e contexto

Registro de demonstração de um piloto no Observatório Horizonte (fictício) em 2024. A equipe de operações queria comparar semanas de atendimento sem contar duas vezes eventos que tinham sido atualizados na origem.

## Contribuição de Marina

Marina escreveu a consulta em SQL que mantém o registro mais recente por identificador. Montou o painel e documentou as regras do volume semanal e da mediana do tempo de atendimento. A equipe de operações participou da conferência das definições e dos resultados da amostra.

## O que foi conferido

| Verificação | Evidência da simulação | Resultado observado |
|---|---|---|
| Deduplicação | 12 registros sintéticos, distribuídos entre os identificadores `E01` a `E10`. `E03` e `E07` tinham uma versão anterior e uma atual. | A consulta retornou 10 identificadores e manteve as versões mais recentes de `E03` e `E07`. |
| Volume semanal | Contagem de identificadores distintos pela semana de abertura do atendimento. | Uma atualização do mesmo evento não aumentou o total semanal. |
| Tempo de atendimento | Mediana da diferença entre abertura e conclusão, considerando os eventos concluídos. | Um atendimento sem data de conclusão ficou fora do cálculo da mediana. |

## Limites e uso

A verificação sustenta a regra de deduplicação e o cálculo na amostra sintética. O estágio registrado é piloto. Queda no tempo de atendimento, adoção em produção e ganhos operacionais exigiriam medições próprias.

Esta evidência integra o [caso de portfólio](../../portfolio/painel-indicadores-operacionais.md) e sustenta as alegações correspondentes no [perfil profissional](../perfil-profissional.md).
