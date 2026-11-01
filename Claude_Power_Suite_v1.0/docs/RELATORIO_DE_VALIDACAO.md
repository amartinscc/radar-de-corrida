# Relatório de validação — v1.0.0

Data da execução: 2026-11-01. Ambiente: contêiner Linux, Python 3.13.18,
Claude Code 2.1.316. Todos os resultados abaixo vieram de comandos
efetivamente executados; o que não foi executado está na última seção.

## Sumário
- Resultado consolidado
- Validação estrutural das skills
- Testes unitários
- Validação oficial do plugin
- Instalação e carregamento reais
- Avaliações com o modelo (acionamento)
- Avaliações com o modelo (execução de scripts)
- Problemas encontrados e corrigidos durante a validação
- O que não foi verificado

## Resultado consolidado

| Verificação | Comando | Resultado |
|---|---|---|
| Regras oficiais em modo estrito | `validate_skill.py --strict skills/*/` | 8/8 aprovadas |
| Suíte completa | `python3 tools/validate_suite.py` | 28/28 verificações |
| Testes unitários | `python3 -m unittest discover -s tests` | 46 testes, todos aprovados |
| Manifesto do plugin e marketplace | `claude plugin validate .` | Validation passed; verificações do diretório de publicação sem nenhum apontamento |
| Instalação do plugin | `claude plugin marketplace add` + `install` | instalado e habilitado, 8 skills carregadas |
| Acionamento automático (Opus / Sonnet / Haiku) | `tools/run_trigger_evals.py --model ... --judge` | 24/24 · 18/24 · 4/24 |
| Comportamentos esperados, juiz LLM (Opus / Sonnet / Haiku) | idem | 64/72 · 46/72 · 40/72 |
| Haiku com invocação explícita `/power-suite:<skill>` | 3 cenários | 9/9 comportamentos |
| Empacotamento | `tools/package_skills.py` | 8 ZIPs gerados |

## Validação estrutural das skills

Tamanho do corpo do SKILL.md (limite recomendado: 500 linhas):

| Skill | Linhas | Custo ao acionar (estimativa do `claude plugin details`) |
|---|---|---|
| `orchestrating-power-suite` | 92 | ~1,9k tokens |
| `writing-technical-docs` | 100 | ~1,7k |
| `reviewing-code` | 108 | ~1,7k |
| `analyzing-tabular-data` | 109 | ~1,7k |
| `debugging-systematically` | 134 | ~2,0k |
| `architecting-software` | 136 | ~2,1k |
| `engineering-prompts` | 145 | ~2,4k |
| `authoring-agent-skills` | 155 | ~2,7k |

Custo fixo da suíte inteira em toda sessão (metadados): ~1,7k tokens.
As estimativas de tokens são do primeiro carregamento, feito antes do
ajuste de descriptions descrito abaixo.

## Testes unitários

46 testes em `tests/test_scripts.py` cobrem todos os scripts e ferramentas:
regras de `name`/`description`, links e referências, parser YAML
alternativo, criação de esqueleto sem sobrescrita, lint de prompt (tags,
variáveis, ênfase, negativas), numeração e substituição de ADR, detecção de
segredos e arquivos sensíveis em diff (inclusive via `git` em repositório
temporário), agrupamento de logs, âncoras e cercas aninhadas em Markdown,
perfil de CSV com codificação cp1252 e decimal brasileiro, empacotamento
ZIP, instalador (com HOME temporário, verificando que skill existente não é
sobrescrita sem `--force`) e o executor de avaliações (parser da transcrição,
rastreamento de arquivos alterados e restrição de escrita).

## Validação oficial do plugin

`claude plugin validate .` e `claude plugin validate
.claude-plugin/marketplace.json`: **Validation passed**.

O mesmo comando também roda as verificações do diretório de plugins da
Anthropic (licença, ícone etc.): **"These checks found nothing to report"**,
depois da adição da licença MIT e do ícone `.claude-plugin/icon.png`.

## Instalação e carregamento reais

Executado com `HOME` apontando para um diretório temporário, para não
alterar a configuração do usuário:

```text
claude plugin marketplace add <pasta>  → Successfully added marketplace: power-suite-marketplace
claude plugin install power-suite@power-suite-marketplace → Successfully installed (scope: user)
claude plugin list → power-suite 1.0.0, Status: enabled
```

O evento `init` de uma sessão `claude -p` listou as 8 skills como
`power-suite:<nome>`.

## Avaliações com o modelo (acionamento)

`tools/run_trigger_evals.py` executa cada cenário de `evals/` com
`claude -p` num diretório temporário contendo só os insumos do cenário e
registra quais skills foram carregadas pela ferramenta Skill.

Evolução com o modelo padrão da sessão (Opus):

| Rodada | Mudança | Acionamento |
|---|---|---|
| 1ª | descriptions iniciais | 15/24 |
| 2ª | descriptions com as formulações que falharam | 24/24 |

Rodada final por modelo (após todas as correções; limite de 25 turnos;
juiz fixo `claude-opus-5-5`):

| Modelo | Acionamento automático | Comportamentos esperados (juiz) |
|---|---|---|
| `claude-opus-5-5` | **24/24** | **64/72** (89%) |
| `claude-sonnet-5-5` | 18/24 | 46/72 (64%) |
| `claude-haiku-5-5` | 4/24 | 40/72 (56%) |

Por skill (acionamento | comportamentos):

| Skill | Opus | Sonnet | Haiku |
|---|---|---|---|
| analyzing-tabular-data | 3/3 \| 9/9 | 3/3 \| 6/9 | 1/3 \| 6/9 |
| architecting-software | 3/3 \| 9/9 | 3/3 \| 6/9 | 0/3 \| 4/9 |
| authoring-agent-skills | 3/3 \| 8/9 | 3/3 \| 6/9 | 1/3 \| 5/9 |
| debugging-systematically | 3/3 \| 7/9 | 1/3 \| 6/9 | 1/3 \| 5/9 |
| engineering-prompts | 3/3 \| 9/9 | 2/3 \| 6/9 | 1/3 \| 6/9 |
| orchestrating-power-suite | 3/3 \| 5/9 | 1/3 \| 3/9 | 0/3 \| 4/9 |
| reviewing-code | 3/3 \| 9/9 | 3/3 \| 7/9 | 0/3 \| 5/9 |
| writing-technical-docs | 3/3 \| 8/9 | 2/3 \| 6/9 | 0/3 \| 5/9 |

**Invocação explícita com Haiku.** Repetindo 3 cenários com o prefixo
`/power-suite:<skill>` (reviewing-code#1, analyzing-tabular-data#1,
architecting-software#2), o Haiku seguiu a skill, executou os scripts e
cumpriu **9/9** comportamentos. Na invocação por `/`, o conteúdo da skill é
injetado diretamente, sem chamada à ferramenta Skill, por isso o detector
de acionamento não a registra.

**Conclusão operacional:** com Opus, o acionamento automático é confiável
nestes cenários. Com Sonnet e, sobretudo, Haiku, invoque a skill
explicitamente (`/power-suite:reviewing-code ...`) ou mencione o nome da
skill no pedido.

Sobre o juiz: é outro modelo avaliando a evidência (texto do assistente,
skills carregadas, comandos e arquivos alterados), não verificação humana.
Na rodada anterior ele gerou falsos negativos quando recebia só a resposta
final, o que foi corrigido; na rodada final, todas as 216 decisões tiveram
veredito. Cada cenário rodou uma vez por modelo: as diferenças pequenas entre
rodadas (por exemplo Sonnet 49 → 46) estão dentro da variação esperada.

## Avaliações com o modelo (execução de scripts)

Os cenários que dependem de insumos (ADR existente, projeto para
documentar, pasta `docs/` com defeitos) passaram a usar o projeto de
exemplo `evals/files/projeto-exemplo/`, que tem defeitos plantados (bloco
de código não fechado, âncora inexistente, link quebrado, porta/endpoint/
versão divergentes do código). Na rodada final com Opus, os scripts
`new_adr.py`, `check_markdown.py`, `scaffold_skill.py`, `validate_skill.py`,
`lint_prompt.py`, `diff_hotspots.py` e `profile_csv.py` foram executados nos
cenários correspondentes.

## Problemas encontrados e corrigidos durante a validação

1. As cercas de código aninhadas (```` ```` ```` envolvendo ```` ``` ````)
   eram interpretadas errado por três scripts. Agora eles seguem a regra do
   CommonMark: mesmo caractere e comprimento maior ou igual.
2. O limiar de ênfase em maiúsculas do linter era permissivo demais: 4
   ocorrências num prompt de 5 linhas não geravam aviso. Ajustado para 3.
3. Blocos de código sem linguagem e `TODO` citado em prosa geravam avisos
   nas próprias skills. Corrigido.
4. Descriptions e cenários ajustados, conforme as seções acima.
5. Rodada por modelo revelou lacunas reais nas instruções, corrigidas:
   `analyzing-tabular-data` devolvia a decisão de tratamento ao usuário
   (agora recomenda um tratamento e mostra com/sem); `debugging-systematically`
   não exigia medir a taxa de falha nem propor `git bisect` em regressões;
   `authoring-agent-skills` podia entregar sem validar (agora obrigatório).
6. Executor de avaliações: limite de 25 turnos (com 15, um cenário longo era
   cortado antes da validação), escrita liberada só dentro do diretório do
   cenário, e juiz recebendo a transcrição completa.

## O que não foi verificado

- Upload no claude.ai e na API: os ZIPs foram gerados e inspecionados, mas
  não enviados (exige a conta do usuário na interface/API).
- Medição de variância com várias execuções do mesmo cenário por modelo:
  cada cenário rodou uma vez por modelo na rodada final.
- Conferência humana item a item das 216 decisões do juiz; foram lidas por
  amostragem as respostas citadas neste relatório.
- Uso real por pessoas do time.
