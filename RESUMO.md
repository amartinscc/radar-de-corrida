# Radar de Corrida da Aline — resumo para novas conversas

Leia este arquivo antes de mexer no radar. Atualize-o sempre que mudar regras, tarefas ou o site.

## O que é
- Site público **radardecorrida.com.br** da Aline Martins Carvalho das Chagas (@amartinscc), personal trainer e corredora, esposa do Leandro Simas.
- Abas: **Provas** (corridas de rua do Brasil num mapa-radar por estado), **Parceiros** (marcas com cupom da Aline), **Tênis** (ofertas de tênis de corrida), **Treine comigo** (assessoria de corrida da Aline, presencial na praia da Barra da Tijuca ou online; contato pelo Instagram/DM) e **Resultados** oficiais da Aline.
- Prioridade: corrida (provas). Tênis é um extra.

## Onde fica
- GitHub Pages, repositório `amartinscc/radar-de-corrida`, branch `main`. Domínio no arquivo `CNAME`.
- `index.html`: o site publicado. Os dados ficam no bloco `<script id="radar-data" type="application/json">`.
- `src/template.html`: o visual. Depois de mudar o visual, rode `python3 src/build.py` para regerar o `index.html` mantendo os dados (o cabeçalho com as métricas é preservado).
- Fotos da Aline: `hero.jpg/.webp` (abertura), `fotos/aline-prova-parque` (Resultados, New Balance 15K Rio), `fotos/aline-orla` (convite para seguir), `fotos/aline-asics` (Treine comigo / Em breve, Asics Golden Run Rio), `fotos/aline-prova-closeup` (reserva). Sempre em `.jpg` + `.webp`. `og.jpg` é a imagem de compartilhamento; `favicon.png`, o ícone. Fotos novas mandadas pela Aline: sem marca d'água, alta qualidade.
- O artifact antigo do Claude (`https://claude.ai/artifact/4DvQN7bYGcQC9c7SHfqsAJ`) foi aposentado em 13/10/2026: mostra só um aviso com botão para o site. Não atualizar mais.

## Dados (bloco radar-data)
- `atualizado`, `ofertas_atualizado`: ISO com `-03:00`.
- `perfil` (foto embutida), `assessoria` (planos e preços), `treino_em_breve`: **só manual**. As tarefas nunca mexem.
- `parceiros`: `cupom` geral **AMARTINS**; cada marca tem `nome, categoria, descricao, link, logo` (embutida), `cupom_auto?`, `cupom?` (cupom próprio da marca, ex.: Pozze **AMARTINS15**; a página mostra botão de copiar por marca) e `campanha?`. As tarefas só mexem em `campanhas_conferidas` e `campanha`. Marcas, ordem, logos e cupons: só manual. Parcerias da Aline: linktr.ee/amartinscc.
- `ofertas`: `{loja, nome, marca, preco, de, link, genero}` + `cupom?`, `condicao?`, `foto?`. Foto = URL direta da imagem do próprio modelo/cor na loja (og:image), sem rastreamento; sem foto certa, omitir. Nunca usar AMARTINS em tênis. Links limpos, sem afiliado. Só corrida/running.
- `provas`: `{uf, data, nome, local, link, status}` + `hora?, distancias?, valor?, cidade?, lat?, lng?, regiao?`. **Cumulativas**: só saem quando a data passa; canceladas ficam com status `cancelada`. Fora do RJ precisa de `cidade` + `lat/lng`.
- Selo **"A Aline vai correr"** (`"aline": true`): **só manual**. As tarefas nunca põem nem tiram.

## Tarefas agendadas (atualização automática)
Ambas leem o JSON do `index.html`, trocam só os campos delas, fazem commit e push na `main`. Não usam artifact nem a ferramenta add_repo (o repositório já vem clonado em `/home/claude/radar-de-corrida`).
- **Radar de Corrida da Aline (atualização completa)** — todo dia às **6h48** (Brasília). Tênis, provas (RJ todo dia + rodízio semanal de estados), campanhas dos parceiros. Usa todas as fontes listadas nas instruções.
- **Radar de Corrida da Aline: ofertas de tênis** — todo dia às **18h45**. Só `ofertas` e `ofertas_atualizado` (Telegram Tênis Certo Cupons e Mania de Corrida, Pelando, Promobit).
- Regra: ao mudar o site ou as regras do radar, **atualize também as instruções das duas tarefas**, para a atualização automática não desfazer a mudança.
- Por que o envio ao GitHub falhava até 13/10: as instruções mandavam usar a ferramenta add_repo, que não existe nas execuções agendadas; as tarefas paravam ali. O git funciona normalmente quando a tarefa é criada a partir de uma conversa que já tem o repositório ligado.

## Métricas (PostHog)
- Projeto PostHog do radar, região US (`us.i.posthog.com`), configurado no cabeçalho do `index.html`. Sem cookies (`persistence: memory`) e sem gravação de sessão.
- Eventos: `$pageview`, `clique_loja` (tênis, loja, preço, url), `compartilhar_oferta`, `compartilhar_imagem`, `clique_prova` (prova, url), `cupom_copiado` (parceiro, cupom), `clique_parceiro`, `seguir_instagram` (botão), `voltar_topo`.
- Relatórios de métricas para a Aline: e-mail **amcchagas@gmail.com**.
