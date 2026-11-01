---
name: analyzing-tabular-data
description: "Analisa dados tabulares (CSV, TSV e exportações de planilhas ou bancos) — perfil de qualidade por coluna, nulos, duplicatas, tipos inconsistentes, outliers e números no formato brasileiro — e responde perguntas de negócio com números calculados por código, suposições explícitas e limitações declaradas. Use sempre que houver um arquivo .csv/.tsv no pedido ou no diretório e o usuário fizer qualquer pergunta sobre os dados (quem vendeu mais, totais, médias, comparação entre meses/períodos, queda ou crescimento, ranking, tendência), mesmo que não peça \"análise\" explicitamente; e também para explorar, limpar, validar ou checar se um arquivo está pronto para carga. Data profiling and analysis."
---

# Análise de Dados Tabulares

## Princípio

Todo número na resposta precisa ser **reproduzível**: vem de um cálculo
executado sobre o arquivo, com filtros e suposições declarados. Nunca
estime ou "arredonde de cabeça" um valor que pode ser calculado.

## Fluxo de trabalho

```text
- [ ] 1. Entender a pergunta e a unidade de análise
- [ ] 2. Perfilar o arquivo
- [ ] 3. Decidir o tratamento de cada problema de qualidade
- [ ] 4. Calcular, com código
- [ ] 5. Checar a sanidade dos resultados
- [ ] 6. Comunicar
```

### 1. Pergunta

Defina: a pergunta em uma frase; a **unidade** (o que é uma linha:
pedido, cliente, dia?); o período; a métrica exata (ex.: "ticket médio =
receita bruta / nº de pedidos não cancelados"). Se a pergunta for vaga
("analise isso"), comece pelo perfil e proponha 3 perguntas que os dados
conseguem responder.

### 2. Perfil

```bash
python3 scripts/profile_csv.py dados.csv            # relatório Markdown
python3 scripts/profile_csv.py dados.csv --json     # para processamento
```

O script detecta codificação e delimitador, aceita `1.234,56`, e reporta
por coluna: tipo inferido, % nulos, distintos, mín/máx, média, mediana,
desvio-padrão, outliers (regra de Tukey) e valores mais frequentes; e para
o arquivo: linhas duplicadas, linhas com nº de campos divergente e
cabeçalhos repetidos. Em arquivos muito grandes, use `--max-rows` para uma
amostra e diga que é amostra.

Sem execução de código: leia o cabeçalho e uma amostra, e declare que o
perfil é parcial.

### 3. Tratamento de qualidade

Para cada problema encontrado, escolha e **registre** a decisão:

| Problema | Opções | Critério |
|---|---|---|
| Nulos | excluir linha, imputar, manter como categoria | impacto na métrica; % afetado |
| Duplicatas | remover exatas; deduplicar por chave | existe chave natural? duplicata é erro ou evento real? |
| Tipo inconsistente | converter, descartar valor inválido | quantos valores e quais exemplos |
| Outliers | manter, limitar (winsorizar), excluir | erro de digitação vs. evento real; consulte o usuário se mudar a conclusão |
| Variação de grafia | normalizar (trim, minúsculas, sem acento) | colunas categóricas usadas em agrupamento |

Se uma decisão alterar materialmente o resultado, mostre o resultado
**com e sem** o tratamento.

### 4. Calcular

- Use código (Python com `csv`/`statistics` da biblioteca padrão, ou pandas
  se estiver disponível no ambiente — verifique com `python3 -c "import
  pandas"` antes de depender dele).
- Mantenha o script da análise e mostre-o ou salve-o junto do resultado.
- Agregações: deixe explícito o denominador e os filtros.
- Comparações entre grupos/períodos: reporte valores absolutos **e**
  variação relativa, e o tamanho de cada grupo.
- Dinheiro: some em centavos inteiros ou `decimal.Decimal`.
- Datas: confirme formato (DD/MM vs. MM/DD) olhando valores com dia > 12.

Padrões de análise e armadilhas estatísticas:
[reference/analysis-patterns.md](reference/analysis-patterns.md).

### 5. Sanidade

Antes de responder, confira:
- totais batem com a soma das partes;
- contagens após filtros são plausíveis (nenhum filtro zerou um grupo
  sem querer);
- percentuais somam ~100% quando deveriam;
- ordem de grandeza coerente com o domínio;
- um ou dois registros conferidos manualmente contra o cálculo.

### 6. Comunicar

```markdown
## Resposta
<a resposta direta à pergunta, com o número principal>

## Detalhes
<tabela com os números de apoio; grupos com n>

## Como foi calculado
- Fonte: <arquivo, nº de linhas usadas de N>
- Filtros e tratamentos: <lista>
- Definições: <métricas>

## Limitações
<amostra, dados faltantes, correlação ≠ causalidade, período curto>
```

Gráficos, quando pedidos: um gráfico por mensagem principal, eixos
rotulados com unidade, eixo y começando em zero para barras.
