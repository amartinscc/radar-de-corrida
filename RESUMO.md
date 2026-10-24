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
- `parceiros`: `cupom` geral **AMARTINS**; cada marca tem `nome, categoria, descricao, link, logo` (embutida), `cupom_auto?`, `cupom?` (cupom próprio da marca, ex.: Pozze **AMARTINS15**, Marmitas da Lulu **AMARTINSCC**; a página mostra botão de copiar por marca) e `campanha?`. As tarefas só mexem em `campanhas_conferidas` e `campanha`. Marcas, ordem, logos e cupons: só manual. Parcerias da Aline: linktr.ee/amartinscc. Marmitas da Lulu (desde 18/10/2026): logo é o link da imagem oficial do site deles (não embutida); se quebrar, trocar por imagem embutida. Livvan (desde 24/10/2026, suplementos, cupom AMARTINS): logo também é link da imagem oficial (`livvan.com.br/cdn/...logo-livvan.webp`) com `"logo_ajuste": "contain"` (mostra o logo inteiro, sem cortar; serve para logos horizontais). Se um logo por link falhar, a página mostra a inicial da marca.
- `ofertas`: `{loja, nome, marca, preco, de, link, genero}` + `cupom?`, `condicao?`, `foto?`. Foto = URL direta da imagem do próprio modelo/cor na loja (og:image), sem rastreamento; sem foto certa, omitir. Nunca usar AMARTINS em tênis. Links limpos, sem afiliado. Só corrida/running.
- `provas`: `{uf, data, nome, local, link, status}` + `hora?, distancias?, valor?, cidade?, lat?, lng?, regiao?, capa?`. `capa` = URL https da arte oficial do evento (og:image da página do próprio evento/organizador, conferindo nome e data); a lista mostra a capa e, se faltar ou falhar, o bloco de data. Nunca imagem de página de calendário geral, genérica do site ou de outra edição. Capas não são baixadas: ficam como link para a imagem do organizador. **Cumulativas**: só saem quando a data passa; canceladas ficam com status `cancelada`. Fora do RJ precisa de `cidade` + `lat/lng`.
- Selo **"A Aline vai correr"** (`"aline": true`): **só manual**. As tarefas nunca põem nem tiram.
- Cupom da Aline numa prova (`"cupom": "AMARTINS"`, desde 22/10/2026, primeira: Jungle Running Club Rio, 08/11): **só manual**. O cartão mostra "Desconto com o cupom da Aline na inscrição" com botão de copiar (evento `cupom_copiado` com `tipo: prova`); entra também na imagem de story, no texto de compartilhar e na página/prévia da prova. As tarefas nunca põem, tiram nem mudam.
- Na aba Provas: cada prova tem botão de compartilhar e o filtro **"A Aline vai correr"** mostra só as provas com `aline: true`.

## Páginas de compartilhamento (desde 16/10/2026)
- Cada prova (de hoje em diante) e cada tênis em oferta tem endereço próprio: `radardecorrida.com.br/prova/<slug>/` e `/tenis/<slug>/`. Slug da prova = nome + data; do tênis = marca + nome + gênero (com cidade/UF ou loja só se repetir). A regra está em `src/paginas.py` e na função `slugTxt` do template: mudar as duas juntas.
- `python3 src/paginas.py` gera essas páginas e a imagem de prévia 1200x630 de cada item (`og/`), com os metadados Open Graph no HTML. Só regrava imagens de itens que mudaram (`og/manifest.json`). **Rodar sempre depois de mudar os dados** (a tarefa diária roda). Fontes das imagens em `src/fontes` (Outfit e Inter, licença OFL).
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
- Links para a calculadora na home: botão no topo (`.calc-link`, desde 22/10/2026 com borda dourada e um brilho que gira ao redor; para quem pede menos movimento no celular, a borda fica parada) e uma linha antes da nota de preços, no `src/template.html`.
- SEO: título e descrição próprios, canonical, Open Graph, dados estruturados (WebApplication, BreadcrumbList, FAQPage igual ao FAQ visível), tabela de pace em HTML. `sitemap.xml` e `robots.txt` na raiz.

## SEO (desde 17/10/2026)
- Home: título "Calendário de Corridas de Rua no Rio e no Brasil | Radar de Corrida" (no `src/template.html`), descrição, canonical e robots no cabeçalho do `index.html` (o `build.py` preserva o cabeçalho). Dados estruturados WebSite + Person + FAQPage no template; o FAQ visível fica no bloco `.sobre`, no fim da página. Mudar o FAQ visível e o do JSON-LD juntos.
- Páginas de prova: indexáveis, com título "<nome> – <data>, <cidade>" e dados estruturados SportsEvent (só com dados do radar). **Não redirecionam mais sozinhas**: só vão para o radar quando o link tem `?c=1`, que o botão de compartilhar acrescenta. Quem vem do Google vê a página da prova.
- Páginas de tênis e de provas encerradas: `noindex` (continuam no ar para compartilhar).
- Google Search Console: verificação pelo arquivo `google46ef085f7a7a7d5c.html` na raiz. **Nunca apagar nem alterar** (o Google confere de tempos em tempos).
- `sitemap.xml` é gerado pelo `src/paginas.py` (home, calculadora e provas ativas). `robots.txt` aponta para ele.

## Tarefas agendadas (atualização automática)
**Uma única atualização por dia** (decisão de 17/10/2026): a tarefa **Radar de Corrida da Aline (atualização completa)**, todo dia às **6h48** (Brasília), atualiza tênis, provas (RJ todo dia + rodízio semanal de estados) e campanhas dos parceiros. Usa todas as fontes listadas nas instruções, inclusive a lista de eventos em destaque da Ticket Sports (`lnk.bio/TicketSports`, sem datas: abrir cada página /e/ do evento). Também completa capas que faltam (até ~30 por dia, RJ primeiro).
- A antiga tarefa de ofertas de tênis das 18h45 foi **desativada** (as fontes dela, Telegram, Pelando e Promobit, já estão na atualização completa). Não reativar sem pedido.
- A tarefa lê o JSON do `index.html`, troca só os campos dela, roda `python3 src/paginas.py` (páginas, imagens e sitemap), faz `git add -A`, commit e push na `main`. Não usa artifact nem a ferramenta add_repo (o repositório já vem clonado em `/home/claude/radar-de-corrida`). Nunca mexe em `calculadora-de-pace/`, `src/`, `robots.txt` nem no cabeçalho do `index.html`.
- Regra: ao mudar o site ou as regras do radar, **atualize também as instruções da tarefa**, para a atualização automática não desfazer a mudança.
- Por que o envio ao GitHub falhava até 13/10: as instruções mandavam usar a ferramenta add_repo, que não existe nas execuções agendadas; as tarefas paravam ali. O git funciona normalmente quando a tarefa é criada a partir de uma conversa que já tem o repositório ligado.

## Modo Aline (desde 24/10/2026)
- Funções que só aparecem no celular da Aline. Ativar: abrir `radardecorrida.com.br/?aline` e digitar a senha (com o Leandro). Guarda `radar-aline=1` (e `radar-quem=aline`) no localStorage daquele aparelho. Sair: botão "Modo Aline" (canto de baixo) → "Sair do Modo Aline".
- A senha é conferida pelo SHA-256 de `radar-aline:<senha>` (constante `ADM_HASH` no `src/template.html`). Para trocar: calcular o novo hash e rodar `python3 src/build.py`. O repositório é público: o Modo Aline esconde funções, não guarda segredo. Não pôr dado pessoal nele.
- Menu: Kits das parceiras, Métricas (link do painel), Link para os stories, Link dos parceiros (`/#parceiros`), Sair.
- **Kit para a parceira** (botão em cada marca da aba Parceiros): arte "Aline × Marca" em Story (1080x1920) ou Post/collab (1080x1350), com foto, logo da marca, frase, cupom da marca e `radardecorrida.com.br · @amartinscc`. A Aline escolhe a foto da galeria, arrasta e dá zoom; a foto **não sobe para o site** (fica no IndexedDB `radar-aline` daquele celular, por marca, junto com zoom, enquadramento, frase e formato). Sem foto, usa `hero.jpg`. Traz legenda do post e mensagem para a marca (editáveis) e o link da marca no radar.
- Textos e frases de cada marca: objeto `KIT_TXT` no `src/template.html` (chave = slug do nome). Marca nova sem entrada usa os textos genéricos da categoria. Ao adicionar parceiro, acrescentar a entrada dele.
- Logo por URL no kit é carregado com CORS; se o servidor da marca não permitir, a arte mostra a inicial da marca no lugar.
- Links públicos (servem para qualquer um): `/#parceiros` abre a aba Parceiros; `/#parceiro=<slug>` abre e destaca a marca.

## Métricas (PostHog)
- Projeto PostHog do radar, região US (`us.i.posthog.com`), configurado no cabeçalho do `index.html`. Sem cookies (`persistence: memory`) e sem gravação de sessão.
- Eventos: `compartilhar_link` (canal, tipo, item), `abriu_link_compartilhado` (tipo, item, achou), `$pageview`, `clique_loja` (tênis, loja, preço, url), `compartilhar_oferta`, `compartilhar_imagem`, `clique_prova` (prova, url), `cupom_copiado` (parceiro, cupom), `clique_parceiro`, `seguir_instagram` (botão), `voltar_topo`.
- Relatórios de métricas para a Aline: e-mail **amcchagas@gmail.com**.

## Painel de métricas privado (desde 22/10/2026)
- Endereço secreto: **radardecorrida.com.br/painel/rc-5yecuqq3sbbk9h/** (no molde do painel do Mais Mercante). `noindex`, fora do sitemap, sem PostHog na própria página. Atenção: o repositório é público, então o painel é "escondido", não protegido por senha. Não pôr dado pessoal nele.
- Arquivos: `painel/rc-5yecuqq3sbbk9h/index.html` (visual, períodos Hoje/7/30/90 dias, lê `dados.json` ao abrir) e `painel/rc-5yecuqq3sbbk9h/dados.json` (dados).
- Atualização: tarefa agendada **Painel de métricas do Radar** roda as duas consultas de `src/painel-consultas.sql` no PostHog (execute-sql), salva a saída em texto e roda `python3 src/painel.py agregado.txt diario.txt`, que grava só o `dados.json`. Depois commit e push. A tarefa nunca mexe em outros arquivos.
- O endereço do painel está na constante `PAINEL` de `src/painel.py`. Para trocar o link: renomear a pasta e a constante, e atualizar este resumo e a tarefa.
- Visita = sessão com página vista (sem cookies, quem volta outro dia conta de novo). Inclui testes nossos.
- Origem das visitas no painel: "Instagram · link na bio" (o Instagram marca sozinho `utm_content=link_in_bio`), "Instagram · stories de @..." (links marcados com `utm_medium=stories&utm_campaign=<perfil>`), "Instagram · stories ou direct (sem marcação)" (adesivo de link sem marcação; não dá para saber de quem), "Link compartilhado" (`?c=1`). Link para os stories da Aline: `radardecorrida.com.br/?utm_medium=stories&utm_campaign=amartinscc`.
- As páginas de prova/tênis, ao redirecionar (`?c=1`), levam junto a query (`?c=1` e `utm_`), para o painel saber a origem (desde 22/10/2026).
- Links do botão de compartilhar (desde 22/10/2026): levam o canal em `o=` (`wa` WhatsApp, `lk` copiar link, `st` imagem + link pelo menu do celular, `sh` menu só com link) e, se o aparelho estiver marcado, quem compartilhou em `q=`. Marcar o celular da Aline: abrir uma vez `radardecorrida.com.br/?marcar=aline` no navegador onde ela compartilha (guarda `radar-quem` no localStorage; `?marcar=sair` desfaz). O painel mostra "Compartilhado pela Aline · <canal>", e quando o clique vem do Instagram, "Instagram (stories ou direct)". O evento `compartilhar_link` leva também `quem`.
