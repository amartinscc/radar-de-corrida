# Gera o carrossel "Provas do mês no Rio e em São Paulo" (1080x1350, feed do Instagram; o Modo Aline monta a versão story)
# a partir do bloco radar-data do index.html.
# Saída: carrossel/mes/<n>-<versão>.jpg e carrossel/mes.json (mês, totais, legenda, lista das imagens).
# Mês: o mês atual a partir de hoje (no dia 1º, o mês inteiro); a partir do dia 25, já gera o mês seguinte inteiro,
# para a Aline poder preparar o post do início do mês. Só provas do RJ e de SP que não foram canceladas.
# Rodado pelo src/paginas.py (portanto pela atualização diária). Só regrava quando as provas mudam.
# Uso direto: python3 src/carrossel_mes.py [AAAA-MM-DD para simular o dia]   (não publicar o resultado da simulação)
import datetime, hashlib, json, pathlib, re, sys
from PIL import ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from paginas import D, B, M, quebra, centro, MESF  # noqa: E402
from carrossel import fundo, avatar, rodape, W, H, INK, MUTED, ACCENT, MAUVE, HOT, DIAC  # noqa: E402

VERSAO = 'm1'  # mude para forçar a regravação
root = pathlib.Path(__file__).resolve().parent.parent
PASTA = root / 'carrossel' / 'mes'
POR_SLIDE = 8
MAX_SLIDES = 18  # slides de provas (+ capa + final = 20, o máximo do Instagram)
UFS = [('RJ', 'Rio de Janeiro', 'no Rio'), ('SP', 'São Paulo', 'em SP')]


def janela(hoje):
    if hoje.day >= 25:  # já prepara o mês seguinte inteiro
        ini = (hoje.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
    else:
        ini = hoje
    fim = (ini.replace(day=1) + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    return ini, fim


def capa(base, perfil, mes, tot, n_slides):
    im = base.copy(); dr = ImageDraw.Draw(im); cx = W // 2
    r = 92; av = avatar(perfil, r)
    dr.ellipse((cx - r - 8, 150 - r - 8, cx + r + 8, 150 + r + 8), fill='white')
    if av: im.paste(av[0], (cx - r, 150 - r), av[1])
    centro(dr, cx, 262, '@' + (perfil.get('instagram') or 'amartinscc'), B(34), INK)
    centro(dr, cx, 312, 'RADAR DE CORRIDA', B(28), ACCENT)
    dr.rounded_rectangle((70, 380, W - 70, 1110), 56, fill='white')
    centro(dr, cx, 440, 'PROVAS DE', B(40), MUTED)
    centro(dr, cx, 500, MESF[mes.month - 1].capitalize(), D(140), INK)
    centro(dr, cx, 660, 'no Rio e em São Paulo', B(46), ACCENT)
    y = 780
    for uf, _, onde in UFS:
        if not tot.get(uf): continue
        txt = f'{tot[uf]} prova' + ('s' if tot[uf] != 1 else '') + ' ' + onde
        tw = dr.textlength(txt, font=D(54)) + 100
        dr.rounded_rectangle((cx - tw / 2, y, cx + tw / 2, y + 92), 46, fill=MAUVE)
        centro(dr, cx, y + 12, txt, D(54), INK)
        y += 120
    centro(dr, cx, 1160, 'Arrasta e salva o seu calendário  →', B(36), (255, 255, 255))
    rodape(dr, 1, n_slides, True)
    return im


def lista(base, titulo, itens, n, n_slides, parte):
    im = base.copy(); dr = ImageDraw.Draw(im)
    dr.text((70, 66), titulo, font=B(30), fill=ACCENT)
    if parte:
        dr.text((W - 70 - dr.textlength(parte, font=B(26)), 70), parte, font=B(26), fill=MUTED)
    y = 128; alt = 134
    for p in itens:
        d = datetime.date.fromisoformat(p['data'])
        dr.rounded_rectangle((70, y, W - 70, y + alt - 14), 30, fill='white')
        dr.rounded_rectangle((90, y + 12, 196, y + alt - 26), 22, fill=MAUVE)
        centro(dr, 143, y + 14, f'{d.day:02d}', D(54), INK)
        centro(dr, 143, y + 78, DIAC[d.weekday()], B(20), INK)
        x, larg = 220, W - 70 - 220 - 28
        destaque = '★ A Aline vai correr' if p.get('aline') else ('Cupom da Aline: ' + p['cupom'] if p.get('cupom') else None)
        nome = quebra(dr, p['nome'], D(36), larg, 1)[0]
        dr.text((x, y + 16), nome, font=D(36), fill=INK)
        lugar = p.get('cidade') if (p.get('uf') or 'RJ') != 'RJ' and p.get('cidade') else (p.get('local') or p.get('cidade'))
        info = ' · '.join(t for t in [lugar, p.get('hora', '').replace(':', 'h') if p.get('hora') else None, p.get('distancias')] if t)
        if destaque:
            dr.text((x, y + 62), quebra(dr, destaque, B(24), larg, 1)[0], font=B(24), fill=HOT)
        elif info:
            dr.text((x, y + 64), quebra(dr, info, M(24), larg, 1)[0], font=M(24), fill=MUTED)
        y += alt
    rodape(dr, n, n_slides)
    return im


def final(base, mes, sobrou, n_slides):
    im = base.copy(); dr = ImageDraw.Draw(im); cx = W // 2
    dr.rounded_rectangle((70, 200, W - 70, 1130), 56, fill='white')
    y = 280
    for l in ['Inscrições', 'e mais provas']:
        centro(dr, cx, y, l, D(104), INK); y += 116
    y += 30
    linhas = (['+' + str(sobrou) + ' prova' + ('s' if sobrou != 1 else '') + ' em ' + MESF[mes.month - 1]] if sobrou else []) + \
             ['Calendário do Rio e do Brasil', 'Calculadora de pace', 'Ofertas de tênis de corrida']
    for l in linhas:
        centro(dr, cx, y, l, B(40), ACCENT if l.startswith('+') else MUTED); y += 62
    y += 50
    tw = dr.textlength('Link na bio', font=D(64)) + 120
    dr.rounded_rectangle((cx - tw / 2, y, cx + tw / 2, y + 108), 54, fill=MAUVE)
    centro(dr, cx, y + 16, 'Link na bio', D(64), INK)
    centro(dr, cx, y + 150, 'radardecorrida.com.br', B(42), INK)
    centro(dr, cx, 1190, 'Salva e marca quem vai correr com você', B(34), (255, 255, 255))
    rodape(dr, n_slides, n_slides, True)
    return im


def legenda(mes, por_uf):
    nm = MESF[mes.month - 1]
    topo = [f'🗓️ Provas de {nm} no Rio e em São Paulo!', '']
    fim = ['Inscrições, horários e todas as provas no meu Radar de Corrida 👉 link na bio (radardecorrida.com.br)', '',
           'Salva o post e marca quem vai correr com você! 💜', '',
           '#corridaderua #corrida #riodejaneiro #saopaulo #calendariodecorrida #radardecorrida']
    blocos = []
    for uf, nome, _ in UFS:
        ps = por_uf.get(uf) or []
        if not ps: continue
        bl = [f'📍 {nome} ({len(ps)} provas)']
        for p in ps:
            d = datetime.date.fromisoformat(p['data'])
            bl.append(f"• {d.day:02d}/{d.month:02d} – {p['nome']}" + (' ⭐ eu vou!' if p.get('aline') else ''))
        blocos.append(bl)
    # corta as listas por igual até caber no limite de legenda do Instagram (2.200)
    n = max((len(b) for b in blocos), default=0)
    while True:
        linhas = list(topo)
        for b in blocos:
            linhas += b[:n] + ([f'…e mais {len(b) - n} no radar'] if len(b) > n else []) + ['']
        txt = '\n'.join(linhas + fim)
        if len(txt) <= 2150 or n <= 2: return txt
        n -= 1


def main(hoje=None):
    s = (root / 'index.html').read_text()
    d = json.loads(re.search(r'<script id="radar-data" type="application/json">(.*?)</script>', s, re.S).group(1))
    perfil = d.get('perfil') or {}
    hoje = hoje or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).date()
    ini, fim = janela(hoje)
    por_uf = {}
    for uf, _, _ in UFS:
        ps = [p for p in (d.get('provas') or []) if (p.get('uf') or 'RJ') == uf and p.get('status') != 'cancelada'
              and ini.isoformat() <= p['data'] <= fim.isoformat()]
        ps.sort(key=lambda p: (p['data'], not p.get('aline'), not p.get('cupom'), p.get('hora') or '99', p['nome']))
        por_uf[uf] = ps
    tot = {uf: len(ps) for uf, ps in por_uf.items()}
    chave = hashlib.sha1(json.dumps([VERSAO, ini.isoformat(), por_uf, perfil.get('instagram'), hashlib.sha1((perfil.get('foto') or '').encode()).hexdigest()], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    PASTA.mkdir(parents=True, exist_ok=True)
    jpath = root / 'carrossel' / 'mes.json'
    atual = json.loads(jpath.read_text()) if jpath.exists() else {}
    if atual.get('chave') == chave and all((root / i).exists() for i in atual.get('imagens', [])):
        print(f'carrossel do mês: sem mudança ({sum(tot.values())} provas)'); return
    for f in PASTA.glob('*.jpg'): f.unlink()
    # divide os slides entre RJ e SP (no máximo MAX_SLIDES, proporcional ao número de provas)
    nec = {uf: -(-len(ps) // POR_SLIDE) for uf, ps in por_uf.items()}
    while sum(nec.values()) > MAX_SLIDES:
        maior = max(nec, key=lambda k: nec[k]); nec[maior] -= 1
    imagens, mostrados = [], 0
    total = sum(tot.values())
    if total:
        grupos = []
        for uf, nome, _ in UFS:
            ps = por_uf[uf][:nec[uf] * POR_SLIDE]
            mostrados += len(ps)
            gs = [ps[i:i + POR_SLIDE] for i in range(0, len(ps), POR_SLIDE)]
            for k, g in enumerate(gs):
                grupos.append((f'{MESF[ini.month - 1].upper()} · {nome.upper()}', g, f'{k + 1}/{len(gs)}' if len(gs) > 1 else ''))
        n_slides = len(grupos) + 2
        base = fundo()
        slides = [capa(base, perfil, ini, tot, n_slides)] + \
                 [lista(base, t, g, i + 2, n_slides, parte) for i, (t, g, parte) in enumerate(grupos)] + \
                 [final(base, ini, total - mostrados, n_slides)]
        v = chave[:8]
        for i, im in enumerate(slides, 1):
            nome = f'carrossel/mes/{i}-{v}.jpg'
            im.convert('RGB').save(root / nome, 'JPEG', quality=90, optimize=True)
            imagens.append(nome)
    info = {'chave': chave, 'gerado': hoje.isoformat(), 'de': ini.isoformat(), 'ate': fim.isoformat(),
            'mes': MESF[ini.month - 1], 'ano': ini.year, 'total': total, 'por_uf': tot, 'imagens': imagens,
            'legenda': legenda(ini, por_uf) if total else ''}
    jpath.write_text(json.dumps(info, ensure_ascii=False, indent=1))
    print(f'carrossel do mês: {MESF[ini.month - 1]} de {ini.year}, {total} provas (RJ {tot.get("RJ", 0)}, SP {tot.get("SP", 0)}), {len(imagens)} imagens')


if __name__ == '__main__':
    main(datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else None)
