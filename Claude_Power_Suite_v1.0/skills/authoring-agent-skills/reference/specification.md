# Especificação de Agent Skills por superfície

Fontes consultadas: platform.claude.com/docs (Agent Skills — overview e
best practices) e code.claude.com/docs (Skills, Plugins reference,
Marketplace reference). Reconfira essas páginas antes de depender de um
limite em produção: o produto evolui.

## Sumário
- Estrutura mínima
- Campos obrigatórios (todas as superfícies)
- Campos adicionais do Claude Code
- Carregamento progressivo e orçamento de contexto
- Onde instalar em cada superfície
- Ambiente de execução por superfície
- Empacotamento em plugin do Claude Code
- Checklist oficial de qualidade

## Estrutura mínima

```text
minha-skill/
├── SKILL.md            # obrigatório
├── reference/          # opcional: markdown carregado sob demanda
│   └── topico.md
├── scripts/            # opcional: executados via bash; o código não entra no contexto
│   └── ferramenta.py
└── assets/             # opcional: templates, esquemas, dados
```

`SKILL.md`:

```markdown
---
name: minha-skill
description: Faz X com Y. Use quando o usuário pedir Z.
---

# Título

## Instruções
...
```

## Campos obrigatórios (todas as superfícies)

| Campo | Regras |
|---|---|
| `name` | máx. 64 caracteres; apenas minúsculas, números e hífens; sem tags XML; sem `anthropic` ou `claude` |
| `description` | não vazio; máx. 1024 caracteres; sem tags XML; deve dizer o que faz e quando usar; 3ª pessoa |

No Claude Code todos os campos são tecnicamente opcionais (`name` assume o
nome do diretório e `description` assume o primeiro parágrafo), mas a API e
o claude.ai exigem ambos — preencha sempre.

## Campos adicionais do Claude Code

Ignorados por outras superfícies. Campos desconhecidos são ignorados sem erro.

| Campo | Efeito |
|---|---|
| `when_to_use` | texto extra de acionamento; somado à description, truncado em 1536 caracteres na listagem |
| `argument-hint` | dica de argumentos no autocomplete do `/` |
| `arguments` | argumentos posicionais nomeados para substituição `$nome` |
| `disable-model-invocation` | `true` impede o carregamento automático (só via `/nome`) |
| `user-invocable` | `false` oculta do menu `/` (só o modelo aciona) |
| `allowed-tools` | ferramentas liberadas sem pedir permissão no turno da skill |
| `disallowed-tools` | ferramentas removidas enquanto a skill está ativa |
| `model` / `effort` | modelo / nível de esforço para o restante do turno |
| `context: fork` + `agent` | executa em subagente isolado |
| `paths` | globs que limitam a ativação automática a certos arquivos |
| `hooks`, `shell` | hooks registrados pela skill; shell dos blocos `!` |
| `metadata`, `license`, `compatibility` | informativos; `compatibility` até 500 caracteres |

## Carregamento progressivo e orçamento de contexto

| Nível | Quando carrega | Custo |
|---|---|---|
| 1. Metadados (`name`, `description`) | sempre, no início | ~100 tokens por skill |
| 2. Corpo do SKILL.md | quando a skill é acionada | recomendado < 5k tokens / < 500 linhas |
| 3. Referências e scripts | quando lidos/executados | só o que for lido; scripts custam só a saída |

No Claude Code, após compactação, cada skill reanexada mantém os primeiros
5.000 tokens, com orçamento combinado de 25.000 tokens.

Consequências práticas:
- O que precisa estar sempre disponível vai no SKILL.md; o resto, em
  referências por tópico.
- Referências aninhadas (A → B → C) podem ser lidas parcialmente; mantenha
  tudo a um nível do SKILL.md.

## Onde instalar em cada superfície

| Superfície | Local / mecanismo | Compartilhamento |
|---|---|---|
| Claude Code — pessoal | `~/.claude/skills/<nome>/SKILL.md` | só o usuário, todos os projetos locais |
| Claude Code — projeto | `.claude/skills/<nome>/SKILL.md` | quem clona o repositório |
| Claude Code — plugin | `<plugin>/skills/<nome>/SKILL.md` | onde o plugin estiver habilitado, como `/plugin:skill` |
| claude.ai | upload de ZIP em Configurações > Recursos (planos com execução de código) | individual |
| API | endpoints `/v1/skills`; referenciar `skill_id` no parâmetro `container` com a ferramenta de execução de código | todo o workspace |

Precedência no Claude Code: corporativa > pessoal > projeto. Skills de
plugin têm namespace e não conflitam. O Claude Code observa os diretórios
de skills e recarrega alterações na sessão; um diretório de skills
totalmente novo pode exigir `/reload-skills`.

## Ambiente de execução por superfície

| Superfície | Rede | Pacotes |
|---|---|---|
| API | sem acesso à rede | apenas os pré-instalados no contêiner de execução de código |
| claude.ai | depende das configurações do usuário/admin | pode instalar de npm/PyPI quando a rede permitir |
| Claude Code | mesma rede da máquina | instalar localmente, nunca globalmente |

Scripts portáveis entre as três: Python 3 com biblioteca padrão, sem rede.

## Empacotamento em plugin do Claude Code

```text
meu-plugin/
├── .claude-plugin/
│   ├── plugin.json        # {"name": "meu-plugin", "version": "1.0.0", ...}
│   └── marketplace.json   # opcional: torna o diretório um marketplace
└── skills/
    └── minha-skill/SKILL.md
```

- `plugin.json`: só `name` é obrigatório (kebab-case). Nomes que começam com
  `claude-` ou `anthropic-` são rejeitados pelo validador.
- `marketplace.json`: exige `name`, `owner.name` e `plugins[]` com `name` e
  `source` (caminho relativo começando com `./`).
- Validação oficial: `claude plugin validate CAMINHO`.

## Checklist oficial de qualidade

Qualidade:
- description específica, com o que faz e quando usar
- corpo < 500 linhas; detalhes em arquivos separados
- sem informação datada (ou em seção de "padrões antigos")
- terminologia consistente; exemplos concretos
- referências a um nível; fluxos com passos claros

Código:
- scripts resolvem erros em vez de repassá-los
- sem constantes mágicas; valores justificados
- dependências listadas e disponíveis
- caminhos com `/`; validação em operações críticas

Testes:
- ao menos 3 avaliações
- testada nos modelos-alvo
- testada com uso real
