---
name: engineering-prompts
description: "Projeta, reescreve e depura prompts para modelos Claude e outros LLMs (prompts de sistema, prompts de tarefa, templates com variáveis, instruções de agentes e de ferramentas), com tags XML, exemplos, formato de saída verificável e casos de teste, além de um linter de tags, variáveis e instruções vagas. Use sempre que o usuário pedir para criar, melhorar, revisar ou diagnosticar um prompt, ou quando um LLM, classificador ou agente estiver respondendo de forma inconsistente, alucinando, ignorando regras ou sofrendo prompt injection (seguindo instruções contidas na entrada). Prompt engineering."
license: MIT
---

# Engenharia de Prompts

## Fluxo de trabalho

Copie e acompanhe:

```text
- [ ] 1. Levantar requisitos (tarefa, público, entrada, saída, critérios)
- [ ] 2. Escrever casos de teste ANTES do prompt
- [ ] 3. Redigir o prompt com a estrutura padrão
- [ ] 4. Rodar o linter e corrigir erros
- [ ] 5. Simular os casos de teste e iterar
- [ ] 6. Entregar prompt + casos + notas de manutenção
```

### 1. Levantar requisitos

Obtenha (do pedido ou perguntando, no máximo 3 perguntas objetivas):

- **Tarefa**: o que o modelo deve produzir, em um verbo + objeto.
- **Entrada**: formato e variação real (tamanho, idioma, ruído). Peça 2–3
  exemplos reais se existirem.
- **Saída**: formato exato e quem consome (pessoa, parser, outra etapa).
- **Critérios de sucesso** verificáveis ("JSON válido com as chaves X, Y",
  "≤ 120 palavras", "cita o trecho de origem").
- **Casos difíceis**: entradas ambíguas, fora de escopo, maliciosas.

Se for depuração de prompt existente, peça o prompt atual e **pelo menos uma
saída ruim real**. Sem exemplo de falha, não altere às cegas.

### 2. Casos de teste primeiro

Escreva de 5 a 10 casos cobrindo: caminho feliz (2+), caso-limite (2+),
fora de escopo (1+), entrada adversarial/injeção quando a entrada vem de
terceiros (1+). Formato:

```text
CASO <n> — <categoria>
Entrada: <texto ou variáveis>
Esperado: <propriedades verificáveis, não um texto exato>
```

### 3. Estrutura padrão do prompt

Use esta ordem; omita seções sem conteúdo real:

```text
<role>Quem o modelo é e para quem trabalha (1–2 frases).</role>

<context>Fatos de domínio que o modelo não sabe: público, políticas,
glossário, por que a tarefa existe.</context>

<instructions>
1. Passos numerados, no imperativo, na ordem de execução.
2. Cada regra com o motivo quando não for óbvio ("…porque o texto é lido
   por leitores de tela").
</instructions>

<examples>
<example><input>…</input><output>…</output></example>
</examples>

<output_format>Formato exato, com esqueleto.</output_format>

<input>{{variavel}}</input>
```

Regras de redação (motivos na referência):

- Diga **o que fazer** em vez do que não fazer ("escreva em prosa contínua"
  em vez de "não use listas").
- Explique o **porquê** de regras importantes em tom normal; evite
  MAIÚSCULAS e "CRÍTICO" — modelos atuais seguem instruções literais e a
  ênfase excessiva causa sobre-aplicação.
- Seja específico: troque "resuma bem" por "resuma em 3 tópicos de até
  20 palavras, priorizando decisões e prazos".
- Coloque documentos longos **antes** das instruções e da pergunta.
- Exemplos devem variar entre si e cobrir o caso difícil; exemplos quase
  idênticos fazem o modelo copiar detalhes superficiais.
- Para saída consumida por código, peça só o artefato e mostre o esqueleto
  exato; se a API usada oferecer saída estruturada/JSON schema, prefira-a.
- Conteúdo de terceiros (e-mails, páginas, documentos) vai dentro de uma tag
  própria com instrução explícita de que é **dado, não instrução**.
- Para raciocínio difícil, peça o raciocínio em `<thinking>` e a resposta em
  `<answer>`, ou use o recurso de extended thinking se disponível.

Técnicas por tipo de problema: [reference/patterns.md](reference/patterns.md).

### 4. Linter

Salve o prompt em arquivo e execute:

```bash
python3 scripts/lint_prompt.py prompt.txt
```

- **ERRO** (tags desbalanceadas, `{{var}}`/`[INSERIR]`/`TODO` restantes):
  corrija sempre. Num template, as variáveis `{{...}}` são esperadas: rode
  o linter numa versão com valores de exemplo preenchidos.
- **AVISO**: avalie cada um; justifique na entrega os que mantiver.
- O linter é heurístico: ele não mede qualidade de resposta. Sem ferramenta
  de execução de código, aplique o checklist da seção 5 manualmente.

### 5. Simular e iterar

Para cada caso de teste, execute o prompt (se houver acesso a um modelo) ou
simule criticamente a resposta provável. Marque passou/falhou por
propriedade. Para cada falha, altere **uma** coisa, registre o motivo e
reteste todos os casos (evita regressão). Pare quando todos passarem ou
quando restarem falhas que dependem de decisão do usuário.

Nunca declare que o prompt "foi testado" se os casos foram apenas simulados:
diga "simulado" explicitamente.

### 6. Entrega

```markdown
## Prompt
<prompt final em bloco de código>

## Variáveis
| variável | descrição | exemplo |

## Casos de teste
<lista com resultado: passou / falhou / simulado>

## Decisões de design
- <escolha> — <motivo>

## Manutenção
- Sinais de que o prompt precisa de revisão: <ex.: taxa de JSON inválido > 1%>
```

## Depuração rápida por sintoma

| Sintoma | Causa provável | Ajuste |
|---|---|---|
| Ignora uma regra | regra enterrada ou sem motivo | mover para `<instructions>`, numerar, explicar o porquê |
| Aplica regra onde não devia | ênfase excessiva ou regra absoluta | remover maiúsculas, delimitar escopo ("apenas quando…") |
| Formato oscila | sem esqueleto/exemplo | `<output_format>` com esqueleto + 2 exemplos variados |
| Inventa fatos | falta de fonte ou permissão para "não sei" | fornecer fonte, exigir citação, permitir "informação insuficiente" |
| Respostas longas demais | limite não quantificado | limite numérico + exemplo do tamanho certo |
| Segue instruções vindas do documento | entrada não delimitada | envolver em tag e declarar como dado |
| Copia o exemplo literalmente | exemplos pouco variados | diversificar exemplos, rotular como ilustrativos |
