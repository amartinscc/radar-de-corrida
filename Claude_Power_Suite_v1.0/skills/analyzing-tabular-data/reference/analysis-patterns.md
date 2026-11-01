# Padrões de análise e armadilhas

## Sumário
- Comparação entre períodos
- Segmentação e ranking
- Funil e conversão
- Coortes e retenção
- Distribuições e resumo
- Teste de diferença entre grupos
- Armadilhas estatísticas
- Snippets em Python (biblioteca padrão)

## Comparação entre períodos
- Compare períodos equivalentes (mesmo nº de dias úteis, mesma
  sazonalidade: mês contra mesmo mês do ano anterior).
- Reporte absoluto, variação absoluta e variação percentual.
- Período parcial (mês corrente) não se compara com mês fechado sem
  normalizar por dia.

## Segmentação e ranking
- Mostre o tamanho (n) de cada segmento; segmentos pequenos produzem taxas
  extremas por acaso.
- Ranking por taxa com n pequeno: exija n mínimo ou ordene pelo limite
  inferior do intervalo de confiança.
- Agrupe a cauda longa em "Outros" e diga quantos itens ela contém.

## Funil e conversão
- Defina cada etapa como evento verificável e a janela de tempo.
- Conte usuários únicos por etapa, não eventos.
- Conversão de etapa = etapa(n) / etapa(n−1); conversão total =
  última / primeira.

## Coortes e retenção
- Coorte = data do primeiro evento (ex.: mês da primeira compra).
- Retenção no período k = ativos no período k / tamanho da coorte.
- Coortes recentes têm menos períodos observados: não as compare em
  períodos que ainda não aconteceram.

## Distribuições e resumo
- Para dados assimétricos (renda, tempo de resposta, valor de pedido),
  reporte mediana e percentis (p90, p95) além da média.
- Desvio-padrão só é bom resumo para distribuições aproximadamente
  simétricas.
- Outliers pela regra de Tukey (fora de Q1−1,5·IQR … Q3+1,5·IQR) são
  candidatos a investigação, não a exclusão automática.

## Teste de diferença entre grupos
- Diferença de proporções com amostras grandes: teste z para duas
  proporções; reporte também o intervalo de confiança da diferença.
- Diferença de médias: teste t de Welch (não supõe variâncias iguais);
  para dados muito assimétricos, considere Mann-Whitney.
- Muitas comparações ao mesmo tempo aumentam falsos positivos; ajuste
  (Bonferroni/Holm) ou trate como exploratório.
- Significância estatística não implica relevância prática: reporte o
  tamanho do efeito.

## Armadilhas estatísticas
- **Paradoxo de Simpson**: a tendência agregada pode inverter dentro dos
  grupos; verifique por segmento quando a composição dos grupos muda.
- **Viés de sobrevivência**: analisar só quem "ficou" (clientes ativos,
  empresas existentes).
- **Correlação ≠ causalidade**: sem experimento, descreva associação.
- **Regressão à média**: grupos selecionados por valor extremo tendem a
  voltar ao normal.
- **Média de médias**: média de taxas de grupos de tamanhos diferentes
  ≠ taxa global; pondere pelo tamanho.
- **Dupla contagem** após junções (joins) 1-para-N.

## Snippets em Python (biblioteca padrão)

Leitura com o formato brasileiro:

```python
import csv
from decimal import Decimal

def br_decimal(s):
    return Decimal(s.strip().replace(".", "").replace(",", "."))

with open("dados.csv", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f, delimiter=";"))
```

Agregação por grupo:

```python
from collections import defaultdict
total = defaultdict(Decimal)
count = defaultdict(int)
for r in rows:
    total[r["regiao"]] += br_decimal(r["valor"])
    count[r["regiao"]] += 1
for k in sorted(total, key=total.get, reverse=True):
    print(k, count[k], total[k], (total[k] / count[k]).quantize(Decimal("0.01")))
```

Percentis:

```python
import statistics
p = statistics.quantiles(valores, n=100)  # p[49]=p50, p[89]=p90, p[94]=p95
```

Intervalo de confiança de 95% para proporção (aproximação normal, adequada
quando n·p e n·(1−p) ≥ 10):

```python
import math
def ic95(sucessos, n):
    p = sucessos / n
    e = 1.96 * math.sqrt(p * (1 - p) / n)
    return p - e, p + e
```
