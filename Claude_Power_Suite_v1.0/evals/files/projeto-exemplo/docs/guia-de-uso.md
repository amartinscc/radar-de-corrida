# Guia de uso

## Instalação

```
pip install encurtador==0.2.0
```

Depois inicie com `python server.py` e acesse a porta 5000.

#### Encurtar uma URL

Para detalhes da API, clique [aqui](api.md#post-encurtar).

```bash
curl -X POST localhost:5000/encurtar -d '{"url": "https://exemplo.com"}'
```

Configuração: veja [configuração](configuracao.md).

TODO documentar o cache.
