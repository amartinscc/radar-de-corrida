# Gera os stories do "Tênis do dia" (1080x1920) do @radardecorrida a partir do bloco radar-data do index.html.
# Modelo aprovado em 24/11/2026: capa "TÊNIS DO DIA" + 1 card por tênis (foto, selo de desconto, preço, cupom, logo oficial).
# A figurinha de link NÃO é desenhada: o Business Suite coloca a figurinha real no CENTRO da imagem (não dá para arrastar),
# por isso a faixa central (y 890–1030) fica sempre livre em todas as artes.
#
# Saída em tenis-do-dia/hoje/: 0-capa.jpg, 1.jpg ... N.jpg e posts.json (link da figurinha, texto da figurinha e legenda de cada story).
# Histórico em tenis-do-dia/historico.json: um tênis não repete em menos de 7 dias.
# Uso: python3 src/tenis_do_dia.py [--n 4] [--sem-historico]
#      python3 src/tenis_do_dia.py --relampago "<parte do nome>"  → 1 story "ACHADO RELÂMPAGO" em tenis-do-dia/relampago/
#      (o achado já precisa estar no index.html; ver src/tarefas/achados.md, seção ACHADO RELÂMPAGO)
import base64, datetime, json, pathlib, re, sys, unicodedata, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from paginas import achados_ativos, slugs, tenis_base, tenis_extra, SITE  # noqa: E402

root = pathlib.Path(__file__).resolve().parent.parent
OUT = root / 'tenis-do-dia' / 'hoje'
HIST = root / 'tenis-do-dia' / 'historico.json'
FONTES = root / 'src' / 'fontes'
LOGO = root / 'src' / 'instagram' / 'logo-radar.png'
TZ = datetime.timezone(datetime.timedelta(hours=-3))
DIAS = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
MESF = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'}

b64 = lambda raw: base64.b64encode(raw).decode()
brl = lambda v: ('R$ ' + f'{v:,.2f}').replace(',', 'X').replace('.', ',').replace('X', '.')


def nk(s): return re.sub(r'[^a-z0-9]+', ' ', unicodedata.normalize('NFD', str(s or '').lower()).encode('ascii', 'ignore').decode())


def precos(o):
    """preço final (com cupom, se houver preco_final menor) e preço de referência ("de")"""
    fin = o['preco']
    if isinstance(o.get('preco_final'), (int, float)) and o['preco_final'] < fin: fin = o['preco_final']
    base = o.get('de') if isinstance(o.get('de'), (int, float)) and o['de'] > fin else (o['preco'] if fin < o['preco'] else None)
    return fin, base


def escolhe(d, n, usar_hist=True):
    ofertas = achados_ativos(d)
    sl = slugs(ofertas, tenis_base, tenis_extra)
    rk = [(m, [re.compile(b, re.I) for b in (m.get('busca') or [])]) for m in ((d.get('ranking_tenis') or {}).get('modelos') or [])]
    hist = json.loads(HIST.read_text()) if HIST.exists() and usar_hist else {}
    hoje = datetime.datetime.now(TZ).date()
    recentes = {s for s, dt in hist.items() if (hoje - datetime.date.fromisoformat(dt)).days < 7}
    cand = []
    for o, s in zip(ofertas, sl):
        if o.get('categoria') != 'Tênis' or not o.get('foto') or s in recentes: continue
        fin, base = precos(o)
        off = (1 - fin / base) * 100 if base else 0
        if off < 20 and not o.get('cupom'): continue  # só desconto de verdade
        top = next((m for m, rx in rk if any(r.search(nk(o['nome'])) for r in rx)), None)
        pts = off + (40 if top else 0) + (15 if 'mais_vendido' in (o.get('motivos') or []) else 0) + (5 if o.get('cupom') else 0)
        cand.append((pts, o, s, fin, base, round(off), top))
    cand.sort(key=lambda c: -c[0])
    sel, marcas, modelos = [], {}, set()
    for c in cand:  # variedade: no máximo 2 por marca e nunca o mesmo modelo duas vezes
        o = c[1]; mod = nk(o['nome'])[:28]
        if marcas.get(o.get('marca'), 0) >= 2 or mod in modelos: continue
        sel.append(c); marcas[o.get('marca')] = marcas.get(o.get('marca'), 0) + 1; modelos.add(mod)
        if len(sel) == n: break
    return sel


def baixa(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25) as r:
            raw = r.read(); ct = r.headers.get('Content-Type', 'image/jpeg').split(';')[0]
        return raw, ct if ct.startswith('image/') else 'image/jpeg'
    except Exception:
        return None, None


CSS = f'''@font-face{{font-family:Urbanist;src:url("{(FONTES / 'Urbanist-var.ttf').as_uri()}")}}
@font-face{{font-family:"Plus Jakarta Sans";src:url("{(FONTES / 'PlusJakartaSans-var.ttf').as_uri()}")}}
*{{margin:0;box-sizing:border-box}}body{{width:1080px;height:1920px;position:relative;overflow:hidden;font-family:"Plus Jakarta Sans";color:#F4ECF4;
background:radial-gradient(circle at 50% 640px,#33203a 0,#1D1220 62%)}}
.ring{{position:absolute;left:50%;border:3px solid rgba(221,185,221,.14);border-radius:50%}}
.logo{{position:absolute;left:50%;transform:translateX(-50%);bottom:96px;height:104px}}
.kick{{font-family:Urbanist;font-weight:800;letter-spacing:12px;color:#DDB9DD;font-size:34px}}'''


def rings(cy):
    return ''.join(f'<div class="ring" style="top:{cy}px;width:{d}px;height:{d}px;margin-left:-{d // 2}px;margin-top:-{d // 2}px;opacity:{o}"></div>'
                   for d, o in [(640, 1), (900, .7), (1180, .45), (1480, .25)])


def capa(data, n, logo):
    return f'''<html><head><style>{CSS}</style></head><body>{rings(640)}
<div style="position:absolute;left:50%;top:640px;width:760px;height:760px;margin:-380px 0 0 -380px;border-radius:50%;background:conic-gradient(from 30deg,rgba(242,138,91,.30),rgba(242,138,91,0) 55deg,transparent)"></div>
<div style="position:absolute;left:calc(50% + 230px);top:440px;width:38px;height:38px;border-radius:50%;background:#F28A5B;box-shadow:0 0 44px 14px rgba(242,138,91,.55)"></div>
<div style="position:absolute;top:250px;width:100%;text-align:center" class="kick">ACHADOS COM PREÇO CONFERIDO</div>
<div style="position:absolute;top:430px;width:100%;text-align:center;font:800 190px/0.92 Urbanist;letter-spacing:-6px">TÊNIS<br><span style="color:#F28A5B">DO DIA</span></div>
<div style="position:absolute;top:1080px;width:100%;text-align:center;font:700 44px Urbanist;color:#DDB9DD">{data}</div>
<div style="position:absolute;top:1170px;width:820px;left:130px;text-align:center;font:600 40px/1.35 'Plus Jakarta Sans'">Separamos {n} tênis de corrida e HYROX com desconto de verdade. Passa pro lado 👉</div>
<img class="logo" src="data:image/png;base64,{logo}"></body></html>'''


def card(o, foto, ct, i, n, fin, base, off, logo, kick=None):
    mod = (o.get('modalidade') or 'Corrida').upper()
    cup = f'<div style="display:inline-block;margin-top:26px;background:#F28A5B;color:#1D1220;font:800 34px Urbanist;padding:12px 28px;border-radius:999px;letter-spacing:2px">CUPOM {o["cupom"]}</div>' if o.get('cupom') else ''
    cond = o.get('condicao') or ''
    if o.get('cupom') and cond.lower().startswith('desconto extra com o cupom'): cond = cond.split('+', 1)[1].strip() if '+' in cond else ''
    cond = f'<div style="margin-top:18px;font:600 30px \'Plus Jakarta Sans\';color:#DDB9DD">{cond}</div>' if cond else ''
    selo = f'<div style="position:absolute;top:240px;right:60px;background:#F28A5B;color:#1D1220;font:800 64px Urbanist;padding:18px 30px;border-radius:28px;transform:rotate(4deg);box-shadow:0 10px 30px rgba(0,0,0,.3)">-{off}%</div>' if off else ''
    loja = '' if o.get('marca') == o.get('loja') else ' · ' + (o.get('loja') or '').upper()
    return f'''<html><head><style>{CSS}</style></head><body>{rings(580)}
<div style="position:absolute;top:200px;left:80px" class="kick">{kick or f"TÊNIS DO DIA · {i}/{n}"}</div>
<div style="position:absolute;top:200px;right:80px;font:800 34px Urbanist;color:#DDB9DD">{mod}</div>
<div style="position:absolute;top:280px;left:80px;width:920px;height:580px;background:#fff;border-radius:44px;display:flex;align-items:center;justify-content:center;overflow:hidden;box-shadow:0 30px 60px rgba(0,0,0,.35)">
<img src="data:{ct};base64,{foto}" style="max-width:92%;max-height:92%;object-fit:contain;mix-blend-mode:multiply"></div>{selo}
<div style="position:absolute;top:1060px;left:80px;width:920px">
<div style="font:700 32px Urbanist;color:#DDB9DD;letter-spacing:3px">{(o.get('marca') or '').upper()}{loja}</div>
<div style="margin-top:12px;font:800 66px/1.05 Urbanist">{o['nome']}</div>
<div style="margin-top:26px;display:flex;align-items:baseline;gap:26px"><span style="font:800 120px/1 Urbanist;color:#F28A5B">{brl(fin)}</span>{f'<s style="font:600 42px Urbanist;color:#B9A3BC">{brl(base)}</s>' if base else ''}</div>
{cup}{cond}</div>
<div style="position:absolute;bottom:230px;width:100%;text-align:center;font:500 22px 'Plus Jakarta Sans';color:rgba(244,236,244,.6)">Preço conferido hoje pelo Radar · pode mudar na loja a qualquer momento</div>
<img class="logo" src="data:image/png;base64,{logo}"></body></html>'''


def relampago(termo):
    s = (root / 'index.html').read_text()
    d = json.loads(re.search(r'<script id="radar-data" type="application/json">(.*?)</script>', s, re.S).group(1))
    ofertas = achados_ativos(d)
    sl = slugs(ofertas, tenis_base, tenis_extra)
    t = nk(termo)
    cand = []
    for o, sg in zip(ofertas, sl):
        if o.get('categoria') != 'Tênis' or t not in nk(o['nome']): continue
        fin, base = precos(o)
        cand.append((fin, o, sg, base))
    if not cand:
        print(json.dumps({'ok': False, 'motivo': f'nenhum tênis com "{termo}" nos achados de hoje'}, ensure_ascii=False)); return
    fin, o, sg, base = min(cand, key=lambda c: c[0])
    off = round((1 - fin / base) * 100) if base else 0
    raw, ct = baixa(o['foto']) if o.get('foto') else (None, None)
    if not raw:
        print(json.dumps({'ok': False, 'motivo': 'foto do tênis não baixou'}, ensure_ascii=False)); return
    out = root / 'tenis-do-dia' / 'relampago'; out.mkdir(parents=True, exist_ok=True)
    arq = out / f'{datetime.datetime.now(TZ).date().isoformat()}-{sg}.jpg'
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome')
        pg = b.new_page(viewport={'width': 1080, 'height': 1920})
        pg.set_content(card(o, b64(raw), ct, 1, 1, fin, base, off, b64(LOGO.read_bytes()), kick='ACHADO RELÂMPAGO')); pg.wait_for_timeout(700)
        pg.screenshot(path=str(arq), type='jpeg', quality=92); b.close()
    print(json.dumps({'ok': True, 'arquivo': str(arq), 'link': SITE + f'tenis/{sg}/', 'figurinha': 'VER OFERTA', 'nome': o['nome'],
                      'loja': o.get('loja'), 'preco': fin, 'de': base, 'off': off, 'cupom': o.get('cupom')}, ensure_ascii=False))


def main():
    if '--relampago' in sys.argv:
        return relampago(sys.argv[sys.argv.index('--relampago') + 1])
    n = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 4
    usar_hist = '--sem-historico' not in sys.argv
    s = (root / 'index.html').read_text()
    d = json.loads(re.search(r'<script id="radar-data" type="application/json">(.*?)</script>', s, re.S).group(1))
    sel = escolhe(d, n + 3, usar_hist)  # sobra para o caso de foto que não baixa
    itens = []
    for pts, o, sl, fin, base, off, top in sel:
        raw, ct = baixa(o['foto'])
        if raw: itens.append((o, sl, fin, base, off, top, b64(raw), ct))
        if len(itens) == n: break
    if len(itens) < 3:
        print(json.dumps({'ok': False, 'motivo': f'só {len(itens)} tênis com desconto de verdade hoje (mínimo 3)'}, ensure_ascii=False)); return
    hoje = datetime.datetime.now(TZ).date()
    data = f'{DIAS[hoje.weekday()]}, {hoje.day} de {MESF[hoje.month - 1]}'
    logo = b64(LOGO.read_bytes())
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob('*'): f.unlink()
    from playwright.sync_api import sync_playwright
    paginas = [('0-capa.jpg', capa(data, len(itens), logo))] + [
        (f'{k + 1}.jpg', card(o, foto, ct, k + 1, len(itens), fin, base, off, logo)) for k, (o, sl, fin, base, off, top, foto, ct) in enumerate(itens)]
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome')
        pg = b.new_page(viewport={'width': 1080, 'height': 1920})
        for nome, h in paginas:
            pg.set_content(h); pg.wait_for_timeout(700)
            pg.screenshot(path=str(OUT / nome), type='jpeg', quality=92)
        b.close()
    posts = [{'arquivo': '0-capa.jpg', 'link': SITE + '#tenis', 'figurinha': 'TÊNIS DO RADAR'}]
    for k, (o, sl, fin, base, off, top, foto, ct) in enumerate(itens):
        posts.append({'arquivo': f'{k + 1}.jpg', 'link': SITE + f'tenis/{sl}/', 'figurinha': 'VER OFERTA', 'slug': sl,
                      'nome': o['nome'], 'marca': o.get('marca'), 'loja': o.get('loja'), 'preco': fin, 'de': base, 'off': off,
                      'cupom': o.get('cupom'), 'ranking': top.get('selo') if top else None})
    legenda = ('Tênis do dia no Radar 👟 ' + ' · '.join(f"{p['marca']} {brl(p['preco'])}" for p in posts[1:]) +
               '. Preços conferidos hoje, com cupom das lojas parceiras. Todos em radardecorrida.com.br #corrida #hyrox #tenisdecorrida #corridaderua #radardecorrida')
    (OUT / 'posts.json').write_text(json.dumps({'data': hoje.isoformat(), 'stories': posts, 'legenda_outras_redes': legenda}, ensure_ascii=False, indent=1))
    if usar_hist:
        hist = json.loads(HIST.read_text()) if HIST.exists() else {}
        hist = {k: v for k, v in hist.items() if (hoje - datetime.date.fromisoformat(v)).days < 30}
        for p_ in posts[1:]: hist[p_['slug']] = hoje.isoformat()
        HIST.parent.mkdir(exist_ok=True); HIST.write_text(json.dumps(hist, ensure_ascii=False, indent=1, sort_keys=True))
    print(json.dumps({'ok': True, 'pasta': str(OUT), 'stories': len(posts)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
