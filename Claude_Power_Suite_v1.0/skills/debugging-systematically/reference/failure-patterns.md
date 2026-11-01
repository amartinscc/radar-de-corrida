# Causas frequentes por sintoma

## Sumário
- Funciona localmente, falha em outro ambiente
- Falha intermitente
- Começou a falhar sem mudança no código
- Lentidão / degradação
- Consumo crescente de memória
- Dados errados ou corrompidos
- Erros de rede e integração
- Testes que falham só na suíte completa
- Erros de build e dependências
- Experimentos de confirmação rápida

## Funciona localmente, falha em outro ambiente
- Variáveis de ambiente/configuração diferentes ou ausentes.
- Versões diferentes de runtime, SO, biblioteca nativa, banco.
- Sistema de arquivos sensível a maiúsculas (Linux) vs. não (macOS/Windows).
- Fuso horário, locale (separador decimal, ordenação de strings).
- Permissões de usuário/arquivo; diretório somente leitura no contêiner.
- Dados de produção com casos que não existem no ambiente local.
- **Confirme**: imprimir versões e configuração efetiva nos dois ambientes
  e comparar com `diff`.

## Falha intermitente
- Condição de corrida / estado compartilhado entre threads ou requisições.
- Dependência de ordem de iteração (sets, mapas) ou de ordem de testes.
- Tempo: `sleep` em vez de espera por condição; relógio real em teste;
  virada de dia/mês; expiração de token.
- Recurso esgotado: pool de conexões, descritores de arquivo, limite de taxa.
- Rede: timeouts curtos, DNS, balanceador com instância ruim.
- **Confirme**: repetir N vezes registrando taxa; fixar semente; rodar em
  série vs. paralelo; isolar a instância.

## Começou a falhar sem mudança no código
- Dependência sem versão fixada atualizou (lockfile ausente).
- Dados novos com formato inesperado (campo nulo, encoding, tamanho).
- Certificado expirado, credencial rotacionada, cota atingida.
- Mudança de infraestrutura/configuração feita fora do repositório.
- Crescimento de volume ultrapassando um limite (índice, memória, timeout).
- **Confirme**: linha do tempo de mudanças (deploys, configs, dados,
  provedores) alinhada ao início do sintoma.

## Lentidão / degradação
- Consulta sem índice ou plano de execução que mudou com o volume.
- N+1 consultas; chamadas remotas em série que poderiam ser paralelas.
- Contenção de locks; pool de conexões pequeno demais.
- GC excessivo por alocação em laço quente.
- Cache frio após deploy ou cache com baixa taxa de acerto.
- **Confirme**: profiler ou trace da requisição lenta; `EXPLAIN ANALYZE`;
  comparar latência por componente.

## Consumo crescente de memória
- Cache sem limite; listeners/callbacks registrados e nunca removidos.
- Referências mantidas em estruturas globais; closures capturando objetos
  grandes.
- Leitura de arquivo/resposta inteira na memória.
- **Confirme**: snapshots de heap em dois momentos e comparar os tipos que
  mais cresceram.

## Dados errados ou corrompidos
- Conversão de tipos: ponto flutuante para dinheiro, truncamento, overflow.
- Encoding (UTF-8 vs. Latin-1), BOM, normalização Unicode.
- Fuso horário na gravação vs. na leitura.
- Escritas concorrentes sem controle de versão (última escrita vence).
- Migração/backfill parcial.
- **Confirme**: rastrear um registro concreto pela pipeline, comparando o
  valor em cada fronteira.

## Erros de rede e integração
- Timeout menor que a latência real no pico; retry multiplicando carga.
- Contrato mudou do outro lado (campo renomeado, novo obrigatório).
- TLS: cadeia de certificados, SNI, proxy corporativo.
- Limites de taxa (HTTP 429) e cotas.
- **Confirme**: reproduzir a chamada isolada (curl) com os mesmos headers e
  payload; checar logs do outro lado pelo ID de correlação.

## Testes que falham só na suíte completa
- Estado vazando entre testes (banco, arquivos, variáveis globais, mocks
  não restaurados).
- Ordem de execução; testes paralelos usando o mesmo recurso.
- **Confirme**: rodar o teste isolado e depois junto com o anterior;
  bisseção na lista de testes.

## Erros de build e dependências
- Cache de build desatualizado; artefato gerado antigo.
- Conflito de versões transitivas.
- Diferença entre lockfile e manifesto.
- **Confirme**: build limpo em diretório novo; árvore de dependências
  (`npm ls`, `pip show`, `go mod graph`, `mvn dependency:tree`).

## Experimentos de confirmação rápida
| Pergunta | Experimento |
|---|---|
| É o código ou o ambiente? | rodar a mesma versão nos dois ambientes com a mesma entrada |
| Qual commit introduziu? | `git bisect run <teste>` |
| Qual parte da entrada causa? | bisseção da entrada |
| É concorrência? | forçar execução serial; aumentar paralelismo |
| É tempo? | congelar o relógio; mudar o fuso |
| É dado? | reproduzir com cópia anonimizada do registro problemático |
