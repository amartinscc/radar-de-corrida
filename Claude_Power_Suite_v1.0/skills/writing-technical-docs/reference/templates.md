# Templates por tipo de documento

## Sumário
- README de projeto
- Guia (how-to)
- Runbook operacional
- Referência de endpoint de API
- Changelog
- Postmortem

## README de projeto

````markdown
# <Nome do projeto>

<Uma frase: o que faz e para quem.>

## Início rápido

```bash
<comando de instalação>
<comando para rodar>
```

Resultado esperado: <o que o leitor vê>.

## Requisitos
- <runtime e versão mínima, conforme o manifesto>
- <serviços externos: banco, fila, chaves>

## Configuração
| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `DATABASE_URL` | sim | — | conexão PostgreSQL |

## Uso
<exemplos dos 2–3 casos mais comuns>

## Desenvolvimento
```bash
<rodar testes>
<rodar lint>
```

## Arquitetura
<parágrafo curto + link para documento de arquitetura/ADRs>

## Contribuição e licença
<links>
````

## Guia (how-to)

````markdown
# Como <realizar tarefa>

<Para quem é e quando usar este guia, em 1–2 frases.>

## Pré-requisitos
- <acesso, ferramenta, versão>

## Passos

1. <Ação no imperativo.>
   ```bash
   <comando>
   ```
   Saída esperada: `<trecho>`.
2. <Ação.>

## Verificar
<como confirmar que deu certo>

## Problemas comuns
| Sintoma | Causa | Solução |
|---|---|---|
````

## Runbook operacional

````markdown
# Runbook: <alerta ou situação>

- Severidade: <SEV1–SEV4>
- Responsável: <time/escala>
- Última revisão: <AAAA-MM-DD>

## Impacto
<o que o usuário percebe>

## Diagnóstico
1. <Painel/consulta> — se <condição>, vá para Ação A.
2. <Comando> — se <condição>, vá para Ação B.

## Ações
### Ação A: <nome>
> Aviso: <risco da ação, se houver>
```bash
<comando exato>
```
Verificação: <métrica/comando que confirma a recuperação>.

## Escalonamento
Se não recuperar em <N> minutos: <quem acionar e como>.

## Pós-incidente
- [ ] Registrar linha do tempo
- [ ] Abrir postmortem se SEV1/SEV2
````

## Referência de endpoint de API

````markdown
## `POST /v1/orders`

Cria um pedido.

**Autenticação:** Bearer token com escopo `orders:write`.

**Corpo**
| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `customer_id` | string | sim | ID do cliente |
| `items` | array | sim | 1–100 itens |

**Exemplo**
```bash
curl -X POST https://api.exemplo.com/v1/orders \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "c_123", "items": [{"sku": "A1", "qty": 2}]}'
```

**Respostas**
| Status | Quando | Corpo |
|---|---|---|
| 201 | criado | `{"id": "o_456", "status": "pending"}` |
| 400 | validação | `{"error": "items_required"}` |
| 409 | chave de idempotência repetida com corpo diferente | ... |
````

## Changelog

Formato baseado em "Keep a Changelog" com versionamento semântico:

````markdown
# Changelog

## [1.4.0] - 2026-03-10
### Adicionado
- Exportação de relatórios em CSV (#231).
### Alterado
- Timeout padrão de 10 s para 30 s.
### Corrigido
- Duplicidade de cobrança em retry (#240).
### Removido
- Endpoint `/v0/orders` (descontinuado desde 1.2.0).
### Segurança
- Atualização de dependência com CVE crítica.
````

Regras: entradas escritas para quem **usa** o software; mudanças
incompatíveis destacadas no topo da versão com instrução de migração.

## Postmortem

````markdown
# Postmortem: <título> (<AAAA-MM-DD>)

## Resumo
<o que aconteceu, impacto, duração, em 3–4 frases>

## Impacto
- Usuários afetados: <número/percentual>
- Duração: <início–fim, com fuso>
- Dados: <perda/corrupção ou "nenhuma">

## Linha do tempo
| Horário | Evento |
|---|---|

## Causa-raiz
<mecanismo técnico e fatores contribuintes; foco em sistemas e processos, não em pessoas>

## O que funcionou / o que não funcionou
## Ações
| Ação | Tipo (prevenir/detectar/mitigar) | Responsável | Prazo |
|---|---|---|---|
````
