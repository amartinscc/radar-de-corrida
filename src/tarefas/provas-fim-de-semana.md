# Tarefa semanal: Provas do fim de semana no Rio (@radardecorrida)

Decisão do Leandro (27/11/2026): o carrossel "Provas do fim de semana no Rio" sai TODA SEGUNDA-FEIRA no feed do @radardecorrida,
com as provas de sexta a domingo DAQUELA semana (dá tempo de o seguidor se inscrever). É automático: NÃO passa pela aprovação da Aline.
Sem impulsionar, sem collab, sem anúncio ("Talvez mais tarde" na oferta de anúncio).

## 1. Gerar
1. `git pull`; `python3 src/carrossel.py` (na segunda ele pega sexta a domingo da semana atual). Saída: `carrossel/<n>-<versão>.jpg` e `carrossel/semana.json` (imagens e legenda).
   - Se `total` for 0, não postar e só registrar.
   - Abrir as imagens (Read) e conferir: capa, datas, nada cortado. Máximo 10 imagens (limite do Instagram).
2. Legenda = `legenda` do semana.json, trocando "no meu Radar de Corrida" por "no Radar de Corrida" (o perfil é do Radar, não da Aline).

## 2. Marcar os organizadores (só perfis conferidos)
- Para cada prova da legenda, procurar em `src/tarefas/organizadores-instagram.json` (campo `prova` contido no nome da prova, minúsculas).
  Achou: acrescentar o @ no fim da linha da prova (`• Fla Run – Etapa II – Aterro do Flamengo @flarunoficial`).
- Provas sem @ na lista: tentar conferir no navegador interno do app Claude (conta de pesquisa, só leitura): abrir `https://www.instagram.com/<candidato>/` e ler nome, bio e seguidores.
  Só vale se o nome ou a bio baterem com a prova/organizador (edição, cidade ou link de inscrição). Na dúvida, NÃO marca.
  Perfis conferidos entram no JSON (com data) e os descartados em `nao_confirmados`, com o motivo. Commit e push.
- Nunca marcar perfil de pessoa física só porque o nome parece; nunca inventar @.

## 3. Publicar (Chrome do Leandro, ferramentas claude-in-chrome)
1. Aba nova: `https://business.facebook.com/latest/composer?business_id=3217118888498289&asset_id=1549184344937343`
2. "Postar em": deixar só o Instagram radardecorrida (desmarcar a Página do Facebook).
3. Upload: no console `HTMLInputElement.prototype.click=function(){if(this.type==='file'&&!this.isConnected){document.body.appendChild(this)}}`,
   clicar em "Adicionar foto/vídeo", achar o file-input (find) e usar file_upload com as imagens na ordem.
   O file_upload só aceita arquivos que a sessão pode ler: gravar as imagens no PC (device_commit_files em
   `C:\Projeto mini aline\07 Instagram Radar\<AAAA-MM-DD> provas-fds\`, com nome novo) e usar o stagedPath de device_stage_files.
4. Legenda: clicar na caixa de texto e colar por evento de paste (DataTransfer com text/plain) para as quebras de linha e os @ entrarem certos.
5. Conferir: 1 conta (Instagram), N fotos ("Remover foto" aparece N vezes), legenda completa. Publicar.
6. Na janela "Seu post foi feito": "Talvez mais tarde" (nunca criar anúncio). Conferir no perfil que o número de posts subiu.
Login, CAPTCHA ou verificação: parar e avisar o Leandro.

## 4. Fechar
- Fechar as abas. Resumo curto: total de provas, quantos @ marcados (quais) e quantos novos perfis conferidos.
- Se algo falhou, avisar o Leandro (push curto) com o que ficou pendente.
