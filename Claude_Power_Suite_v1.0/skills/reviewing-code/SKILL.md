---
name: reviewing-code
description: "Revisa código como engenheiro sênior — diffs, pull requests, commits, arquivos ou trechos colados na conversa — priorizando defeitos de correção, segurança, concorrência, tratamento de erros e testes ausentes, com cada achado classificado por severidade, localizado e acompanhado de cenário de falha concreto e correção sugerida. Inclui script que aponta hotspots no diff (segredos, arquivos sensíveis, código sem teste). Use sempre que o usuário pedir revisão de código, code review, \"revise este código/endpoint/função\", análise de PR, \"pode mergear?\", \"está bom?\", auditoria de qualidade ou de segurança, ou orientação sobre como revisar uma mudança grande."
---

# Revisão de Código

## Objetivo

Encontrar o que causaria **dano real** se fosse integrado: bugs, falhas de
segurança, perda de dados, regressões e lacunas de teste. Estilo e
preferência pessoal só entram se o projeto tiver regra explícita.

## Fluxo de trabalho

```text
- [ ] 1. Obter o diff e o contexto da mudança
- [ ] 2. Rodar o mapa de hotspots
- [ ] 3. Ler a mudança inteira, depois os hotspots em profundidade
- [ ] 4. Verificar cada achado candidato
- [ ] 5. Classificar e redigir
- [ ] 6. Veredito
```

### 1. Diff e contexto

- Obtenha o diff (`git diff <base>...HEAD`, o PR, ou os arquivos indicados).
- Descubra a **intenção**: descrição do PR, issue, mensagem de commit. Uma
  mudança correta para a intenção errada é um achado.
- Leia as convenções do projeto se existirem (CONTRIBUTING, CLAUDE.md,
  config de lint).

### 2. Hotspots

```bash
git diff main...HEAD | python3 scripts/diff_hotspots.py -
# ou
python3 scripts/diff_hotspots.py --git "main...HEAD"
```

Saída: tamanho por arquivo e sinais ALTO/MÉDIO/BAIXO (possíveis segredos,
arquivos sensíveis, código sem teste, testes removidos, debug esquecido).
Os sinais orientam onde olhar; **não são achados por si só** — confirme
cada um lendo o código. Sem execução de código, faça a mesma triagem
manualmente usando a lista de sinais acima.

### 3. Leitura

Primeiro uma passada completa para entender a mudança; depois, nos trechos
de risco, leia também o código **ao redor** e os chamadores — a maioria dos
bugs está na interação com o que não mudou. Use o checklist por categoria:
[reference/checklist.md](reference/checklist.md).

### 4. Verificar achados

Para cada candidato, construa o **cenário de falha concreto**: entrada ou
estado → caminho no código → resultado errado. Se não conseguir construir
o cenário, rebaixe para pergunta ou descarte. Quando possível, prove:
rode o teste existente, escreva um teste mínimo que falha, ou execute o
trecho. Diga no achado se foi **comprovado** (executado) ou **inferido**
(leitura).

### 5. Classificar e redigir

| Severidade | Critério |
|---|---|
| **Crítico** | perda/corrupção de dados, falha de segurança explorável, indisponibilidade; bloqueia merge |
| **Alto** | comportamento incorreto em caso realista; bloqueia merge |
| **Médio** | incorreto em caso raro, ou risco de manutenção com custo concreto; corrigir em breve |
| **Baixo** | melhoria opcional com benefício claro |

Formato de cada achado:

```markdown
### [Alto] Retry sem idempotência duplica cobrança — `payments/charge.py:88`
**Cenário:** gateway responde timeout após debitar → `retry()` reenvia →
cliente é cobrado duas vezes.
**Evidência:** inferido pela leitura; `charge()` não envia chave de idempotência.
**Correção:** gerar `idempotency_key` por pedido e enviá-la em todas as tentativas.
```

Regras de redação:
- Um achado por problema; agrupe ocorrências repetidas do mesmo padrão.
- Ordene por severidade.
- Cite código exato; nada de "em algum lugar do arquivo".
- Sugira a correção mínima; refatorações amplas vão como observação
  separada.
- Reconheça em uma linha o que está bem feito quando for relevante para a
  decisão (ex.: "migração reversível e testada").

### 6. Veredito

Termine com um destes:
- **Aprovar** — nenhum achado Crítico/Alto.
- **Aprovar com ressalvas** — apenas Médio/Baixo; liste o que acompanhar.
- **Solicitar mudanças** — há Crítico ou Alto; liste exatamente o que
  precisa mudar para aprovar.

Inclua o que **não** foi verificado (ex.: "não executei a suíte de
integração; não revisei o arquivo gerado `schema.pb.go`").

## Postura

- Assuma competência do autor; questione o código, não a pessoa.
- Pergunte quando a intenção for ambígua em vez de presumir erro.
- Não invente regra do projeto; se citar convenção, indique onde ela está.
- Diff grande demais (> ~400 linhas por arquivo, ou muitos assuntos
  misturados): recomende dividir e revise primeiro as partes de maior risco.
