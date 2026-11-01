# Conformidade com a especificação oficial

Pesquisa realizada em 2026-11-01 nas páginas oficiais abaixo. Reconfira-as
antes de uma nova versão: os limites podem mudar.

| Fonte | Endereço |
|---|---|
| Agent Skills — visão geral | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview |
| Boas práticas de autoria | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices |
| Skills no Claude Code | https://code.claude.com/docs/en/skills |
| Manifesto de plugin | https://code.claude.com/docs/en/plugins-reference |
| Marketplace | https://code.claude.com/docs/en/plugins/marketplace-reference.md |

A especificação aberta em agentskills.io não pôde ser consultada: o domínio
não estava liberado na rede deste ambiente. As regras implementadas vêm
apenas das fontes acima.

## Regras e como cada uma é garantida

| Regra oficial | Onde é verificada | Situação |
|---|---|---|
| `SKILL.md` com frontmatter YAML na primeira linha | `validate_skill.py` (erro) | 8/8 skills |
| `name` ≤ 64, `[a-z0-9-]`, sem XML, sem `anthropic`/`claude` | `validate_skill.py` (erro) | 8/8 |
| `description` não vazia, ≤ 1024, sem XML | `validate_skill.py` (erro) | 8/8 |
| description em 3ª pessoa com "o que faz" e "quando usar" | `validate_skill.py` (aviso heurístico) | 8/8 |
| description + `when_to_use` ≤ 1536 no Claude Code | `validate_skill.py` (aviso) | 8/8 |
| corpo do SKILL.md < 500 linhas | `validate_skill.py` (aviso) | 8/8 |
| referências a um nível do SKILL.md | `validate_skill.py` (aviso) | 8/8 |
| referência > 100 linhas com sumário | `validate_skill.py` (aviso) | 8/8 |
| caminhos com `/` | `validate_skill.py` (erro em links) | 8/8 |
| nomes de skill no gerúndio | revisão manual | 8/8 (todas no gerúndio: `orchestrating-`, `engineering-`, `authoring-`, `architecting-`, `reviewing-`, `debugging-`, `writing-`, `analyzing-`) |
| pelo menos 3 avaliações por skill | `validate_suite.py` | 24 cenários |
| scripts tratam erros e documentam constantes | testes unitários + revisão | ver relatório |
| sem dependências fora da biblioteca padrão | revisão + execução dos testes | ok |
| `plugin.json` com `name` em kebab-case, fora de prefixos reservados | `validate_suite.py` e `claude plugin validate` | ver relatório |
| `marketplace.json` com `name`, `owner`, `plugins[].name/source` | `validate_suite.py` e `claude plugin validate` | ver relatório |

Os avisos acima são executados em modo estrito na suíte: qualquer aviso
reprova a validação.

## Itens do checklist oficial que dependem de uso real

O checklist oficial pede testes com os modelos Haiku, Sonnet e Opus e com
uso real. Esses testes exigem sessões do Claude com as skills instaladas e
**não foram executados** na construção desta versão; os cenários em
`evals/` são o roteiro para fazê-los.
