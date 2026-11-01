---
name: debugging-systematically
description: "Investiga erros, falhas, regressões e comportamentos inesperados com método científico — reproduzir, isolar, hipóteses falsificáveis testadas uma a uma, causa-raiz comprovada antes de corrigir — e agrupa logs volumosos por assinatura para revelar os erros dominantes. Use sempre que o usuário relatar bug, exceção, stack trace, erro HTTP 4xx/5xx, teste falhando ou intermitente, \"funcionava ontem\", lentidão, crash ou incidente, ou anexar um arquivo de log e perguntar a causa (\"qual a causa?\", \"por que quebrou?\", \"o que aconteceu?\"). Root-cause debugging and log analysis."
---

# Depuração Sistemática

## Regra central

Nenhuma correção sem causa-raiz **comprovada**. Uma mudança que faz o
sintoma sumir sem explicação é um risco, não uma solução.

## Fluxo de trabalho

```text
- [ ] 1. Descrever o sintoma com precisão
- [ ] 2. Reproduzir (ou coletar evidência suficiente)
- [ ] 3. Reduzir o espaço de busca
- [ ] 4. Hipóteses → experimentos, uma de cada vez
- [ ] 5. Comprovar a causa-raiz
- [ ] 6. Corrigir com teste de regressão
- [ ] 7. Verificar e relatar
```

### 1. Sintoma

Registre: comportamento esperado vs. observado; mensagem de erro **exata**;
quando começou; frequência (sempre / às vezes / sob carga); ambiente
(versão, SO, dados, configuração); o que mudou recentemente (deploy,
dependência, dado, infraestrutura).

### 2. Reproduzir

- Busque o menor passo a passo que reproduz. Escreva-o como teste
  automatizado sempre que possível — ele vira o teste de regressão.
- Falha intermitente: aumente a frequência (laço com centenas de execuções,
  paralelismo, carga, semente aleatória fixa vs. variada) e registre a
  taxa. Intermitência costuma indicar concorrência, tempo, ordem de testes,
  estado compartilhado ou dependência externa.
- Sem reprodução (produção): colete logs, métricas, traces, IDs de
  requisição afetadas e compare com requisições que funcionaram.

**Logs volumosos**: agrupe por assinatura antes de ler linha a linha:

```bash
python3 scripts/log_signatures.py app.log --level WARN --top 20
```

O script normaliza partes variáveis (horários, IDs, IPs, números) e mostra
contagem, primeira e última ocorrência de cada padrão, tipos de exceção e
número de stack traces. Procure: a assinatura que **aparece primeiro**
(causa costuma vir antes dos efeitos), as que surgem só após o horário do
problema, e picos de contagem.

### 3. Reduzir o espaço de busca

Técnicas, em ordem de custo:
- **Ler o stack trace de baixo para cima** até o primeiro quadro do código
  do projeto.
- **Comparar** caminho que funciona vs. que falha (entrada, ambiente,
  versão) e listar todas as diferenças.
- **Bisseção no histórico**: `git bisect start <ruim> <bom>` com
  `git bisect run <comando-de-teste>` quando há versão boa conhecida.
- **Bisseção na entrada**: cortar a entrada pela metade até o mínimo que
  falha.
- **Instrumentar** a fronteira entre componentes: logar valores na entrada
  e na saída para localizar onde o dado fica errado.

Catálogo de causas frequentes por sintoma:
[reference/failure-patterns.md](reference/failure-patterns.md).

### 4. Hipóteses e experimentos

Mantenha uma tabela viva:

```markdown
| # | Hipótese | Previsão se verdadeira | Experimento | Resultado |
|---|---|---|---|---|
| 1 | cache devolve objeto de outro tenant | falha só com 2+ tenants simultâneos | teste com 2 tenants em paralelo | confirmada / refutada |
```

Regras:
- Hipótese precisa ser **falsificável**: diga o que a refutaria.
- Um experimento muda **uma variável**.
- Comece pela hipótese mais barata de testar entre as prováveis.
- Registre resultados refutados; eles evitam voltar ao mesmo lugar.
- Se três hipóteses seguidas forem refutadas, volte à etapa 3: o modelo
  mental do sistema está errado em algum ponto.

### 5. Comprovar a causa-raiz

A causa está comprovada quando você consegue **ligar e desligar** a falha
controlando apenas a causa. Em seguida pergunte "por que isso foi possível?"
até chegar a algo que valha corrigir (técnica dos 5 porquês), sem parar no
primeiro sintoma intermediário.

### 6. Corrigir

- Escreva/ajuste o teste que reproduz a falha e **veja-o falhar**.
- Faça a correção mínima na causa, não no sintoma.
- Veja o teste passar; rode a suíte relacionada.
- Procure o mesmo padrão em outros lugares do código (`grep`).
- Remova instrumentação temporária.

### 7. Relatar

```markdown
## Resumo
<1–2 frases: o que falhava, por quê, o que foi corrigido>

## Causa-raiz
<mecanismo, com arquivo:linha e evidência que comprova>

## Reprodução
<passos ou teste>

## Correção
<o que mudou e por que resolve a causa>

## Verificação
<testes executados e resultados reais; o que NÃO foi verificado>

## Prevenção
<teste de regressão, alerta, validação, mudança de processo>
```

Se a causa não foi comprovada, diga isso explicitamente, liste as hipóteses
restantes com a evidência a favor e contra e o próximo experimento.

## Armadilhas

- Corrigir em vários lugares ao mesmo tempo: impossível saber o que
  resolveu.
- Confiar em mensagem de log sem verificar se o código que a gera é o que
  está rodando (versão implantada ≠ versão no editor).
- Aumentar timeout ou adicionar retry/sleep para "resolver" intermitência
  sem entender a causa.
- Descartar "não pode ser isso" sem testar.
