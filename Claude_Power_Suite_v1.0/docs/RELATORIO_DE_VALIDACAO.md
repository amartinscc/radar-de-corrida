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
| Testes unitários | `python3 -m unittest discover -s tests` | 45 testes, todos aprovados |
| Manifesto do plugin e marketplace | `claude plugin validate .` | Validation passed |
| Instalação do plugin | `claude plugin marketplace add` + `install` | instalado e habilitado, 8 skills carregadas |
| Acionamento com o modelo, 2ª rodada | `tools/run_trigger_evals.py` | 24/24 cenários |
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

45 testes em `tests/test_scripts.py` cobrem todos os scripts e ferramentas:
regras de `name`/`description`, links e referências, parser YAML
alternativo, criação de esqueleto sem sobrescrita, lint de prompt (tags,
variáveis, ênfase, negativas), numeração e substituição de ADR, detecção de
segredos e arquivos sensíveis em diff (inclusive via `git` em repositório
temporário), agrupamento de logs, âncoras e cercas aninhadas em Markdown,
perfil de CSV com codificação cp1252 e decimal brasileiro, empacotamento
ZIP, instalador (com HOME temporário, verificando que skill existente não é
sobrescrita sem `--force`) e o parser do executor de avaliações.

## Validação oficial do plugin

`claude plugin validate .` e `claude plugin validate
.claude-plugin/marketplace.json`: **Validation passed**.

O mesmo comando também roda as verificações do diretório de plugins da
Anthropic, que não mudam o resultado acima e só importam para publicação
nesse diretório:
- **LICENSE_MISSING** (impediria a submissão): nenhuma licença foi escolhida.
  A escolha é do autor; adicione `LICENSE` ou o campo `license` em
  `plugin.json` antes de publicar.
- **ICON_MISSING** (aviso): sem ícone.

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
`claude -p` num diretório temporário contendo só os arquivos do cenário e
registra quais skills foram carregadas. O modelo foi o padrão da sessão.

| Rodada | Descriptions | Acionamento correto |
|---|---|---|
| 1ª | versão inicial | 15/24 |
| 2ª | reescritas com as formulações que falharam | **24/24** |

Falhas da 1ª rodada e causa:
- Perguntas diretas sobre um CSV ("Qual região vendeu mais?"), escolha de
  tecnologia ("PostgreSQL ou MongoDB?"), log + "qual a causa?", pergunta
  sobre prompt injection e código colado na conversa: o modelo respondeu
  sem a skill, porque as descriptions não citavam essas formulações.
- Incidente com várias entregas: só a skill de documentação foi carregada.
- 2 falhas eram do próprio cenário (um pedia revisão de um PR não
  fornecido; outro esperava acionar o orquestrador quando o correto era
  aplicar `reviewing-code` direto). Os cenários foram corrigidos e o campo
  `skills` passou a indicar a skill que **deve** ser acionada.

Cada cenário foi executado uma vez por rodada. Como a saída do modelo
varia, 24/24 é o resultado medido nessa rodada, não uma garantia.

## Avaliações com o modelo (execução de scripts)

Na 2ª rodada, entre os cenários cujo `expected_behavior` pede um script:
- executaram: `scaffold_skill.py`, `validate_skill.py`, `lint_prompt.py`;
- **não executaram, por defeito do cenário**: `new_adr.py` e
  `check_markdown.py` (2 cenários). O cenário não fornece repositório nem
  pasta `docs/`;
- **não executou, por expectativa errada**: `log_signatures.py`. A skill
  manda agrupar só logs volumosos e o log do cenário tem 11 linhas. A
  expectativa foi corrigida;
- **não executaram, por lacuna da skill**: `diff_hotspots.py` e
  `profile_csv.py`. As duas skills passaram a exigir a execução mesmo em
  entradas pequenas. Esses 2 cenários foram reexecutados e os dois scripts
  rodaram.

Os demais itens de `expected_behavior` foram conferidos por leitura em 5
respostas (reviewing-code#1, debugging#1, analyzing#1, engineering-prompts#1,
orchestrating#1): achados com severidade e cenário de falha, causa imediata
separada de hipótese não comprovada, resultado com e sem tratamento do
outlier, prompt reescrito com linter, pipeline com postmortem coerente com
o diagnóstico. As outras 19 respostas não foram conferidas item a item.

## Problemas encontrados e corrigidos durante a validação

1. As cercas de código aninhadas (```` ```` ```` envolvendo ```` ``` ````)
   eram interpretadas errado por três scripts. Agora eles seguem a regra do
   CommonMark: mesmo caractere e comprimento maior ou igual.
2. O limiar de ênfase em maiúsculas do linter era permissivo demais: 4
   ocorrências num prompt de 5 linhas não geravam aviso. Ajustado para 3.
3. Blocos de código sem linguagem e `TODO` citado em prosa geravam avisos
   nas próprias skills. Corrigido.
4. Descriptions e cenários ajustados, conforme as seções acima.

## O que não foi verificado

- Testes com Haiku, Sonnet e Opus separadamente. As rodadas usaram apenas
  o modelo padrão da sessão.
- Upload no claude.ai e na API: os ZIPs foram gerados e inspecionados, mas
  não enviados.
- Execução repetida dos cenários para medir variância.
- Conferência item a item do `expected_behavior` em 19 das 24 respostas.
