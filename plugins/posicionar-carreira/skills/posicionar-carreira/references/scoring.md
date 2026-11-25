# Scoring de oportunidades

Use este contrato apenas para vagas com informação suficiente sobre função, responsabilidades e requisitos.

## Dimensões

| Chave | Peso | Pergunta |
|---|---:|---|
| `alinhamento_funcao` | 30% | O mandato e as responsabilidades se aproximam dos cargos-alvo? |
| `senioridade_autonomia` | 20% | Nível, escopo e poder de decisão são compatíveis? |
| `segmento_contexto` | 15% | O contexto aproveita a experiência e respeita segmentos desejados? |
| `modalidade_localizacao` | 15% | Modalidade, localização e viagens são compatíveis? |
| `competencias_evidencias` | 10% | Os requisitos obrigatórios têm evidência no perfil? |
| `remuneracao_contrato` | 10% | O vínculo e as demais condições contratuais comprovadas são compatíveis com as preferências da pessoa? |

Justifique cada nota de 0 a 10. Em `remuneracao_contrato`, consulte a estratégia salarial na base da pessoa. Considere o valor salarial na nota somente com critério individual explícito e evidência comparável da vaga. Sem critério sobre o valor, avalie as demais condições contratuais confirmadas. Se faltarem informações decisivas, use 5 e registre as lacunas na [pesquisa salarial](benchmark-salarial.md). Preserve os pesos e os resultados históricos.

## Entrada do validador

```json
{
  "sufficient_information": true,
  "dimensions": {
    "alinhamento_funcao": {"score": 9, "justification": "Responsabilidades alinhadas aos objetivos da pessoa."},
    "senioridade_autonomia": {"score": 8, "justification": "Reporte e escopo compatíveis."},
    "segmento_contexto": {"score": 9, "justification": "Experiência anterior no segmento."},
    "modalidade_localizacao": {"score": 8, "justification": "Modelo híbrido compatível."},
    "competencias_evidencias": {"score": 9, "justification": "Requisitos sustentados pelo perfil."},
    "remuneracao_contrato": {"score": 5, "justification": "Condições contratuais ainda pendentes de confirmação."}
  },
  "disqualifier": {"confirmed": false, "reason": null},
  "overall_score": 10
}
```

`overall_score` é aceito apenas para demonstrar que será ignorado. O script sempre recalcula o resultado.

Para conteúdo insuficiente:

```json
{
  "sufficient_information": false,
  "missing_information": ["responsabilidades", "requisitos obrigatórios"]
}
```

Nesse caso, o resultado não contém score nem rótulo.

## Desqualificadores

Marque `confirmed: true` somente com conflito comprovado frente a requisito decisivo ou critério eliminatório explícito da pessoa. Isso inclui um piso firme apenas quando o valor confirmado da vaga estiver abaixo dele em condições comparáveis. Cite a evidência e a razão. Informação ausente ou abaixo da referência de mercado, por si só, não desqualifica.

Desqualificador confirmado produz score 0 e rótulo `Disqualified`. Ausência de informação não é desqualificador.

## Cálculo

```text
score =
  alinhamento_funcao * 0.30 +
  senioridade_autonomia * 0.20 +
  segmento_contexto * 0.15 +
  modalidade_localizacao * 0.15 +
  competencias_evidencias * 0.10 +
  remuneracao_contrato * 0.10
```

O script arredonda para uma casa decimal e aplica depois:

- alinhamento até 4: teto 4,0;
- alinhamento acima de 4 e até 6: teto 6,5;
- alinhamento acima de 6: sem teto adicional;
- `Strong fit` exige score de 8,5 ou mais e alinhamento de 8 ou mais;
- `Moderate fit` exige score de 7,0 ou mais e alinhamento de 6 ou mais;
- score de 5,0 a 6,9: `Weak fit`;
- score abaixo de 5,0: `Poor fit`.

## Validação

Execute `python -B "<pasta-da-skill>/scripts/validate_score.py" "<entrada.json>"`. Use `--output "<novo-resultado.json>"` para gravar uma saída nova quando autorizado. Caminhos relativos partem do diretório atual.

Quando a gravação da avaliação estiver autorizada, guarde a saída em `avaliacao-validada.json`, ao lado de `avaliacao.md` no dossiê. O relatório de vagas lê esse arquivo. Ao reavaliar, use uma saída temporária, confira o resultado e preserve a avaliação anterior no histórico antes de substituir a versão atual.

## Saída

O validador devolve `status`, notas validadas, `weighted_score`, `final_score`, `label`, `disqualified` e `disqualifier_reason`. Use esses campos sem recalculá-los no texto.
