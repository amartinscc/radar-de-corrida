---
name: orchestrating-power-suite
description: Roteia pedidos complexos ou de várias etapas para os especialistas da Power Suite (prompts, skills, arquitetura, revisão de código, depuração, documentação técnica, dados tabulares) e coordena a passagem de contexto entre eles. Use quando o pedido envolver duas ou mais dessas áreas, quando o usuário pedir um "plano completo", um "pipeline" ou "do zero até a entrega", ou quando não estiver claro qual especialista aplicar. Routes multi-step software requests across the suite specialists.
---

# Orquestrador da Power Suite

Esta skill decide **qual especialista aplicar, em que ordem e com que contexto**.
Ela não executa o trabalho técnico: cada especialista tem seu próprio SKILL.md
completo e independente.

## Especialistas disponíveis

| Especialista (skill) | Aplica-se quando o pedido é sobre... | Entrega principal |
|---|---|---|
| `engineering-prompts` | escrever, revisar ou depurar prompts de sistema, prompts de tarefa, templates | prompt final + casos de teste |
| `authoring-agent-skills` | criar, validar ou empacotar uma Agent Skill (SKILL.md) | diretório de skill validado |
| `architecting-software` | desenhar sistema, escolher tecnologia, avaliar trade-offs, registrar decisão | visão de arquitetura + ADR |
| `reviewing-code` | revisar diff, PR, commit ou arquivo antes de integrar | achados priorizados por severidade |
| `debugging-systematically` | erro, falha, regressão, teste intermitente, comportamento inesperado | causa-raiz comprovada + correção |
| `writing-technical-docs` | README, guia, runbook, referência de API, changelog | documento verificado |
| `analyzing-tabular-data` | CSV/TSV/planilha exportada: qualidade, perfil, análise | perfil + achados com números |

Se só um especialista se aplica, **não orquestre**: aplique diretamente a skill
correspondente e siga as instruções dela.

## Procedimento de roteamento

1. **Classifique o pedido** em uma ou mais linhas da tabela acima. Use o verbo
   e o artefato como pista: "por que quebra" → depuração; "está bom para
   mergear?" → revisão; "como devo estruturar" → arquitetura.
2. **Identifique dependências** entre as partes. Uma parte depende de outra
   quando precisa do artefato que ela produz (ex.: a documentação depende da
   decisão de arquitetura).
3. **Ordene** usando os pipelines padrão abaixo; ajuste só se houver motivo
   explícito no pedido.
4. **Declare o plano ao usuário** em até 5 linhas antes de executar:
   especialistas, ordem e o que cada um entrega.
5. **Execute uma etapa por vez**, carregando a skill do especialista e
   passando o *pacote de contexto* (seção seguinte).
6. **Verifique a saída de cada etapa** contra o critério de pronto antes de
   seguir. Se falhar, repita a etapa — não avance com artefato incompleto.

## Pacote de contexto entre etapas

Ao passar de um especialista para o próximo, resuma em um bloco:

```text
CONTEXTO PARA <próximo especialista>
- Objetivo do usuário: <1 frase, nas palavras dele>
- Artefatos produzidos: <caminhos de arquivo ou resumo>
- Decisões já tomadas (não reabrir): <lista>
- Restrições: <prazo, stack, compatibilidade, idioma>
- Perguntas em aberto: <lista ou "nenhuma">
```

Decisões já tomadas não são reabertas por etapas seguintes, a menos que a
etapa encontre evidência de que a decisão está errada; nesse caso, pare e
reporte ao usuário com a evidência.

## Pipelines padrão

**Nova funcionalidade**
`architecting-software` (opções + ADR) → implementação → `reviewing-code`
→ `writing-technical-docs` (README/guia atualizado).

**Incidente em produção**
`analyzing-tabular-data` (se houver métricas/exports) e/ou
`debugging-systematically` (causa-raiz) → correção → `reviewing-code`
→ `writing-technical-docs` (postmortem/runbook).

**Automação com LLM**
`engineering-prompts` (prompt + casos de teste) → `authoring-agent-skills`
(empacotar como skill, se for reutilizável) → `writing-technical-docs`.

**Auditoria de repositório**
`reviewing-code` (amostra dos módulos críticos) → `architecting-software`
(riscos estruturais) → `writing-technical-docs` (relatório).

## Critério de pronto da orquestração

```text
- [ ] Cada parte do pedido foi atribuída a exatamente um especialista
- [ ] Toda etapa terminou com o critério de pronto do próprio especialista
- [ ] Nenhuma decisão registrada foi contradita por etapa posterior
- [ ] Resposta final lista artefatos entregues e pendências reais
```

## Limites honestos

- As skills orientam o raciocínio e trazem scripts locais; elas **não**
  concedem acesso a sistemas que a sessão não tem (repositórios, bancos,
  rede). Na API da Anthropic, skills rodam sem acesso à rede.
- Se um especialista exigir executar um script e não houver ferramenta de
  execução de código disponível, siga o procedimento manual descrito na
  própria skill e diga ao usuário que a verificação automática não foi feita.
