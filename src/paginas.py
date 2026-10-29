# Gera as páginas de compartilhamento do radar a partir dos dados do index.html (bloco radar-data):
#   prova/<slug>/index.html e tenis/<slug>/index.html, com metadados de prévia (Open Graph) no HTML,
#   e a imagem de prévia 1200x630 de cada item em og/<tipo>-<slug>.jpg.
# Não altera o index.html. Uso: python3 src/paginas.py
# O slug é o mesmo que a página calcula em JavaScript (função slugItem do template): mude os dois juntos.
import base64, hashlib, html, io, json, math, re, sys, unicodedata, pathlib, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from PIL import Image, ImageDraw, ImageFont

VERSAO = 'v1'  # mude para forçar a regravação de todas as imagens
root = pathlib.Path(__file__).resolve().parent.parent
FONTES = root / 'src' / 'fontes'
SITE = 'https://' + (root / 'CNAME').read_text().strip().strip('/') + '/'

MES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
MESF = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
DOW = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom']
ST = {'cancelada': 'Cancelada pela organização', 'adiada': 'Adiada', 'aberta': 'Inscrições abertas', 'esgotada': 'Esgotada',
      'parcial': 'Alguns lotes esgotados', 'embreve': 'Inscrições em breve', 'confira': 'Confira no site'}


def slug(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:70].rstrip('-')


def slugs(itens, base, extra):
    """slug base; se dois itens tiverem o mesmo, os dois ganham o complemento (cidade/UF ou loja)."""
    b = [base(i) for i in itens]
    return [x + '-' + slug(extra(i)) if b.count(x) > 1 else x for i, x in zip(itens, b)]


def prova_base(p): return slug(p['nome']) + '-' + p['data']
def prova_extra(p): return (p.get('cidade') or '') + ' ' + (p.get('uf') or 'RJ')
def tenis_base(o): return slug(' '.join(x for x in [o.get('marca') or '', o['nome'], o.get('genero') or ''] if x))


AFIL_AMAZON = 'amartins0b-20'  # mesmo código da constante AFIL do template


def afil(u):
    """link de afiliada da Aline (Amazon): acrescenta tag=; os dados guardam o link limpo."""
    try:
        from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
        x = urlsplit(u)
        if re.search(r'(^|\.)amazon\.com\.br$', x.hostname or ''):
            q = [(k, v) for k, v in parse_qsl(x.query, keep_blank_values=True) if k != 'tag'] + [('tag', AFIL_AMAZON)]
            return urlunsplit((x.scheme, x.netloc, x.path, urlencode(q), x.fragment))
    except Exception:
        pass
    return u
def tenis_extra(o): return o.get('loja') or ''


def brl(v):
    s = f'{v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return 'R$ ' + s


# ---------- imagem de prévia ----------
def fonte(n, tam): return ImageFont.truetype(str(FONTES / n), tam)
D = lambda t: fonte('Outfit-Bold.ttf', t)
B = lambda t: fonte('Inter-SemiBold.otf', t)
M = lambda t: fonte('Inter-Medium.otf', t)


def quebra(dr, txt, f, larg, maxl):
    pal, lin, cur = txt.split(), [], ''
    for w in pal:
        t = (cur + ' ' + w).strip()
        if dr.textlength(t, font=f) > larg and cur:
            lin.append(cur); cur = w
        else:
            cur = t
    if cur: lin.append(cur)
    if len(lin) > maxl:
        lin = lin[:maxl]
        while dr.textlength(lin[-1] + '…', font=f) > larg and ' ' in lin[-1]:
            lin[-1] = lin[-1].rsplit(' ', 1)[0]
        lin[-1] += '…'
    return lin


def centro(dr, cx, y, txt, f, cor):
    dr.text((cx - dr.textlength(txt, font=f) / 2, y), txt, font=f, fill=cor)


def fundo(W, H):
    paradas = [(0, (187, 227, 229)), (.45, (217, 193, 217)), (.78, (233, 160, 126)), (1, (59, 42, 64))]
    im = Image.new('RGB', (W, H))
    px = im.load()
    for y in range(H):
        t = y / (H - 1)
        for k in range(len(paradas) - 1):
            a, b = paradas[k], paradas[k + 1]
            if a[0] <= t <= b[0]:
                u = (t - a[0]) / (b[0] - a[0])
                cor = tuple(round(a[1][i] + (b[1][i] - a[1][i]) * u) for i in range(3))
                break
        for x in range(W): px[x, y] = cor
    return im


_FUNDO = None


def imagem(item, tipo, perfil, ofertas_em):
    global _FUNDO
    W, H = 1200, 630
    if _FUNDO is None: _FUNDO = fundo(W, H)
    im = _FUNDO.copy()
    dr = ImageDraw.Draw(im)
    # coluna da Aline
    cx, cy, r = 215, 170, 98
    dr.ellipse((cx - r - 9, cy - r - 9, cx + r + 9, cy + r + 9), fill='white')
    foto = perfil.get('foto') or ''
    if foto.startswith('data:image'):
        av = Image.open(io.BytesIO(base64.b64decode(foto.split(',', 1)[1]))).convert('RGB')
        lado = min(av.size); av = av.crop(((av.width - lado) // 2, (av.height - lado) // 2, (av.width + lado) // 2, (av.height + lado) // 2)).resize((2 * r, 2 * r), Image.LANCZOS)
        mk = Image.new('L', (2 * r, 2 * r), 0); ImageDraw.Draw(mk).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
        im.paste(av, (cx - r, cy - r), mk)
    centro(dr, cx, 290, '@' + (perfil.get('instagram') or 'amartinscc'), B(30), '#1D1220')
    centro(dr, cx, 334, 'PROVA DO RADAR' if tipo == 'prova' else 'OFERTA DO DIA', B(22), '#7A4E7D')
    centro(dr, cx, 438, 'Achado no', B(24), (255, 255, 255))
    centro(dr, cx, 472, 'Radar de Corrida', D(44), (255, 255, 255))
    centro(dr, cx, 522, 'da Aline', D(44), (255, 255, 255))
    centro(dr, cx, 584, 'radardecorrida.com.br', M(20), (255, 255, 255))
    # cartão
    x0, y0, x1, y1 = 430, 40, 1160, 590
    dr.rounded_rectangle((x0, y0, x1, y1), 40, fill='white')
    kx, larg = (x0 + x1) / 2, x1 - x0 - 90
    dr.rounded_rectangle((kx - 130, y0 + 40, kx + 130, y0 + 150), 26, fill='#B28AB1')
    if tipo == 'prova':
        y, m, d = map(int, item['data'].split('-'))
        centro(dr, kx, y0 + 44, f'{d:02d}', D(72), '#1D1220')
        centro(dr, kx, y0 + 120, MESF[m - 1].upper(), B(20), '#1D1220')
        dow = DOW[datetime.date(y, m, d).weekday()]
        lugar = item.get('cidade') if (item.get('uf') or 'RJ') != 'RJ' and item.get('cidade') else (item.get('regiao') or 'Rio de Janeiro')
        centro(dr, kx, y0 + 172, f'{dow} · {lugar}'.upper(), B(20), '#6B5A6E')
        yy = y0 + 210
        for l in quebra(dr, item['nome'], D(46), larg, 2):
            centro(dr, kx, yy, l, D(46), '#1D1220'); yy += 54
        yy += 14
        info = []
        if item.get('local'): info.append(item['local'])
        hd = ' · '.join(x for x in [item['hora'].replace(':', 'h') if item.get('hora') else None, item.get('distancias')] if x)
        if hd: info.append(hd)
        pr = 'Inscrição gratuita' if item.get('valor') == 0 else ('A partir de ' + brl(item['valor']) if isinstance(item.get('valor'), (int, float)) else None)
        ult = ' · '.join(x for x in [pr, ST.get(item.get('status'), '')] if x)
        if ult: info.append(ult)
        if item.get('cupom'): info.append('Cupom da Aline: ' + item['cupom'])
        for linha in info:
            for l in quebra(dr, linha, M(25), larg, 1):
                centro(dr, kx, yy, l, M(25), '#6B5A6E'); yy += 34
            yy += 4
        if item.get('aline'):
            dr.rounded_rectangle((kx - 190, y1 - 112, kx + 190, y1 - 66), 23, fill='#B28AB1')
            t = 'A Aline vai correr'; w = dr.textlength(t, font=B(22)) + 30
            sx = kx - w / 2
            pts = []
            for i in range(10):
                rr_ = 11 if i % 2 == 0 else 4.5
                a = (-90 + 36 * i) * 3.14159265 / 180
                pts.append((sx + 10 + rr_ * math.cos(a), y1 - 89 + rr_ * math.sin(a)))
            dr.polygon(pts, fill='#1D1220')
            dr.text((sx + 30, y1 - 103), t, font=B(22), fill='#1D1220')
        centro(dr, kx, y1 - 48, 'Confira a inscrição no radar', M(20), '#6B5A6E')
    else:
        off = round((1 - item['preco'] / item['de']) * 100) if item.get('de') and item['de'] > item['preco'] else 0
        centro(dr, kx, y0 + 50, f'-{off}%' if off else 'Aline indica', D(72) if off else D(44), '#1D1220')
        cab = ' · '.join(dict.fromkeys(x for x in [item.get('genero'), item.get('marca'), item.get('loja')] if x))
        centro(dr, kx, y0 + 172, cab.upper(), B(20), '#6B5A6E')
        yy = y0 + 210
        for l in quebra(dr, item['nome'], D(46), larg, 2):
            centro(dr, kx, yy, l, D(46), '#1D1220'); yy += 54
        yy += 16
        centro(dr, kx, yy, brl(item['preco']), D(70), '#B4501F'); yy += 86
        if off:
            de = 'de ' + brl(item['de']); f = M(28)
            centro(dr, kx, yy, de, f, '#6B5A6E')
            wd, wp = dr.textlength(de, font=f), dr.textlength('de ', font=f)
            dr.line((kx - wd / 2 + wp, yy + 19, kx + wd / 2, yy + 19), fill='#6B5A6E', width=3)
            yy += 46
        cond = ' · '.join(x for x in [('cupom ' + item['cupom']) if item.get('cupom') else None, item.get('condicao')] if x)
        if cond: centro(dr, kx, yy, cond, B(22), '#7A4E7D')
        centro(dr, kx, y1 - 48, 'Preço sujeito a alteração: confira na loja', M(19), '#6B5A6E')
    out = io.BytesIO(); im.save(out, 'JPEG', quality=80, optimize=True, progressive=True, subsampling=2)
    return out.getvalue()


# ---------- páginas ----------
CSS = ('*{box-sizing:border-box}body{margin:0;font-family:"Plus Jakarta Sans",system-ui,-apple-system,"Segoe UI",sans-serif;'
       'background:#F6F0F6 linear-gradient(180deg,#BBE3E5 0,#D9C1D9 360px,#F6F0F6 720px) no-repeat;color:#1D1220;padding:24px 16px 40px}'
       '.c{max-width:560px;margin:0 auto;display:flex;flex-direction:column;gap:14px}img{width:100%;height:auto;border-radius:18px;display:block}'
       'h1{font:800 28px/1.1 system-ui,sans-serif;margin:0}p{margin:0;color:#6B5A6E}'
       'a.b{display:block;text-align:center;padding:13px 18px;border-radius:999px;text-decoration:none;font-weight:700}'
       'a.p{background:#B28AB1;color:#1D1220}a.s{background:#fff;color:#7A4E7D;border:1.5px solid #B28AB1}'
       '.x{text-align:center;font-size:14px}.x a{color:#7A4E7D}.n{background:#FFF0DC;color:#9A5B00;padding:10px 14px;border-radius:14px;font-weight:600}')


def pagina(tipo, sl, titulo, desc, img, destino, ext_label, ext_link, ativo, titulo_busca=None, ld=None):
    url = SITE + tipo + '/' + sl + '/'
    e = html.escape
    # Só quem chega por um link compartilhado (?c=1) vai direto para o radar; quem vem do Google vê a página da prova.
    # O redirecionamento leva junto o ?c=1 e as marcações utm_ (o painel de métricas usa para separar links compartilhados e stories).
    redir = (f'<script>if(/[?&]c=1(&|$)/.test(location.search))location.replace("/"+location.search+"#{tipo}={sl}");</script>' if ativo else '')
    # Indexar só provas ativas; tênis (preço muda todo dia) e páginas encerradas ficam fora da busca.
    robots = 'index,follow,max-image-preview:large' if (ativo and tipo == 'prova') else 'noindex,follow'
    ldj = ('<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace('</', '<\\/') + '</script>') if ld else ''
    aviso = '' if ativo else ('<p class="n">' + ('Essa prova já aconteceu ou saiu do radar.' if tipo == 'prova' else 'Essa oferta não está mais no radar. Veja as ofertas de hoje.') + '</p>')
    ext = f'<a class="b s" href="{e(ext_link)}" target="_blank" rel="noopener">{e(ext_label)}</a>' if (ativo and ext_link) else ''
    return f'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titulo_busca or titulo)} · Radar de Corrida</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Radar de Corrida da Aline">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}{img}">
<meta property="og:image:secure_url" content="{SITE}{img}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(titulo)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#BBE3E5">
<link rel="icon" type="image/png" href="/favicon.png">
<style>{CSS}</style>
{ldj}
{redir}
</head>
<body>
<main class="c">
{aviso}
<img src="/{img}" alt="{e(titulo)}" width="1200" height="630">
<h1>{e(titulo)}</h1>
<p>{e(desc)}</p>
<a class="b p" href="/{destino}">Ver no Radar de Corrida da Aline</a>
{ext}
<p class="x"><a href="/calculadora-de-pace/">Calcule seu pace e a previsão de tempo para a prova</a></p>
</main>
</body>
</html>
'''


def evento(p, sl, img, desc):
    """Dados estruturados (schema.org SportsEvent) só com o que está no radar."""
    uf = p.get('uf') or 'RJ'
    cidade = p.get('cidade') or ('Rio de Janeiro' if uf == 'RJ' else '')
    end = {'@type': 'PostalAddress', 'addressRegion': uf, 'addressCountry': 'BR'}
    if cidade: end['addressLocality'] = cidade
    if p.get('local'): end['streetAddress'] = p['local']
    lugar = {'@type': 'Place', 'name': p.get('local') or cidade or uf, 'address': end}
    if p.get('lat') is not None and p.get('lng') is not None:
        lugar['geo'] = {'@type': 'GeoCoordinates', 'latitude': p['lat'], 'longitude': p['lng']}
    inicio = p['data'] + (f"T{p['hora']}:00-03:00" if re.fullmatch(r'\d{2}:\d{2}', p.get('hora') or '') else '')
    ev = {'@context': 'https://schema.org', '@type': 'SportsEvent', 'name': p['nome'], 'startDate': inicio,
          'eventAttendanceMode': 'https://schema.org/OfflineEventAttendanceMode',
          'eventStatus': 'https://schema.org/EventCancelled' if p.get('status') == 'cancelada' else 'https://schema.org/EventPostponed' if p.get('status') == 'adiada' else 'https://schema.org/EventScheduled',
          'sport': 'Corrida de rua', 'location': lugar, 'image': [SITE + img], 'description': desc, 'url': SITE + 'prova/' + sl + '/'}
    if p.get('link'): ev['offers'] = {'@type': 'Offer', 'url': p['link'], 'availability': 'https://schema.org/SoldOut' if p.get('status') == 'esgotada' else 'https://schema.org/InStock'}
    return ev


def sitemap(provas_ativas, hoje):
    urls = [(SITE, 'daily', '1.0', hoje), (SITE + 'calculadora-de-pace/', 'monthly', '0.9', None)]
    urls += [(SITE + 'prova/' + sl + '/', 'weekly', '0.6', None) for sl in sorted(provas_ativas)]
    linhas = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, f, pr, lm in urls:
        linhas.append(f'  <url><loc>{html.escape(u)}</loc>' + (f'<lastmod>{lm}</lastmod>' if lm else '') + f'<changefreq>{f}</changefreq><priority>{pr}</priority></url>')
    linhas.append('</urlset>')
    (root / 'sitemap.xml').write_text('\n'.join(linhas) + '\n')


def main():
    s = (root / 'index.html').read_text()
    d = json.loads(re.search(r'<script id="radar-data" type="application/json">(.*?)</script>', s, re.S).group(1))
    perfil = d.get('perfil') or {}
    hoje = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).date().isoformat()
    ofertas_em = ''
    if d.get('ofertas_atualizado') or d.get('atualizado'):
        t = datetime.datetime.fromisoformat(d.get('ofertas_atualizado') or d['atualizado'])
        ofertas_em = t.strftime('%d/%m')
    og = root / 'og'; og.mkdir(exist_ok=True)
    manpath = og / 'manifest.json'
    man = json.loads(manpath.read_text()) if manpath.exists() else {}
    novos_man, gravadas, ativos = {}, 0, {'prova': set(), 'tenis': set()}

    provas = d.get('provas') or []
    ps = slugs(provas, prova_base, prova_extra)
    ofertas = d.get('ofertas') or []
    ts = slugs(ofertas, tenis_base, tenis_extra)
    itens = [('prova', p, sl) for p, sl in zip(provas, ps) if p['data'] >= hoje] + [('tenis', o, sl) for o, sl in zip(ofertas, ts)]

    for tipo, it, sl in itens:
        ativos[tipo].add(sl)
        img = f'og/{tipo}-{sl}.jpg'
        chave = hashlib.sha1(json.dumps([VERSAO, it, perfil.get('instagram'), hashlib.sha1((perfil.get('foto') or '').encode()).hexdigest(), ''], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if man.get(img) != chave or not (root / img).exists():
            (root / img).write_bytes(imagem(it, tipo, perfil, ofertas_em)); gravadas += 1
        novos_man[img] = chave
        if tipo == 'prova':
            y, m, dd = map(int, it['data'].split('-'))
            lugar = it.get('local') or ''
            if (it.get('uf') or 'RJ') != 'RJ': lugar = ', '.join(x for x in [lugar, (it.get('cidade') or '') + ' - ' + it['uf']] if x)
            partes = [f'{dd:02d} de {MESF[m - 1]} de {y}', lugar, it.get('distancias'), ST.get(it.get('status'))]
            desc = ' · '.join(x for x in partes if x) + ('. A Aline vai correr!' if it.get('aline') else '.') + (f" Cupom da Aline na inscrição: {it['cupom']}." if it.get('cupom') else '') + ' Achado no Radar de Corrida da Aline.'
            cidade = it.get('cidade') or ('Rio de Janeiro' if (it.get('uf') or 'RJ') == 'RJ' else '')
            tb = f"{it['nome']} – {dd} de {MESF[m - 1]} de {y}" + (f", {cidade}" if cidade else '')
            html_ = pagina('prova', sl, it['nome'], desc, img, f'#prova={sl}', 'Ver inscrição', it.get('link'), True, tb, evento(it, sl, img, desc))
        else:
            off = round((1 - it['preco'] / it['de']) * 100) if it.get('de') and it['de'] > it['preco'] else 0
            titulo = f"{it['nome']} por {brl(it['preco'])}" + (f" (-{off}%)" if off else '')
            cond = ' · '.join(x for x in [('cupom ' + it['cupom']) if it.get('cupom') else None, it.get('condicao')] if x)
            desc = ' · '.join(x for x in [it.get('categoria') if it.get('categoria') not in (None, 'Tênis') else None, it.get('genero')] if x) + (f" · de {brl(it['de'])} por {brl(it['preco'])}" if off else f" · {brl(it['preco'])}") + f" na {it['loja']}" + (f' ({cond})' if cond else '') + '. Achado no Radar de Corrida da Aline.'
            html_ = pagina('tenis', sl, titulo, desc, img, f'#tenis={sl}', 'Ver na loja', afil(it.get('link') or ''), True)
        pasta = root / tipo / sl; pasta.mkdir(parents=True, exist_ok=True)
        (pasta / 'index.html').write_text(html_)

    # páginas de itens que saíram do radar: continuam no ar, com aviso e sem redirecionar
    encerradas = 0
    for tipo in ('prova', 'tenis'):
        base = root / tipo
        if not base.exists(): continue
        for pasta in sorted(base.iterdir()):
            if not pasta.is_dir() or pasta.name in ativos[tipo]: continue
            f = pasta / 'index.html'
            if not f.exists(): continue
            atual = f.read_text()
            if 'location.replace' not in atual and 'noindex' in atual: continue  # já encerrada
            img = f'og/{tipo}-{pasta.name}.jpg'
            if (root / img).exists(): novos_man[img] = man.get(img, '')
            tit = html.unescape(re.search(r'<meta property="og:title" content="([^"]*)"', atual).group(1))
            desc = html.unescape(re.search(r'<meta property="og:description" content="([^"]*)"', atual).group(1))
            f.write_text(pagina(tipo, pasta.name, tit, desc, img, f'#{"provas" if tipo == "prova" else "tenis"}', '', None, False))
            encerradas += 1
    for img in man:
        if img not in novos_man and (root / img).exists(): novos_man[img] = man[img]  # imagens de páginas encerradas
    sitemap(ativos['prova'], hoje)
    manpath.write_text(json.dumps(novos_man, ensure_ascii=False, indent=0, sort_keys=True))
    print(f'páginas: {len(ativos["prova"])} provas, {len(ativos["tenis"])} tênis; imagens novas/alteradas: {gravadas}; encerradas agora: {encerradas}')
    # carrossel "Provas do fim de semana no Rio" (Modo Aline e e-mail de quinta); um erro aqui não impede o resto
    try:
        import carrossel
        carrossel.main()
    except Exception as e:
        print(f'carrossel: ERRO ({e}); páginas geradas normalmente')


if __name__ == '__main__':
    main()
