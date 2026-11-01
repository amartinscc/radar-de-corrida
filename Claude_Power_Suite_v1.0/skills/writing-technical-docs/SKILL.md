---
name: writing-technical-docs
description: Escreve e revisa documentação técnica — README, guias de instalação, tutoriais, runbooks operacionais, referências de API, postmortems e changelogs — escolhendo o tipo de documento pelo objetivo do leitor, verificando comandos e exemplos contra o código real e validando links, âncoras, títulos e blocos de código com script. Use quando o usuário pedir para documentar um projeto, criar ou melhorar README, escrever guia, runbook, postmortem, changelog ou revisar documentação existente. Technical writing.
license: MIT
---

# Documentação Técnica

## Princípio

Documento bom responde à pergunta de **um leitor específico** que quer
**fazer algo**. Antes de escrever, defina quem lê, o que já sabe e o que
precisa conseguir fazer ao terminar.

## Fluxo de trabalho

```text
- [ ] 1. Definir leitor, objetivo e tipo de documento
- [ ] 2. Levantar fatos no código/sistema (não presumir)
- [ ] 3. Estruturar pelo template do tipo
- [ ] 4. Redigir
- [ ] 5. Verificar comandos e exemplos
- [ ] 6. Validar estrutura com script
- [ ] 7. Entregar com lista do que foi e não foi verificado
```

### 1. Tipo de documento

| Leitor quer... | Tipo | Característica |
|---|---|---|
| aprender fazendo | Tutorial | um caminho feliz, resultado visível rápido |
| resolver uma tarefa específica | Guia (how-to) | passos numerados, pré-requisitos, verificação |
| consultar detalhe exato | Referência | completa, consistente, organizada como o código |
| entender o porquê | Explicação | conceitos, trade-offs, histórico |
| operar sob pressão | Runbook | diagnóstico → ação → verificação → escalonamento |
| saber o que mudou | Changelog | por versão, agrupado por tipo de mudança |
| aprender com incidente | Postmortem | linha do tempo, causa, ações, sem culpados |

Não misture tipos no mesmo documento; ligue um ao outro.
Templates de cada tipo: [reference/templates.md](reference/templates.md).

### 2. Levantar fatos

Leia antes de escrever: manifesto de dependências (versões de runtime),
scripts de build/teste, variáveis de ambiente usadas no código, portas,
comandos de CLI (`--help`), endpoints e schemas. Cada afirmação técnica do
documento deve ter origem verificável. O que não puder ser confirmado vira
pergunta ao usuário ou nota explícita "a confirmar".

### 3–4. Estruturar e redigir

- Primeira tela responde: o que é, para quem, e o comando/passo mais
  importante.
- Um H1 por documento; títulos em ordem sem pular níveis; títulos que
  descrevem a ação ("Configurar o banco"), não rótulos vagos ("Banco").
- Passos numerados, um comando por passo, seguidos do resultado esperado:

  ```bash
  npm test
  ```
  Saída esperada: `Tests: 42 passed`.
- Blocos de código sempre com linguagem; comandos copiáveis sem prompt
  (`$`) e sem saída misturada.
- Placeholders explícitos e consistentes: `<SEU_TOKEN>`; diga onde obter.
- Frases curtas, voz ativa, segunda pessoa no imperativo para instruções.
- Texto de link descritivo ("guia de implantação"), nunca "clique aqui".
- Avisos (perda de dados, custo, irreversibilidade) **antes** do passo
  perigoso.
- Sem datas relativas ("recentemente", "nova versão"); use versão ou data.

### 5. Verificar comandos

Sempre que houver execução disponível, rode os comandos documentados em
ambiente limpo ou descartável e corrija divergências. Comandos destrutivos
ou que dependem de credenciais/produção **não** devem ser executados: marque
como "não executado" na entrega. Nunca declare que um passo funciona sem
tê-lo executado.

### 6. Validar estrutura

```bash
python3 scripts/check_markdown.py docs/ README.md
```

Verifica links relativos quebrados, âncoras inexistentes, blocos de código
não fechados ou sem linguagem, H1 duplicado/ausente, saltos de nível,
links com texto genérico e pendências (`TODO`/`FIXME`/`TBD`). Corrija todos os
ERROS; trate os AVISOS (use `--strict` para que reprovem). Links http(s)
não são testados pelo script (ele não acessa a rede).

### 7. Entrega

Informe: arquivos criados/alterados, comandos verificados por execução,
itens não verificados e perguntas em aberto.

## Revisão de documentação existente

Avalie nesta ordem e reporte achados com arquivo:linha:
1. **Correção**: comando, versão, caminho ou opção desatualizada em relação
   ao código.
2. **Completude**: pré-requisito ausente, passo pulado, erro comum não
   tratado.
3. **Encontrabilidade**: título, sumário, links entre documentos.
4. **Clareza**: frases ambíguas, jargão sem definição.
5. **Estrutura**: resultado do `check_markdown.py`.
