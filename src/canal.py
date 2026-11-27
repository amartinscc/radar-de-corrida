#!/usr/bin/env python3
"""Gera a postagem do Canal do WhatsApp do Radar de Corrida.

Arte = o mesmo card dos stories do @radardecorrida (função card() do src/tenis_do_dia.py: fundo escuro do Radar,
foto do produto, desconto, preço em laranja, cupom e logo oficial) + texto com o link de afiliada da Aline
(Awin com clickref whatsapp-canal; demais lojas pelo código de afiliada do site). As ofertas do canal NÃO entram no site.

Uso:  python3 src/canal.py oferta.json        (um objeto ou uma lista)
Campos: nome, marca, loja, preco (final, conferido na loja), de (preço cheio, opcional), link (URL limpa do produto),
        foto (URL da imagem do produto na loja), cupom?, condicao? (ex.: "no Pix"), modalidade? (Corrida/HYROX/...)
Saída: canal/fila/AAAA-MM-DD-HHMM-<slug>.jpg e .txt (+ JSON no stdout com os caminhos e o texto)
"""
import json, sys, re, datetime, unicodedata, pathlib, threading, http.server, functools, base64, urllib.request
root = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / 'src'))
import tenis_do_dia as T
FILA = root / 'canal' / 'fila'


def slug(s):
    s = unicodedata.normalize('NFD', s.lower())
    s = re.sub(r'[^a-z0-9]+', '-', s.encode('ascii', 'ignore').decode())
    return s.strip('-')[:50]


def baixa(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30)
    return base64.b64encode(r.read()).decode(), (r.headers.get('content-type') or 'image/jpeg').split(';')[0]


def main(arq):
    itens = json.load(open(arq, encoding='utf-8'))
    if isinstance(itens, dict):
        itens = [itens]
    FILA.mkdir(parents=True, exist_ok=True)
    http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    agora = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3)))
    logo = base64.b64encode(T.LOGO.read_bytes()).decode()
    from playwright.sync_api import sync_playwright
    out = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome')
        site = b.new_page()
        site.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html')
        site.wait_for_function('window.__radarCanal', timeout=20000)
        pg = b.new_page(viewport={'width': 1080, 'height': 1920})
        for o in itens:
            preco = float(o['preco'])
            de = float(o['de']) if o.get('de') else None
            off = round((1 - preco / de) * 100) if de and de > preco else 0
            foto, ct = baixa(o['foto'])
            html = T.card(o, foto, ct, 1, 1, preco, de or preco, off, logo, kick='ACHADO DO RADAR', figurinha=False)
            pg.set_content(html)
            pg.wait_for_timeout(700)
            base = FILA / f"{agora:%Y-%m-%d-%H%M}-{slug(o['nome'])}"
            pg.screenshot(path=str(base.with_suffix('.jpg')), type='jpeg', quality=90)
            link = site.evaluate('u => window.__radarCanal.link(u)', o['link'])
            brl = site.evaluate('v => window.__radarCanal.brl(v)', preco)
            txt = f"{o['nome']} por {brl}" + (f" (-{off}%)" if off else '') + f" na {o['loja']}"
            if o.get('condicao'):
                txt += f" {o['condicao']}"
            if o.get('cupom'):
                txt += f", cupom {o['cupom']}"
            txt += f"\nAchado no Radar de Corrida 👉 {link}"
            base.with_suffix('.txt').write_text(txt + '\n', encoding='utf-8')
            out.append({'imagem': str(base.with_suffix('.jpg')), 'texto': txt})
        b.close()
    srv.shutdown()
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
