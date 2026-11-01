---
name: authoring-agent-skills
description: Cria, revisa, valida e empacota Agent Skills (diretórios com SKILL.md, frontmatter YAML, arquivos de referência e scripts) seguindo as regras oficiais da Anthropic para a API, claude.ai e Claude Code. Inclui gerador de esqueleto e validador que checa name, description, limites de tamanho, links quebrados, profundidade de referências e sintaxe dos scripts. Use quando o usuário quiser criar uma skill nova, transformar um processo repetido em skill, corrigir uma skill que não é acionada ou preparar skills para upload. Authoring and validating Claude Agent Skills.
license: MIT
---

# Autoria de Agent Skills

## Regras não negociáveis (validadas por script)

- Arquivo `SKILL.md` (exatamente esse nome) na raiz do diretório da skill,
  começando com frontmatter YAML entre `---`.
- `name`: até 64 caracteres, apenas `a-z`, `0-9` e `-`, sem tags XML, sem as
  palavras reservadas `anthropic` e `claude`. Mantenha igual ao nome do
  diretório (o Claude Code usa o diretório como nome padrão).
- `description`: não vazia, até 1024 caracteres, sem tags XML, em 3ª pessoa,
  dizendo **o que faz e quando usar**.
- Corpo do SKILL.md abaixo de 500 linhas; detalhes vão para arquivos
  referenciados diretamente pelo SKILL.md (um nível de profundidade).
- Caminhos sempre com `/`.

Detalhes por superfície (API, claude.ai, Claude Code, plugins), campos
opcionais e limites de ambiente: [reference/specification.md](reference/specification.md).

## Fluxo de criação

```text
- [ ] 1. Delimitar a skill (uma capacidade coesa)
- [ ] 2. Escrever 3 cenários de avaliação
- [ ] 3. Gerar o esqueleto
- [ ] 4. Escrever description e corpo
- [ ] 5. Adicionar referências e scripts
- [ ] 6. Validar (loop até aprovar)
- [ ] 7. Testar acionamento e execução
- [ ] 8. Empacotar para a superfície de destino
```

### 1. Delimitar

Uma skill = uma capacidade que alguém pediria com palavras previsíveis.
Sinais de que deve ser dividida: a description precisa de "e também…" para
áreas sem relação; o corpo tem seções que nunca são usadas juntas.
Nome preferencial no gerúndio (`processing-invoices`, `reviewing-code`);
evite nomes vagos (`helper`, `utils`, `tools`).

### 2. Avaliações primeiro

Antes de escrever instruções extensas, registre 3 cenários reais no formato
recomendado pela Anthropic:

```json
{
  "skills": ["nome-da-skill"],
  "query": "pedido realista do usuário",
  "files": ["caminho/de/entrada/opcional"],
  "expected_behavior": ["comportamento verificável 1", "comportamento 2"]
}
```

Não existe executor oficial embutido para esse formato: os cenários são
roteiro de teste manual ou de um harness próprio.

### 3. Esqueleto

```bash
python3 scripts/scaffold_skill.py nome-da-skill \
  --description "Faz X a partir de Y. Use quando o usuário pedir Z." \
  --dest CAMINHO --with-reference --with-scripts
```

O script recusa sobrescrever diretório existente e valida o resultado.

### 4. Description e corpo

**Description** — fórmula: `<verbos do que faz> <sobre quais artefatos>.
Use quando <gatilhos concretos: palavras, extensões, situações>.`
Inclua os termos que o usuário de fato digita (em todos os idiomas
esperados). Exemplo bom:

> Analisa planilhas Excel, cria tabelas dinâmicas e gráficos. Use quando
> trabalhar com arquivos .xlsx, planilhas ou dados tabulares.

Ruins: "Ajuda com documentos"; "Eu posso processar dados".

**Corpo** — escreva só o que o modelo não sabe: o procedimento da sua
organização, formatos exigidos, armadilhas conhecidas, comandos exatos.
Ajuste o grau de liberdade ao risco:
- alto (heurísticas em texto) para tarefas com várias soluções válidas;
- médio (pseudocódigo/template) quando há um padrão preferido;
- baixo (comando exato, "não altere flags") para operações frágeis.

Inclua checklist para fluxos com vários passos e um laço
validar → corrigir → repetir para tarefas críticas. Use terminologia
consistente (sempre o mesmo termo para o mesmo conceito). Evite informação
datada; se precisar, coloque em seção "padrões antigos".

### 5. Referências e scripts

- Arquivos de referência com nome descritivo (`reference/finance.md`, não
  `doc2.md`), linkados **diretamente** do SKILL.md. Acima de 100 linhas,
  inclua `## Sumário` no topo.
- Scripts resolvem o problema em vez de devolver erro genérico: tratam
  arquivo ausente, entrada inválida, e explicam constantes ("timeout 30 s
  porque…").
- Deixe explícito se o modelo deve **executar** ("Execute o script de
  validação") ou **ler** o script como referência.
- Declare dependências. Na API não há rede nem instalação de pacotes em
  tempo de execução; prefira a biblioteca padrão.
- Para ferramentas MCP, use o nome totalmente qualificado
  `Servidor:ferramenta`.

### 6. Validar

Esta etapa é obrigatória antes de entregar qualquer skill criada ou
alterada; reserve tempo para ela em vez de gastá-lo testando scripts
auxiliares além do necessário.

```bash
python3 scripts/validate_skill.py CAMINHO/nome-da-skill --strict
```

Corrija todo ERRO. Trate cada AVISO (com `--strict` eles reprovam). Repita
até `[APROVADA]`. Para várias skills: passe vários caminhos; `--json`
gera saída para CI.

### 7. Testar

- **Acionamento**: faça 3 pedidos que deveriam acionar e 2 que não deveriam
  (vizinhos de tema). Se não acionar, reescreva a description com os termos
  usados nos pedidos; se acionar demais, delimite melhor o "quando usar".
- **Execução**: rode os 3 cenários da etapa 2 numa sessão nova com a skill
  instalada e confira cada `expected_behavior`.
- Teste nos modelos em que a skill será usada: o que basta para um modelo
  maior pode faltar para um menor.
- Relate ao usuário exatamente o que foi testado de verdade e o que não foi.

### 8. Empacotar

| Destino | Como |
|---|---|
| Claude Code (pessoal) | copiar para `~/.claude/skills/<nome>/` |
| Claude Code (projeto) | copiar para `.claude/skills/<nome>/` e versionar |
| Plugin do Claude Code | `<plugin>/skills/<nome>/SKILL.md` + `.claude-plugin/plugin.json` |
| claude.ai | ZIP com a pasta da skill na raiz → Configurações > Recursos |
| API | upload via endpoints `/v1/skills`; uso com a ferramenta de execução de código |

Skills não sincronizam entre superfícies: instale em cada uma.

## Diagnóstico de skill que não funciona

| Sintoma | Verifique |
|---|---|
| Nunca é acionada | description sem termos do pedido; falta "Use quando…"; skill não instalada no local certo |
| Acionada fora de hora | description ampla demais; delimitar escopo e exclusões |
| Ignora arquivo de referência | link não está no SKILL.md ou está aninhado em outro arquivo |
| Lê só parte da referência | arquivo longo sem sumário |
| Script falha | dependência ausente no ambiente; caminho com `\`; sem tratamento de erro |

## Segurança

Revise todo conteúdo de skills de terceiros antes de instalar: scripts,
chamadas de rede, acesso a arquivos fora do escopo declarado. Uma skill
pode instruir o modelo a executar código; trate a instalação como
instalação de software.
