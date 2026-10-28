# Gera o carrossel "Provas do fim de semana no Rio" (1080x1350, para o feed do Instagram) a partir do bloco radar-data do index.html.
# Saída: carrossel/1.jpg ... carrossel/N.jpg e carrossel/semana.json (datas, total, legenda, lista das imagens).
# Fim de semana = sexta a domingo da semana atual (a partir de hoje); só provas do RJ que não foram canceladas.
# Rodado pelo src/paginas.py (portanto pela atualização diária). Só regrava quando as provas do fim de semana mudam.
# Uso direto: python3 src/carrossel.py [AAAA-MM-DD para simular o dia]
import base64, datetime, hashlib, io, json, pathlib, re, sys
from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from paginas import D, B, M, quebra, centro, brl, MESF  # noqa: E402

VERSAO = 'c2'  # mude para forçar a regravação
root = pathlib.Path(__file__).resolve().parent.parent
PASTA = root / 'carrossel'
W, H = 1080, 1350
POR_SLIDE = 4
MAX_SLIDES = 6  # slides de provas (+ capa + final)
INK, MUTED, ACCENT, MAUVE, HOT = '#1D1220', '#6B5A6E', '#7A4E7D', '#B28AB1', '#B4501F'
DIAS = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
DIAC = ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SÁB', 'DOM']
ST = {'esgotada': 'Esgotada', 'parcial': 'Últimos lotes', 'embreve': 'Inscrições em breve', 'adiada': 'Adiada'}


def fundo():
    paradas = [(0, (187, 227, 229)), (.55, (217, 193, 217)), (.85, (233, 160, 126)), (1, (59, 42, 64))]
    col = Image.new('RGB', (1, H))
    for y in range(H):
        t = y / (H - 1)
        for k in range(len(paradas) - 1):
            a, b = paradas[k], paradas[k + 1]
            if a[0] <= t <= b[0]:
                u = (t - a[0]) / (b[0] - a[0])
                col.putpixel((0, y), tuple(round(a[1][i] + (b[1][i] - a[1][i]) * u) for i in range(3)))
                break
    return col.resize((W, H))


def avatar(perfil, r):
    foto = perfil.get('foto') or ''
    if not foto.startswith('data:image'): return None
    av = Image.open(io.BytesIO(base64.b64decode(foto.split(',', 1)[1]))).convert('RGB')
    lado = min(av.size)
    av = av.crop(((av.width - lado) // 2, (av.height - lado) // 2, (av.width + lado) // 2, (av.height + lado) // 2)).resize((2 * r, 2 * r), Image.LANCZOS)
    mk = Image.new('L', (2 * r, 2 * r), 0); ImageDraw.Draw(mk).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
    return av, mk


def rodape(dr, n, total, claro=False):
    cor = (255, 255, 255) if claro else INK
    dr.text((70, H - 78), 'radardecorrida.com.br · @amartinscc', font=B(28), fill=cor)
    t = f'{n}/{total}'
    dr.text((W - 70 - dr.textlength(t, font=B(28)), H - 78), t, font=B(28), fill=cor)


def datas_txt(dias):
    """'31 de outubro e 1º de novembro' / '7 e 8 de novembro' / '6, 7 e 8 de novembro'"""
    fmt = lambda d: ('1º' if d.day == 1 else str(d.day))
    partes, meses = [], []
    for d in dias:
        if meses and meses[-1][0] == d.month: meses[-1][1].append(fmt(d))
        else: meses.append((d.month, [fmt(d)]))
    for m, ds in meses:
        partes.append((', '.join(ds[:-1]) + ' e ' + ds[-1] if len(ds) > 1 else ds[0]) + ' de ' + MESF[m - 1])
    return ' e '.join(partes)


def capa(base, perfil, dias, total, n_slides):
    im = base.copy(); dr = ImageDraw.Draw(im); cx = W // 2
    r = 92; av = avatar(perfil, r)
    dr.ellipse((cx - r - 8, 150 - r - 8, cx + r + 8, 150 + r + 8), fill='white')
    if av: im.paste(av[0], (cx - r, 150 - r), av[1])
    centro(dr, cx, 262, '@' + (perfil.get('instagram') or 'amartinscc'), B(34), INK)
    centro(dr, cx, 312, 'RADAR DE CORRIDA', B(28), ACCENT)
    dr.rounded_rectangle((70, 380, W - 70, 1110), 56, fill='white')
    centro(dr, cx, 440, 'PROVAS DO', B(40), MUTED)
    y = 500
    for l in ['Fim de semana', 'no Rio']:
        centro(dr, cx, y, l, D(128), INK); y += 140
    y += 30
    dt = datas_txt(dias)
    for l in quebra(dr, dt, B(44), W - 260, 2):
        centro(dr, cx, y, l, B(44), ACCENT); y += 58
    y += 40
    txt = f'{total} prova' + ('s' if total != 1 else '')
    tw = dr.textlength(txt, font=D(64)) + 110
    dr.rounded_rectangle((cx - tw / 2, y, cx + tw / 2, y + 104), 52, fill=MAUVE)
    centro(dr, cx, y + 14, txt, D(64), INK)
    centro(dr, cx, 1160, 'Arrasta para ver todas  →', B(36), (255, 255, 255))
    rodape(dr, 1, n_slides, True)
    return im


def info_prova(p):
    l1 = ' · '.join(x for x in [p.get('local'), p['hora'].replace(':', 'h') if p.get('hora') else None] if x)
    preco = 'Gratuita' if p.get('valor') == 0 else ('a partir de ' + brl(p['valor']) if isinstance(p.get('valor'), (int, float)) else None)
    l2 = ' · '.join(x for x in [p.get('distancias'), preco, ST.get(p.get('status'))] if x)
    return l1, l2


def lista(base, itens, n, n_slides):
    im = base.copy(); dr = ImageDraw.Draw(im)
    dr.text((70, 70), 'PROVAS DO FIM DE SEMANA NO RIO', font=B(30), fill=ACCENT)
    y = 140; altura = 262
    for p in itens:
        d = datetime.date.fromisoformat(p['data'])
        dr.rounded_rectangle((70, y, W - 70, y + altura - 22), 40, fill='white')
        # selo da data
        dr.rounded_rectangle((100, y + 30, 270, y + 200), 30, fill=MAUVE)
        centro(dr, 185, y + 44, f'{d.day:02d}', D(84), INK)
        centro(dr, 185, y + 150, DIAC[d.weekday()] + ' · ' + MESF[d.month - 1][:3].upper(), B(24), INK)
        x, larg = 300, W - 70 - 300 - 36
        yy = y + 30
        nome = quebra(dr, p['nome'], D(46), larg, 2)
        for l in nome:
            dr.text((x, yy), l, font=D(46), fill=INK); yy += 54
        yy += 8
        extra = '★ A Aline vai correr' if p.get('aline') else None
        if p.get('cupom'): extra = (extra + ' · ' if extra else '') + 'Cupom da Aline: ' + p['cupom']
        l1, l2 = info_prova(p)
        info = [t for t in [l1, l2] if t]
        if extra and len(nome) > 1: info = info[:1]  # o destaque (Aline/cupom) tem prioridade sobre a 2ª linha
        for txt in info:
            for l in quebra(dr, txt, M(27), larg, 1):
                dr.text((x, yy), l, font=M(27), fill=MUTED); yy += 36
        if extra:
            dr.text((x, yy + 2), extra, font=B(27), fill=HOT)
        y += altura
    rodape(dr, n, n_slides)
    return im


def final(base, sobrou, n_slides):
    im = base.copy(); dr = ImageDraw.Draw(im); cx = W // 2
    dr.rounded_rectangle((70, 200, W - 70, 1130), 56, fill='white')
    y = 280
    for l in ['Inscrições', 'e mais provas']:
        centro(dr, cx, y, l, D(104), INK); y += 116
    y += 30
    linhas = (['+' + str(sobrou) + ' prova' + ('s' if sobrou != 1 else '') + ' neste fim de semana'] if sobrou else []) + \
             ['Calendário do Rio e do Brasil', 'Calculadora de pace', 'Ofertas de tênis de corrida']
    for l in linhas:
        centro(dr, cx, y, l, B(40), ACCENT if l.startswith('+') else MUTED); y += 62
    y += 50
    tw = dr.textlength('Link na bio', font=D(64)) + 120
    dr.rounded_rectangle((cx - tw / 2, y, cx + tw / 2, y + 108), 54, fill=MAUVE)
    centro(dr, cx, y + 16, 'Link na bio', D(64), INK)
    centro(dr, cx, y + 150, 'radardecorrida.com.br', B(42), INK)
    centro(dr, cx, 1190, 'Salva e manda pra quem vai correr com você', B(34), (255, 255, 255))
    rodape(dr, n_slides, n_slides, True)
    return im


def legenda(dias, provas):
    linhas = [f'🏃‍♀️ Provas do fim de semana no Rio: {datas_txt(dias)}!', '']
    for d in dias:
        do_dia = [p for p in provas if p['data'] == d.isoformat()]
        if not do_dia: continue
        linhas.append(f'📅 {DIAS[d.weekday()]}, {d.day:02d}/{d.month:02d}')
        for p in do_dia:
            extra = ' ⭐ eu vou!' if p.get('aline') else ''
            linhas.append(f"• {p['nome']}" + (f" – {p['local']}" if p.get('local') else '') + extra)
        linhas.append('')
    fim = ['Inscrições, horários e todas as provas no meu Radar de Corrida 👉 link na bio (radardecorrida.com.br)', '',
           'Marca aqui quem vai correr com você! 💜', '', '#corridaderua #corrida #riodejaneiro #corridario #radardecorrida']
    txt = '\n'.join(linhas + fim)
    while len(txt) > 2150 and len(linhas) > 3:  # limite de legenda do Instagram (2.200)
        linhas = linhas[:-2] + ['…e mais provas no radar', '']
        txt = '\n'.join(linhas + fim)
    return txt


def main(hoje=None):
    s = (root / 'index.html').read_text()
    d = json.loads(re.search(r'<script id="radar-data" type="application/json">(.*?)</script>', s, re.S).group(1))
    perfil = d.get('perfil') or {}
    hoje = hoje or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).date()
    domingo = hoje + datetime.timedelta(days=6 - hoje.weekday())
    ini = max(hoje, domingo - datetime.timedelta(days=2))
    provas = [p for p in (d.get('provas') or []) if (p.get('uf') or 'RJ') == 'RJ' and p.get('status') != 'cancelada'
              and ini.isoformat() <= p['data'] <= domingo.isoformat()]
    provas.sort(key=lambda p: (p['data'], not p.get('aline'), not p.get('cupom'), p.get('hora') or '99', p['nome']))
    dias = sorted({datetime.date.fromisoformat(p['data']) for p in provas})
    chave = hashlib.sha1(json.dumps([VERSAO, provas, perfil.get('instagram'), hashlib.sha1((perfil.get('foto') or '').encode()).hexdigest()], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    PASTA.mkdir(exist_ok=True)
    jpath = PASTA / 'semana.json'
    atual = json.loads(jpath.read_text()) if jpath.exists() else {}
    if atual.get('chave') == chave and all((root / i).exists() for i in atual.get('imagens', [])):
        print(f'carrossel: sem mudança ({len(provas)} provas)'); return
    for f in PASTA.glob('*.jpg'): f.unlink()
    imagens = []
    if provas:
        mostra = provas[:POR_SLIDE * MAX_SLIDES]
        grupos = [mostra[i:i + POR_SLIDE] for i in range(0, len(mostra), POR_SLIDE)]
        n_slides = len(grupos) + 2
        base = fundo()
        slides = [capa(base, perfil, dias, len(provas), n_slides)] + [lista(base, g, i + 2, n_slides) for i, g in enumerate(grupos)] + [final(base, len(provas) - len(mostra), n_slides)]
        v = chave[:8]
        for i, im in enumerate(slides, 1):
            nome = f'carrossel/{i}-{v}.jpg'
            im.convert('RGB').save(root / nome, 'JPEG', quality=90, optimize=True)
            imagens.append(nome)
    info = {'chave': chave, 'gerado': hoje.isoformat(), 'de': ini.isoformat(), 'ate': domingo.isoformat(),
            'datas': datas_txt(dias) if dias else '', 'total': len(provas), 'imagens': imagens,
            'legenda': legenda(dias, provas) if provas else ''}
    jpath.write_text(json.dumps(info, ensure_ascii=False, indent=1))
    print(f'carrossel: {len(provas)} provas, {len(imagens)} imagens ({info["datas"] or "sem provas no fim de semana"})')


if __name__ == '__main__':
    main(datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else None)
