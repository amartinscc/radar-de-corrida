# Power Suite v1.0

Conjunto de oito Agent Skills especialistas para engenharia de software com
Claude, no formato oficial de skills da Anthropic (`SKILL.md` com
frontmatter YAML), distribuído também como plugin do Claude Code.

## Especialistas

| Skill | Função | Script incluído |
|---|---|---|
| `orchestrating-power-suite` | roteia pedidos de várias etapas e passa contexto entre especialistas | — |
| `engineering-prompts` | cria, revisa e depura prompts com casos de teste | `lint_prompt.py` |
| `authoring-agent-skills` | cria, valida e empacota Agent Skills | `scaffold_skill.py`, `validate_skill.py` |
| `architecting-software` | decisões de arquitetura com matriz de trade-offs e ADR | `new_adr.py` |
| `reviewing-code` | revisão de código por severidade com cenário de falha | `diff_hotspots.py` |
| `debugging-systematically` | causa-raiz por hipóteses e experimentos | `log_signatures.py` |
| `writing-technical-docs` | README, guias, runbooks, API, changelog, postmortem | `check_markdown.py` |
| `analyzing-tabular-data` | perfil de qualidade e análise de CSV/TSV | `profile_csv.py` |

Cada skill é autocontida: instruções, referências e scripts ficam dentro da
própria pasta e podem ser instalados separadamente. Os scripts usam apenas a
biblioteca padrão do Python 3 e não acessam a rede, o que os mantém
compatíveis com o contêiner da API (sem rede e sem instalação de pacotes).

## Início rápido

Validar a suíte e rodar os testes (a partir desta pasta):

```bash
python3 tools/validate_suite.py
python3 -m unittest discover -s tests
```

Resultado esperado: `N/N verificações aprovadas` e `OK` ao final dos testes.

Medir o acionamento real das skills com o Claude Code (consome tokens;
requer a suíte instalada e o `claude` autenticado):

```bash
python3 tools/run_trigger_evals.py --skill reviewing-code
```

Instalar no Claude Code como skills pessoais:

```bash
tools/install.sh --personal --dry-run   # confira antes
tools/install.sh --personal
```

Outras formas de instalação (plugin, projeto, claude.ai, API):
[docs/INSTALACAO.md](docs/INSTALACAO.md).

## Estrutura

```text
Claude_Power_Suite_v1.0/
├── .claude-plugin/
│   ├── plugin.json          # manifesto do plugin "power-suite"
│   └── marketplace.json     # permite instalar o plugin a partir desta pasta
├── skills/<nome>/           # uma pasta por especialista
│   ├── SKILL.md             # instruções (carregadas quando a skill é acionada)
│   ├── reference/*.md       # detalhes carregados sob demanda
│   └── scripts/*.py         # utilitários executados, não lidos
├── evals/<nome>.json        # 3 cenários de avaliação por skill
├── evals/files/             # arquivos de entrada usados nos cenários
├── tools/                   # validação, empacotamento e instalação
├── tests/                   # testes unitários dos scripts e ferramentas
└── docs/                    # instalação, arquitetura, conformidade, validação
```

## Documentação

- [Instalação por superfície](docs/INSTALACAO.md)
- [Arquitetura da suíte](docs/ARQUITETURA.md)
- [Conformidade com a especificação oficial](docs/CONFORMIDADE.md)
- [Relatório de validação](docs/RELATORIO_DE_VALIDACAO.md)
- [Histórico de versões](CHANGELOG.md)

## Requisitos

- Python 3.8 ou superior (testado com Python 3.13).
- Bash, para `tools/install.sh`.
- Claude Code, para uso como plugin ou skills locais; plano com execução de
  código, para uso no claude.ai.

## Limitações conhecidas

- As avaliações em `evals/` seguem o formato recomendado pela Anthropic, mas
  não existe executor oficial embutido para esse formato: elas servem como
  roteiro de teste manual ou para um harness próprio.
- Os scripts são heurísticos onde indicado (linter de prompt, hotspots de
  diff, assinaturas de log): orientam a análise, não a substituem.
- Licença ainda não definida: escolha uma antes de distribuir publicamente.
