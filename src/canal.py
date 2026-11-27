#!/usr/bin/env python3
"""Gera a postagem do Canal do WhatsApp do Radar de Corrida.

Mesma arte do botão "Compartilhar" do site (drawStory, 1080x1920) + texto com o link de afiliada da Aline
(clickref whatsapp-canal na Awin). As ofertas do canal NÃO entram no site.

Uso:
  python3 src/canal.py oferta.json        # um objeto ou uma lista de objetos
Campos: nome, marca, loja, preco (final), de (preço cheio, opcional), link (URL limpa do produto na loja),
        cupom?, condicao? (ex.: "no Pix"), genero? (Masculino/Feminino/Unissex)
Saída: canal/fila/AAAA-MM-DD-HHMM-<slug>.png e .txt  (+ JSON no stdout com os caminhos e o texto)
"""
import json, sys, re, datetime, unicodedata, pathlib, threading, http.server, functools
root = pathlib.Path(__file__).resolve().parent.parent
FILA = root / 'canal' / 'fila'

def slug(s):
    s = unicodedata.normalize('NFD', s.lower()); s = re.sub(r'[^a-z0-9]+', '-', s.encode('ascii', 'ignore').decode())
    return s.strip('-')[:50]

def main(arq):
    itens = json.load(open(arq, encoding='utf-8'))
    if isinstance(itens, dict): itens = [itens]
    FILA.mkdir(parents=True, exist_ok=True)
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), h); http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    porta = srv.server_address[1]
    from playwright.sync_api import sync_playwright
    out = []
    agora = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3)))
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome')
        pg = b.new_page(viewport={'width': 420, 'height': 900})
        pg.goto(f'http://127.0.0.1:{porta}/index.html'); pg.wait_for_function('window.__radarCanal', timeout=20000); pg.wait_for_timeout(800)
        for o in itens:
            preco = float(o['preco']); de = float(o['de']) if o.get('de') else None
            off = round((1 - preco / de) * 100) if de and de > preco else 0
            js_o = {'nome': o['nome'], 'marca': o.get('marca', ''), 'loja': o['loja'], 'genero': o.get('genero'),
                    'preco': preco, 'fin': preco, 'base': de or preco, 'off': off, 'cupom': o.get('cupom'),
                    'conferido': agora.isoformat()}
            r = pg.evaluate('''async o => { const R = window.__radarCanal; const cv = await R.story(o, null);
                return {png: cv.toDataURL('image/png'), brl: R.brl(o.fin)}; }''', js_o)
            link = pg.evaluate('u => window.__radarCanal.link(u)', o['link'])
            txt = f"{o['nome']} por {r['brl']}" + (f" (-{off}%)" if off else '') + f" na {o['loja']}"
            if o.get('condicao'): txt += f" {o['condicao']}"
            if o.get('cupom'): txt += f", cupom {o['cupom']}"
            txt += f"\nAchado no Radar de Corrida 👉 {link}"
            base = FILA / f"{agora:%Y-%m-%d-%H%M}-{slug(o['nome'])}"
            import base64
            base.with_suffix('.png').write_bytes(base64.b64decode(r['png'].split(',', 1)[1]))
            base.with_suffix('.txt').write_text(txt + '\n', encoding='utf-8')
            out.append({'imagem': str(base.with_suffix('.png')), 'texto': txt})
        b.close()
    srv.shutdown()
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main(sys.argv[1])
