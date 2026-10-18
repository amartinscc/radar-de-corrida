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
- Fotos da Aline em uso: `hero.jpg/.webp` (abertura) e `fotos/aline-prova-parque-recorte` (banner de Resultados; recorte do original `aline-prova-parque` sem o braço da outra corredora). Desde 16/10/2026 o rodapé ("Gostou do radar?") e o "Em breve" do Treine comigo ficam **sem foto**, a pedido da Aline (menos fotos pessoais). Fora de uso, guardadas: `aline-prova-parque` (original), `aline-orla`, `aline-asics`, `aline-prova-closeup`. Sempre em `.jpg` + `.webp`. `og.jpg` é a imagem de compartilhamento; `favicon.png`, o ícone. Fotos novas mandadas pela Aline: sem marca d'água, alta qualidade.
- O artifact antigo do Claude (`https://claude.ai/artifact/4DvQN7bYGcQC9c7SHfqsAJ`) foi aposentado em 13/10/2026: mostra só um aviso com botão para o site. Não atualizar mais.

## Dados (bloco radar-data)
- `atualizado`, `ofertas_atualizado`: ISO com `-03:00`.
- `perfil` (foto embutida), `assessoria` (planos e preços), `treino_em_breve`: **só manual**. As tarefas nunca mexem.
- `parceiros`: `cupom` geral **AMARTINS**; cada marca tem `nome, categoria, descricao, link, logo` (embutida), `cupom_auto?`, `cupom?` (cupom próprio da marca, ex.: Pozze **AMARTINS15**; a página mostra botão de copiar por marca) e `campanha?`. As tarefas só mexem em `campanhas_conferidas` e `campanha`. Marcas, ordem, logos e cupons: só manual. Parcerias da Aline: linktr.ee/amartinscc.
- `ofertas`: `{loja, nome, marca, preco, de, link, genero}` + `cupom?`, `condicao?`, `foto?`. Foto = URL direta da imagem do próprio modelo/cor na loja (og:image), sem rastreamento; sem foto certa, omitir. Nunca usar AMARTINS em tênis. Links limpos, sem afiliado. Só corrida/running.
- `provas`: `{uf, data, nome, local, link, status}` + `hora?, distancias?, valor?, cidade?, lat?, lng?, regiao?, capa?`. `capa` = URL https da arte oficial do evento (og:image da página do próprio evento/organizador, conferindo nome e data); a lista mostra a capa e, se faltar ou falhar, o bloco de data. Nunca imagem de página de calendário geral, genérica do site ou de outra edição. Capas não são baixadas: ficam como link para a imagem do organizador. **Cumulativas**: só saem quando a data passa; canceladas ficam com status `cancelada`. Fora do RJ precisa de `cidade` + `lat/lng`.
- Selo **"A Aline vai correr"** (`"aline": true`): **só manual**. As tarefas nunca põem nem tiram.
- Na aba Provas: cada prova tem botão de compartilhar e o filtro **"A Aline vai correr"** mostra só as provas com `aline: true`.

## Páginas de compartilhamento (desde 16/10/2026)
- Cada prova (de hoje em diante) e cada tênis em oferta tem endereço próprio: `radardecorrida.com.br/prova/<slug>/` e `/tenis/<slug>/`. Slug da prova = nome + data; do tênis = marca + nome + gênero (com cidade/UF ou loja só se repetir). A regra está em `src/paginas.py` e na função `slugTxt` do template: mudar as duas juntas.
- `python3 src/paginas.py` gera essas páginas e a imagem de prévia 1200x630 de cada item (`og/`), com os metadados Open Graph no HTML. Só regrava imagens de itens que mudaram (`og/manifest.json`). **Rodar sempre depois de mudar os dados** (as tarefas rodam). Fontes das imagens em `src/fontes` (Outfit e Inter, licença OFL).
- A página do item leva para o radar (`/#prova=<slug>` ou `/#tenis=<slug>`), que abre a aba, o estado e destaca o card. Item que saiu do radar: a página continua no ar com aviso e botão para o radar.
- Folha de compartilhar: "Compartilhar imagem e link" (menu do celular, manda a arte de story + texto com o link), "Enviar link no WhatsApp" e "Copiar link". A foto enviada sozinha nunca vira link; o que abre o radar é o link/prévia. Stories: publicar a imagem e pôr o adesivo de Link.
- O WhatsApp guarda a prévia de um link por um tempo: mudanças na imagem podem demorar a aparecer em links já enviados.

## Calculadora de pace (desde 17/10/2026)
- Página própria: `radardecorrida.com.br/calculadora-de-pace/` (arquivo `calculadora-de-pace/index.html`, independente do `index.html`). As tarefas **nunca mexem** nela.
- Faz: pace, tempo ou distância (km ou milha), previsão de prova (Riegel), parciais (constante ou split negativo), ritmos de treino (VDOT de Jack Daniels), zonas de frequência cardíaca (FC máx. medida, ou Tanaka/Gulati pela idade; Karvonen quando há FC de repouso) e gasto calórico estimado pelo peso. Imagem de story para compartilhar e link com o resultado (`?m=&d=&t=&p=`).
- **Não coleta dados**: idade, FC e peso ficam só no aparelho. As métricas mandam só o tipo de cálculo: `calc_calculo` (modo, unidade, prova), `calc_zonas_fc` (método), `calc_compartilhar` (canal), `calc_copiar_link`, `clique_radar`, `seguir_instagram` (botão `calculadora_*`), `clique_prova` (origem calculadora). Na home: `clique_calculadora` (topo/rodape). PostHog só liga no domínio radardecorrida.com.br.
- Mostra as próximas 4 provas do RJ lendo o bloco radar-data do `index.html` (mesma regra de slug do template), com link para `/#prova=<slug>`.
- Paleta e fontes iguais às do `src/template.html`: se a paleta do radar mudar, mudar também na calculadora.
- Foto: `fotos/aline-calculadora.jpg/.webp` (recorte pequeno do `hero.jpg`, em círculo). Imagem de compartilhamento: `og-calculadora.jpg`.
- Links para a calculadora na home: botão discreto no topo (`.calc-link`) e uma linha antes da nota de preços, no `src/template.html`.
- SEO: título e descrição próprios, canonical, Open Graph, dados estruturados (WebApplication, BreadcrumbList, FAQPage igual ao FAQ visível), tabela de pace em HTML. `sitemap.xml` e `robots.txt` na raiz.

## Tarefas agendadas (atualização automática)
Ambas leem o JSON do `index.html`, trocam só os campos delas, fazem commit e push na `main`. Não usam artifact nem a ferramenta add_repo (o repositório já vem clonado em `/home/claude/radar-de-corrida`).
- **Radar de Corrida da Aline (atualização completa)** — todo dia às **6h48** (Brasília). Tênis, provas (RJ todo dia + rodízio semanal de estados), campanhas dos parceiros. Usa todas as fontes listadas nas instruções, inclusive a lista de eventos em destaque da Ticket Sports (`lnk.bio/TicketSports`, sem datas: abrir cada página /e/ do evento). Também completa capas que faltam (até ~30 por dia, RJ primeiro).
- **Radar de Corrida da Aline: ofertas de tênis** — todo dia às **18h45**. Só `ofertas` e `ofertas_atualizado` (Telegram Tênis Certo Cupons e Mania de Corrida, Pelando, Promobit).
- Ambas rodam `python3 src/paginas.py` antes do commit e fazem `git add -A` (index.html, prova/, tenis/, og/).
- Regra: ao mudar o site ou as regras do radar, **atualize também as instruções das duas tarefas**, para a atualização automática não desfazer a mudança.
- Por que o envio ao GitHub falhava até 13/10: as instruções mandavam usar a ferramenta add_repo, que não existe nas execuções agendadas; as tarefas paravam ali. O git funciona normalmente quando a tarefa é criada a partir de uma conversa que já tem o repositório ligado.

## Métricas (PostHog)
- Projeto PostHog do radar, região US (`us.i.posthog.com`), configurado no cabeçalho do `index.html`. Sem cookies (`persistence: memory`) e sem gravação de sessão.
- Eventos: `compartilhar_link` (canal, tipo, item), `abriu_link_compartilhado` (tipo, item, achou), `$pageview`, `clique_loja` (tênis, loja, preço, url), `compartilhar_oferta`, `compartilhar_imagem`, `clique_prova` (prova, url), `cupom_copiado` (parceiro, cupom), `clique_parceiro`, `seguir_instagram` (botão), `voltar_topo`.
- Relatórios de métricas para a Aline: e-mail **amcchagas@gmail.com**.
