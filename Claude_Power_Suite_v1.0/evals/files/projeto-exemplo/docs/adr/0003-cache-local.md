# ADR-0003: Cache local de redirecionamentos

- Status: Aceito
- Data: 2026-06-20
- Decisores: time de plataforma

## Contexto

Leituras são 50 vezes mais frequentes que escritas.

## Decisão

Cache local em memória por instância, com TTL de 300 s (`ENCURTADOR_CACHE_TTL`).

## Consequências

Instâncias diferentes podem divergir até o TTL expirar.
