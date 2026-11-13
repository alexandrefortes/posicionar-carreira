---
name: md-to-cv
description: Converte o currículo de trabalho em Markdown para PDF com Pandoc e pdfLaTeX e confere a extração do texto.
---

# Converter currículo em PDF

Use o conversor para gerar um PDF de coluna única com texto selecionável. Resolva a pasta da skill pelo caminho deste arquivo. Use Python 3.10 ou superior, Pandoc 3 ou superior, pdfLaTeX com os pacotes do [template](scripts/template.tex) e a dependência Python da [lista de requisitos](requirements.txt).

Antes de gerar, confira o Markdown de trabalho da vaga. Preserve o conteúdo enviado em `envios/` e atualize apenas o PDF de trabalho autorizado. Conserve o vínculo do processo com a versão de trabalho.

```powershell
python -B "<pasta-da-skill>/scripts/convert.py" "<caminho-do-dossie>/curriculo.md" --output "Marina_Exemplo_CV_Laboratorio_Exemplo_Analista_Dados.pdf"
```

Passe o caminho absoluto ou relativo ao diretório atual. `--output` recebe só o nome do PDF. O conversor grava o arquivo ao lado do Markdown. Sem a opção, usa o nome da fonte com extensão `.pdf`.

## Nome do PDF

Use nome, empresa e cargo, separados por underscores, como no exemplo fictício acima. Acrescente data ou identificador quando precisar distinguir vagas ou versões. Preserve o nome do Markdown de trabalho e atualize os links do dossiê quando renomear o PDF.

## Conferência

O conversor informa a paginação e mostra uma amostra do texto extraído. Confira o texto, a ordem das seções e a aparência do PDF. Use uma linha de contato em texto e títulos Markdown para nome, seções e entradas. Se incluir `title`, `author` e `keywords` no bloco YAML inicial, use apenas informações autorizadas e pertinentes à vaga.
