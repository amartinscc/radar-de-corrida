# Atributos de qualidade: perguntas, métricas e táticas

## Sumário
- Desempenho
- Escalabilidade
- Disponibilidade e resiliência
- Segurança
- Manutenibilidade e modificabilidade
- Testabilidade
- Observabilidade
- Custo
- Consistência de dados
- Implantação e operação

## Desempenho
- **Perguntas**: qual operação é crítica? qual latência o usuário tolera?
  qual o pico?
- **Métricas**: latência p50/p95/p99, throughput, tempo até o primeiro byte.
- **Táticas**: cache com invalidação definida; índices orientados às
  consultas reais; paginação; processamento assíncrono; evitar N+1;
  reduzir saltos de rede no caminho crítico; compressão.

## Escalabilidade
- **Perguntas**: o crescimento é de usuários, de dados ou de ambos? há
  sazonalidade?
- **Métricas**: custo e latência por unidade de carga ao dobrar a carga.
- **Táticas**: serviços sem estado atrás de balanceador; particionamento
  (sharding) por chave com boa distribuição; réplicas de leitura; filas para
  amortecer picos; limites de taxa.

## Disponibilidade e resiliência
- **Perguntas**: quanto tempo fora do ar é aceitável por mês? qual o custo
  de uma hora parado? o que pode degradar sem parar tudo?
- **Métricas**: SLO (ex.: 99,9% ≈ 43 min/mês de indisponibilidade), MTTR,
  taxa de erro.
- **Táticas**: redundância em zonas; health checks; timeouts; retry com
  backoff exponencial e jitter; circuit breaker; bulkhead; degradação
  graciosa; idempotência; backups testados com restauração periódica.

## Segurança
- **Perguntas**: quais dados são sensíveis (LGPD)? quem acessa o quê? qual a
  superfície exposta à internet?
- **Métricas**: vulnerabilidades abertas por severidade, tempo de correção,
  cobertura de autenticação/autorização.
- **Táticas**: menor privilégio; autenticação centralizada; autorização
  verificada no servidor em cada operação; criptografia em trânsito e em
  repouso; segredos em cofre, nunca no repositório; validação de entrada;
  trilha de auditoria; minimização de dados pessoais.

## Manutenibilidade e modificabilidade
- **Perguntas**: o que muda com mais frequência? quantos times mexem no
  mesmo código?
- **Métricas**: tempo de entrega de uma mudança típica, arquivos tocados por
  mudança, acoplamento entre módulos.
- **Táticas**: módulos com fronteiras por domínio; dependências apontando
  para o núcleo; interfaces estáveis; configuração externa; remover código
  morto.

## Testabilidade
- **Perguntas**: é possível testar a regra de negócio sem banco/rede?
- **Métricas**: tempo da suíte, taxa de testes intermitentes, cobertura das
  regras críticas.
- **Táticas**: injeção de dependências; núcleo puro sem I/O; contratos entre
  serviços; dados de teste determinísticos; ambientes efêmeros.

## Observabilidade
- **Perguntas**: em um incidente, como saberemos o que quebrou e para quem?
- **Métricas**: tempo para detectar (MTTD), proporção de alertas acionáveis.
- **Táticas**: logs estruturados com ID de correlação; métricas RED (taxa,
  erros, duração) por endpoint; tracing distribuído; alertas sobre sintomas
  do usuário (SLO), não sobre causas internas.

## Custo
- **Perguntas**: qual o orçamento mensal? o custo escala linearmente com o
  uso?
- **Métricas**: custo por requisição/cliente/transação.
- **Táticas**: dimensionamento automático; armazenamento em camadas;
  reservas para carga base; eliminar recursos ociosos; preferir serviços
  gerenciados quando o custo de operar for maior que o preço.

## Consistência de dados
- **Perguntas**: algum fluxo exige leitura imediata do que foi escrito?
  o que acontece com dados duplicados ou fora de ordem?
- **Táticas**: transação local quando possível; padrão outbox para publicar
  eventos com consistência; saga com compensação para fluxos distribuídos;
  chaves de idempotência; versionamento otimista.

## Implantação e operação
- **Perguntas**: com que frequência se implanta? qual o rollback?
- **Métricas**: frequência de deploy, taxa de falha de mudança, tempo de
  rollback.
- **Táticas**: infraestrutura como código; pipeline automatizado; feature
  flags; deploy canário ou blue-green; migrações de banco compatíveis com a
  versão anterior (expandir → migrar → contrair).
