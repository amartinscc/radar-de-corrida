# Instalação

Skills não sincronizam entre superfícies: instale em cada uma que for usar.
Todos os comandos abaixo partem da pasta `Claude_Power_Suite_v1.0/`.

## Sumário
- Claude Code como plugin
- Claude Code como skills pessoais ou de projeto
- claude.ai
- API da Anthropic
- Verificar a instalação
- Desinstalar

## Claude Code como plugin

O plugin dá namespace às skills (`/power-suite:reviewing-code`) e evita
conflito com skills de mesmo nome.

Testar sem instalar, só nesta sessão:

```bash
claude --plugin-dir .
```

Instalar a partir desta pasta, que também é um marketplace:

```bash
claude plugin marketplace add ./
claude plugin install power-suite@power-suite-marketplace
```

Validar os manifestos:

```bash
claude plugin validate .
```

## Claude Code como skills pessoais ou de projeto

```bash
tools/install.sh --personal                 # ~/.claude/skills/
tools/install.sh --project ../meu-projeto   # ../meu-projeto/.claude/skills/
tools/install.sh --personal --only reviewing-code,debugging-systematically
```

- `--dry-run` mostra o que seria copiado.
- Uma skill já existente no destino é pulada; `--force` substitui.
- O script valida todas as skills antes de copiar.
- Skills de projeto devem ser versionadas no repositório do projeto para que
  o time as receba.

## claude.ai

Requer plano com execução de código habilitada.

1. Gere os pacotes:
   ```bash
   python3 tools/package_skills.py
   ```
   Saída esperada: um `dist/<skill>.zip` por skill, cada um com a pasta da
   skill na raiz.
2. No claude.ai, abra Configurações > Recursos e envie cada ZIP desejado.
3. Skills no claude.ai são individuais: cada pessoa do time faz o próprio
   upload.

## API da Anthropic

Skills na API são enviadas pelos endpoints `/v1/skills` e usadas listando o
`skill_id` no parâmetro `container`, junto com a ferramenta de execução de
código. Ficam disponíveis para todo o workspace. Consulte o guia "Using
Agent Skills with the API" em platform.claude.com para o formato atual das
requisições e os cabeçalhos beta exigidos; este projeto não inclui cliente
de upload. No contêiner da API não há rede nem instalação de pacotes — os
scripts desta suíte usam só a biblioteca padrão por esse motivo.

## Verificar a instalação

No Claude Code, peça algo que corresponda a uma description, por exemplo
"revise o diff da minha branch", e confirme que a skill `reviewing-code` foi
carregada; ou chame diretamente `/reviewing-code` (skills avulsas) ou
`/power-suite:reviewing-code` (plugin).

## Desinstalar

- Skills avulsas: remova as pastas copiadas de `~/.claude/skills/` ou
  `.claude/skills/`.
- Plugin: `claude plugin uninstall power-suite`.
- claude.ai: remova as skills em Configurações > Recursos.
