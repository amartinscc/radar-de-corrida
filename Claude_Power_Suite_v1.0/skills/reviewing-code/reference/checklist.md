# Checklist de revisão por categoria

## Sumário
- Correção e lógica
- Tratamento de erros
- Segurança
- Concorrência e estado
- Dados, banco e migrações
- APIs e compatibilidade
- Desempenho
- Testes
- Particularidades por linguagem

## Correção e lógica
- Condições de borda: vazio, um elemento, máximo, negativo, zero, nulo.
- Off-by-one em laços, fatias e paginação (inclusivo vs. exclusivo).
- Comparações de ponto flutuante usadas para dinheiro (use inteiros/decimal).
- Fuso horário e horário de verão; datas sem fuso comparadas com datas com fuso.
- Ramos `else` ausentes ou `switch` sem caso padrão para valor novo de enum.
- Mudança de comportamento não mencionada na descrição.
- Valores padrão mutáveis ou compartilhados entre chamadas.

## Tratamento de erros
- Exceção capturada e ignorada (`except: pass`, `catch {}`) sem log nem métrica.
- Captura ampla demais escondendo bugs de programação.
- Erro de chamada remota sem timeout; retry sem backoff ou sem limite.
- Recurso não liberado no caminho de erro (arquivo, conexão, lock).
- Mensagem de erro que vaza dados internos para o usuário final.
- Falha parcial deixando estado inconsistente (metade escrita).

## Segurança
- Entrada externa usada em SQL, shell, caminho de arquivo, template, regex,
  desserialização ou URL sem validação/parametrização.
- Autorização verificada só no cliente ou ausente em endpoint novo
  (acesso a recurso de outro usuário trocando um ID — IDOR).
- Segredos no código, em logs ou em mensagens de erro.
- Criptografia caseira; hash de senha sem algoritmo próprio para senhas
  (bcrypt, scrypt, argon2).
- CORS/CSRF permissivos; cookies sem `HttpOnly`/`Secure`/`SameSite`.
- Dados pessoais registrados em log ou retidos sem necessidade (LGPD).
- Dependência nova: origem, manutenção ativa, licença compatível.

## Concorrência e estado
- Leitura-modificação-escrita sem lock/transação (condição de corrida).
- Estado global ou singleton mutável acessado por várias threads/requests.
- Check-then-act sobre sistema de arquivos ou banco.
- Ordem de aquisição de locks inconsistente (deadlock).
- Async: `await` esquecido, tarefas disparadas e perdidas, bloqueio do
  event loop com I/O síncrono.
- Retry de operação não idempotente.

## Dados, banco e migrações
- Migração irreversível ou incompatível com a versão anterior em execução
  durante o deploy (renomear/remover coluna em um passo só).
- Índice ausente para nova consulta em tabela grande; migração que trava
  tabela grande.
- Consultas N+1 em laço.
- Transação longa segurando locks durante chamada remota.
- Alteração de schema sem atualização dos dados existentes (backfill).

## APIs e compatibilidade
- Contrato público alterado sem versionamento (campo removido/renomeado,
  tipo mudado, semântica alterada).
- Novo campo obrigatório quebrando clientes antigos.
- Códigos de status HTTP incoerentes com o resultado.
- Paginação, ordenação e limites ausentes em listagens.

## Desempenho
- Trabalho caro dentro de laço que poderia sair dele.
- Carregar coleção inteira na memória quando streaming/paginação bastaria.
- Cache sem invalidação ou sem limite de tamanho.
- Complexidade quadrática em entrada que cresce com o uso.

## Testes
- Comportamento novo sem teste; correção de bug sem teste de regressão.
- Teste que não falharia se o código estivesse errado (asserção fraca,
  mock que devolve o próprio valor esperado).
- Testes dependentes de ordem, de horário real, de rede ou de aleatoriedade
  sem semente.
- Teste removido ou marcado como ignorado sem justificativa.

## Particularidades por linguagem
- **Python**: argumento padrão mutável; `is` para comparar valores;
  `datetime.now()` sem fuso; iterar e modificar a mesma coleção.
- **JavaScript/TypeScript**: `==` vs `===`; promessa sem `await`/`catch`;
  `any` escondendo erro de tipo; mutação de estado em React fora do setter.
- **Go**: erro retornado e ignorado; goroutine sem cancelamento por
  `context`; captura da variável de laço em closure (versões < 1.22);
  map acessado concorrentemente.
- **Java/Kotlin**: `equals`/`hashCode` inconsistentes; recursos sem
  try-with-resources; `Optional.get()` sem checagem.
- **SQL**: `NOT IN` com subconsulta que pode retornar NULL; `SELECT *` em
  código de produção; falta de `LIMIT` em consulta exploratória.
