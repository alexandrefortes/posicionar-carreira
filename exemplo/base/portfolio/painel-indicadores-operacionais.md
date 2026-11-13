# Painel de indicadores operacionais

**Caso fictício de portfólio.**

## Contexto

Em 2024, a equipe de operações do Observatório Horizonte (fictício) precisava comparar o volume e o tempo de atendimento entre semanas. Uma atualização na origem podia gerar outro registro para o mesmo atendimento e inflar a contagem. O projeto chegou ao estágio de piloto.

## Minha contribuição

Escrevi a consulta em SQL que mantém o registro mais recente de cada identificador. Montei o painel com duas métricas, volume semanal e mediana do tempo de atendimento, e documentei como cada uma era calculada. A equipe de operações conferiu comigo se as definições faziam sentido para a rotina de atendimento.

## Decisões

- Usei a semana de abertura para comparar volume entre períodos. Atualizações do mesmo evento mantêm um identificador e entram uma vez na contagem.
- Calculei a mediana do tempo apenas para os atendimentos concluídos, pois os demais ainda não têm duração final.

## Resultado observado

Em um teste com 12 registros sintéticos, a consulta retornou 10 eventos distintos e reteve as duas versões mais recentes que precisavam prevalecer. O piloto apresentou o volume semanal de eventos e a mediana dos atendimentos concluídos. A verificação não mediu ganho operacional nem adoção em produção.

## Evidências e uso

O [registro de evidência](../perfil/evidencias/painel-indicadores-operacionais.md) indica o recorte, as regras de cálculo e o que a amostra sustenta. O [perfil profissional](../perfil/perfil-profissional.md) registra a função e o período. Este caso de demonstração pode inspirar uma apresentação de SQL, qualidade de dados e trabalho com operações.
