# Tarefa diária: Tênis do dia (@radardecorrida)

Formato desde 27/11/2026 (decisão do Leandro, "opção B / 1 por dia"): 1 tênis por dia (card "TÊNIS DO DIA" com link de compra) + 1 story final chamando para o Canal de ofertas no WhatsApp. Visual centralizado (padrão de qualquer compartilhamento, Leandro 27/11/2026). Não mudar o visual sem nova aprovação.
Roda todo dia depois da atualização dos achados (11h37). Sem impulsionamento, nunca.

## 1. Gerar as artes
1. Clonar/atualizar o repositório `amartinscc/radar-de-corrida` (`git pull`) — os preços do dia já estão no `index.html`.
2. `python3 src/tenis_do_dia.py --um` → `tenis-do-dia/hoje/1.jpg` (o tênis), `2-canal.jpg` (CTA do Canal) e `posts.json`.
   - Se imprimir `"ok": false` (nenhum tênis com desconto de verdade), NÃO postar nada e só registrar o motivo.
   - Antes de postar, abrir o link da loja e conferir que o preço do card ainda vale (regra: nunca publicar oferta sem conferir o preço na hora).
3. Abrir cada imagem (Read) e conferir: foto do tênis aparece, preço legível, nada cortado, logo oficial no rodapé.
   Se o card estiver ruim ou o preço mudou, rodar de novo (o script pega o próximo tênis elegível).
4. `git add tenis-do-dia/historico.json && git commit -m "Tênis do dia: histórico" && git push` (evita repetir tênis em 7 dias).

## 2. Instagram — stories com figurinha de link (Chrome do Leandro)
Usar SOMENTE as ferramentas claude-in-chrome (Chrome do Leandro, logado no @radardecorrida). Nunca o navegador interno (claudionario).
Para cada imagem, na ordem do `posts.json` (1.jpg com figurinha "VER OFERTA" e link da loja; depois 2-canal.jpg com figurinha "ENTRAR NO CANAL" e o link do Canal):
1. Nova aba: `https://business.facebook.com/latest/story_composer?business_id=3217118888498289&asset_id=1549184344937343`
2. Desmarcar a Página do Facebook (publicar só no Instagram).
3. Upload: rodar no console `HTMLInputElement.prototype.click=function(){if(this.type==='file'&&!this.isConnected){document.body.appendChild(this)}}` (evita a janela nativa e mantém o input na página), clicar em "Adicionar foto/vídeo", achar o file-input (find) e usar file_upload. O file_upload só aceita arquivo que a sessão pode ler: se a imagem estiver no PC, primeiro device_stage_files e usar o stagedPath (/mnt/user-data/uploads/...).
4. Editar → Mais figurinhas → **Link**: URL = campo `link` do posts.json; texto da figurinha = campo `figurinha` (até 25 caracteres).
   A figurinha entra sozinha no CENTRO da imagem (o Business Suite não deixa arrastar) — as artes já deixam essa faixa livre. Não mover.
   Dica: se a janela do Chrome estiver baixa, o editor corta a imagem; não precisa ver a figurinha inteira, só confirmar que foi aplicada.
5. Publicar (Compartilhar agora). Conferir que o story apareceu no perfil.
Se o Business Suite pedir login, CAPTCHA ou verificação: parar e avisar o Leandro (SendUserMessage), sem tentar contornar.

## 3. Distribuição automática (conteúdo já aprovado)
- **TikTok @radar.de.corrida** (Chrome): `https://www.tiktok.com/tiktokstudio/upload?tab=photo` → subir só o `1.jpg` (o story do Canal é só do Instagram) →
  título "Tênis do dia · <dia/mês>" → descrição = `legenda_outras_redes` do posts.json (máx. 5 hashtags, já incluídas) →
  Som: buscar "workout energy" e usar um da biblioteca → Programar para **19:00 do mesmo dia**. Se a pré-verificação de conteúdo travar por mais de 10 min, desligar só a pré-verificação desse post e agendar.
- **Threads @radardecorrida** (Chrome, `https://www.threads.com`): novo post com o `1.jpg` e o texto `legenda_outras_redes`.
- Strava: NÃO (o clube recebe só provas).

## 4. Fechar
- Fechar as abas abertas.
- Registrar na planilha de posts (se acessível): data, "Tênis do dia", tênis, redes.
- Resumo curto ao final (sem mensagem ao Leandro se deu tudo certo). Se algo falhou, avisar o Leandro com o que ficou pendente.

## Regras fixas
- Nunca impulsionar, seguir, curtir, comentar ou responder DMs.
- Nunca postar tênis com desconto falso: o script já exige ≥20% real ou cupom; na dúvida, retirar o card.
- Sem collab nesses posts.
