# Monta o HTML do e-mail semanal "Radar de Corrida" (MailerLite, toda quinta) a partir do index.html e do carrossel.
# Uso: python3 src/newsletter.py SAIDA.html [AAAA-MM-DD]
# Imprime um JSON com assunto, pré-cabeçalho e contagens. Não altera nenhum arquivo do site.
# Regras: os links levam para as páginas do radar (nunca link de afiliada direto no e-mail: a Amazon proíbe),
# com utm_source=newsletter para o painel saber a origem. O rodapé leva {$unsubscribe} (exigido pelo MailerLite).
import datetime, html, json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from paginas import slugs, prova_base, prova_extra, tenis_base, tenis_extra, brl, slug, MESF  # noqa: E402

root = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://' + (root / 'CNAME').read_text().strip().strip('/') + '/'
DIAS = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
ST = {'esgotada': 'Esgotada', 'parcial': 'Últimos lotes', 'embreve': 'Inscrições em breve', 'adiada': 'Adiada'}
E = lambda s: html.escape(str(s or ''), quote=True)
INK, MUTED, ACCENT, MAUVE, HOT, LINE, SOFT = '#1D1220', '#6B5A6E', '#7A4E7D', '#B28AB1', '#B4501F', '#E7DAE8', '#F6F0F6'
FONT = "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;"


def utm(url, hoje, conteudo):
    sep = '&' if '?' in url.split('#')[0] else '?'
    base, _, frag = url.partition('#')
    return f'{base}{sep}utm_source=newsletter&utm_medium=email&utm_campaign=semanal-{hoje}&utm_content={conteudo}' + (f'#{frag}' if frag else '')


def botao(txt, url, cor=MAUVE, tinta=INK):
    return (f'<a href="{E(url)}" style="display:inline-block;background:{cor};color:{tinta};text-decoration:none;{FONT}'
            f'font-weight:700;font-size:15px;padding:12px 22px;border-radius:999px">{E(txt)}</a>')


def titulo_secao(txt, sub=''):
    s = f'<p style="margin:0 0 4px;{FONT}font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:{ACCENT}">{E(sub)}</p>' if sub else ''
    return f'<tr><td style="padding:28px 24px 8px">{s}<h2 style="margin:0;{FONT}font-size:24px;line-height:1.2;color:{INK}">{E(txt)}</h2></td></tr>'


def main():
    saida = pathlib.Path(sys.argv[1])
    hoje = datetime.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).date()
    s = (root / 'index.html').read_text()
    d = json.loads(re.search(r'<script id="radar-data" type="application/json">(.*?)</script>', s, re.S).group(1))
    hj = hoje.isoformat()

    # provas das próximas 4 semanas (a partir de 3 dias, para dar tempo de se inscrever), só RJ, sem canceladas/esgotadas
    provas = d.get('provas') or []
    ps = dict(zip(map(id, provas), slugs(provas, prova_base, prova_extra)))
    ini = hoje + datetime.timedelta(days=3)
    fim = hoje + datetime.timedelta(days=31)
    prox = [p for p in provas if (p.get('uf') or 'RJ') == 'RJ' and p.get('status') not in ('cancelada', 'esgotada')
            and ini.isoformat() <= p['data'] <= fim.isoformat()]
    prox.sort(key=lambda p: (p['data'], not p.get('aline'), not p.get('cupom'), p.get('status') == 'confira', p.get('hora') or '99', p['nome']))
    def semana(dt):  # segunda-feira da semana
        x = datetime.date.fromisoformat(dt); return x - datetime.timedelta(days=x.weekday())
    semanas = []
    for p in prox:
        s = semana(p['data'])
        if not semanas or semanas[-1][0] != s: semanas.append((s, []))
        semanas[-1][1].append(p)
    fds = prox  # compatibilidade com o relatório
    dias = sorted({p['data'] for p in prox})

    # achados: primeiro os que rendem comissão para a Aline (escolhas dela e Amazon), depois os maiores descontos
    ofs = d.get('ofertas') or []
    os_ = dict(zip(map(id, ofs), slugs(ofs, tenis_base, tenis_extra)))
    for o in ofs:
        o['_off'] = round((1 - o['preco'] / o['de']) * 100) if o.get('de') and o['de'] > o['preco'] else 0
    def comissao(o):
        u = o.get('link') or ''
        return bool(o.get('escolha') or re.search(r'(^|//)(www\.)?(amazon\.com\.br|amzn\.to|a\.co)/', u) or 'tag=amartins0b-20' in u)
    def variado(lista, n, por_cat=2):
        sel, cats, marcas = [], {}, {}
        for o in lista:
            c = o.get('categoria') or 'Tênis'
            if cats.get(c, 0) < por_cat and not marcas.get(o.get('marca')):
                sel.append(o); cats[c] = cats.get(c, 0) + 1; marcas[o.get('marca')] = 1
            if len(sel) == n: break
        for o in lista:
            if len(sel) >= n: break
            if o not in sel: sel.append(o)
        return sel
    com = sorted([o for o in ofs if comissao(o)], key=lambda o: (not o.get('escolha'), -o['_off']))
    destaques = [o for o in com if o.get('escolha')][:4]
    destaques += variado([o for o in com if o not in destaques], 8 - len(destaques))
    outros = variado(sorted([o for o in ofs if o not in destaques], key=lambda o: -o['_off']), 4)
    escolhidos = destaques + outros

    # parceiros com campanha ou ofertas
    pc = d.get('parceiros') or {}
    parc = [m for m in (pc.get('marcas') or []) if m.get('campanha') or m.get('ofertas')]

    datas = f'{ini.day}/{ini.month:02d} a {fim.day}/{fim.month:02d}'
    assunto = (f'🏃‍♀️ {len(prox)} provas no Rio nas próximas semanas + indicações da Aline' if prox else '🏃‍♀️ Indicações da Aline e achados de corrida da semana')
    pre = (f'Corridas de {datas} com inscrições abertas, as indicações da Aline e os cupons dos parceiros.' if prox else 'As indicações da Aline, os maiores descontos em corrida e os cupons dos parceiros.')

    L = []
    L.append(f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(assunto)}</title></head>')
    L.append(f'<body style="margin:0;padding:0;background:{SOFT}"><span style="display:none;max-height:0;overflow:hidden;opacity:0">{E(pre)}</span>')
    L.append(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{SOFT}"><tr><td align="center" style="padding:16px 8px">')
    L.append(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:20px;overflow:hidden">')
    # topo
    L.append(f'<tr><td style="padding:22px 24px 6px;background:linear-gradient(135deg,#BBE3E5,#D9C1D9)"><p style="margin:0;{FONT}font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:{ACCENT}">Radar de Corrida · {DIAS[hoje.weekday()]}, {hoje.day} de {MESF[hoje.month - 1]}</p>'
             f'<h1 style="margin:6px 0 4px;{FONT}font-size:28px;line-height:1.15;color:{INK}">Sua semana de corrida 🏃‍♀️</h1>'
             f'<p style="margin:0 0 16px;{FONT}font-size:15px;color:{INK}">Oi! Aqui é a Aline. Separei o que eu indico para quem corre, as provas no Rio das próximas semanas (ainda dá tempo de se inscrever) e os cupons dos meus parceiros.</p></td></tr>')

    def grade(itens, destaque):
        if not itens: return
        borda = f'2px solid #E2B13C' if destaque else f'1px solid {LINE}'
        L.append('<tr><td style="padding:6px 16px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">')
        for i in range(0, len(itens), 2):
            L.append('<tr>')
            for o in itens[i:i + 2]:
                url = utm(f'{SITE}tenis/{os_[id(o)]}/?c=1', hj, 'indicacao' if destaque else 'achado')
                selo = (f'<span style="display:inline-block;margin-bottom:5px;background:#FFF3D6;color:#7A4E00;{FONT}font-size:11px;font-weight:800;padding:3px 8px;border-radius:999px">★ {"Escolha da Aline" if o.get("escolha") else "Indicação da Aline"}</span><br>') if destaque else ''
                tag = f'-{o["_off"]}%' if o['_off'] else '★'
                foto = (f'<img src="{E(o["foto"])}" width="250" alt="" style="display:block;width:100%;height:170px;object-fit:contain;background:#fff;border:0">' if o.get('foto')
                        else f'<div style="height:110px;background:{SOFT};{FONT}font-size:40px;font-weight:800;color:{ACCENT};text-align:center;line-height:110px">{tag}</div>')
                cab = ' · '.join(v for v in [o.get('categoria') if o.get('categoria') not in (None, 'Tênis') else None, o.get('marca'), o.get('loja') if o.get('loja') != o.get('marca') else None] if v)
                de = f' <span style="{FONT}font-size:12px;color:{MUTED};text-decoration:line-through">{E(brl(o["de"]))}</span>' if o['_off'] else ''
                rot = (f'-{o["_off"]}% · ' if o['_off'] else '') + ('Quero esse →' if destaque else 'Ver oferta →')
                L.append(f'<td width="50%" valign="top" style="padding:6px"><a href="{E(url)}" style="display:block;text-decoration:none;border:{borda};border-radius:14px;overflow:hidden">{foto}'
                         f'<span style="display:block;padding:10px 12px 12px">{selo}<span style="display:block;{FONT}font-size:11px;font-weight:700;color:{MUTED};text-transform:uppercase;letter-spacing:.05em">{E(cab)}</span>'
                         f'<span style="display:block;{FONT}font-size:14px;font-weight:700;color:{INK};margin:3px 0">{E(o["nome"])}</span>'
                         f'<span style="{FONT}font-size:17px;font-weight:800;color:{HOT}">{E(brl(o["preco"]))}</span>{de}'
                         f'<span style="display:block;{FONT}font-size:12px;font-weight:700;color:{ACCENT};margin-top:4px">{rot}</span></span></a></td>')
            if len(itens[i:i + 2]) == 1: L.append('<td width="50%"></td>')
            L.append('</tr>')
        L.append('</table></td></tr>')

    # 1) indicações da Aline (produtos que rendem comissão): primeiro e em destaque
    if destaques:
        L.append(titulo_secao('Indicações da Aline', 'O que eu uso e recomendo'))
        L.append(f'<tr><td style="padding:2px 24px 4px;{FONT}font-size:14px;color:{INK}">Comprando por estes links você apoia o Radar de Corrida, sem pagar nada a mais. 💜</td></tr>')
        grade(destaques, True)

    # 2) provas das próximas semanas
    if prox:
        L.append(titulo_secao('Próximas provas no Rio', f'{datas} · inscrições abertas'))
        for seg, lista in semanas:
            dom = seg + datetime.timedelta(days=6)
            L.append(f'<tr><td style="padding:16px 24px 4px;{FONT}font-size:13px;font-weight:800;color:{HOT};text-transform:uppercase;letter-spacing:.06em">Semana de {seg.day:02d}/{seg.month:02d} a {dom.day:02d}/{dom.month:02d}</td></tr>')
            for p in lista[:6]:
                x = datetime.date.fromisoformat(p['data'])
                url = utm(f'{SITE}prova/{ps[id(p)]}/?c=1', hj, 'prova')
                info = ' · '.join(v for v in [p.get('local'), p['hora'].replace(':', 'h') if p.get('hora') else None, p.get('distancias')] if v)
                ext = ' · '.join(v for v in ['Gratuita' if p.get('valor') == 0 else (f"a partir de {brl(p['valor'])}" if isinstance(p.get('valor'), (int, float)) else None), ST.get(p.get('status'))] if v)
                dest = ''
                if p.get('aline'): dest += f'<span style="color:{HOT};font-weight:700">★ A Aline vai correr</span> '
                if p.get('cupom'): dest += f'<span style="color:{HOT};font-weight:700">Cupom da Aline: {E(p["cupom"])}</span>'
                L.append(f'<tr><td style="padding:5px 24px"><a href="{E(url)}" style="display:block;text-decoration:none;border:1px solid {LINE};border-radius:14px;padding:10px 14px">'
                         f'<span style="display:block;{FONT}font-size:12px;font-weight:800;color:{ACCENT};text-transform:uppercase">{DIAS[x.weekday()]}, {x.day:02d}/{x.month:02d}</span>'
                         f'<span style="display:block;{FONT}font-size:16px;font-weight:700;color:{INK};margin-top:2px">{E(p["nome"])}</span>'
                         f'<span style="display:block;{FONT}font-size:13px;color:{MUTED};margin-top:2px">{E(info)}</span>'
                         + (f'<span style="display:block;{FONT}font-size:13px;color:{MUTED}">{E(ext)}</span>' if ext else '')
                         + (f'<span style="display:block;{FONT}font-size:13px;margin-top:3px">{dest}</span>' if dest else '')
                         + f'<span style="display:block;{FONT}font-size:13px;font-weight:700;color:{ACCENT};margin-top:5px">Ver inscrição →</span></a></td></tr>')
            if len(lista) > 6:
                L.append(f'<tr><td style="padding:2px 24px;{FONT}font-size:13px;color:{MUTED}">+{len(lista) - 6} provas nesta semana no radar</td></tr>')
        L.append(f'<tr><td align="center" style="padding:14px 24px 4px">{botao("Ver o calendário completo", utm(SITE + "#provas", hj, "provas"))}</td></tr>')

    # 3) outros achados (maiores descontos)
    if outros:
        L.append(titulo_secao('Mais achados da semana', 'Maiores descontos'))
        grade(outros, False)
        L.append(f'<tr><td align="center" style="padding:10px 24px 4px">{botao("Ver todos os achados", utm(SITE + "#achados", hj, "achados"))}</td></tr>')
        L.append(f'<tr><td style="padding:6px 24px 0;{FONT}font-size:12px;color:{MUTED};text-align:center">Preços conferidos pelo radar; podem mudar ao longo do dia.</td></tr>')

    # parceiros
    if parc:
        L.append(titulo_secao('Dos parceiros da Aline', 'Com o meu cupom'))
        for m in parc[:8]:
            code = m.get('cupom') or pc.get('cupom') or ''
            url = utm(f'{SITE}#parceiro={slug(m["nome"])}', hj, 'parceiro')
            ofl = ''.join(f'<span style="display:block;{FONT}font-size:13px;color:{INK};margin-top:2px">• {E(o["nome"])}' + (f' por <b style="color:{HOT}">{E(brl(o["preco"]))}</b>' if isinstance(o.get('preco'), (int, float)) else '') + '</span>' for o in (m.get('ofertas') or [])[:3])
            L.append(f'<tr><td style="padding:6px 24px"><a href="{E(url)}" style="display:block;text-decoration:none;border:1px solid {LINE};border-radius:14px;padding:12px 14px">'
                     f'<span style="display:block;{FONT}font-size:16px;font-weight:700;color:{INK}">{E(m["nome"])}'
                     + (f' <span style="{FONT}font-size:12px;font-weight:700;color:{ACCENT};border:1.5px dashed {MAUVE};border-radius:999px;padding:2px 8px;margin-left:4px">cupom {E(code)}</span>' if code else '') + '</span>'
                     + (f'<span style="display:block;{FONT}font-size:13px;font-weight:700;color:{HOT};margin-top:4px">{E(m["campanha"])}</span>' if m.get('campanha') else '')
                     + ofl + f'<span style="display:block;{FONT}font-size:13px;font-weight:700;color:{ACCENT};margin-top:6px">Ver no radar →</span></a></td></tr>')
    else:
        L.append(titulo_secao('Dos parceiros da Aline', 'Com o meu cupom'))
        L.append(f'<tr><td style="padding:6px 24px;{FONT}font-size:15px;color:{INK}">Roupas, suplementos e alimentação das marcas que eu uso, com o cupom <b>{E(pc.get("cupom") or "AMARTINS")}</b>.</td></tr>')
        L.append(f'<tr><td align="center" style="padding:10px 24px 4px">{botao("Ver os parceiros", utm(SITE + "#parceiros", hj, "parceiros"))}</td></tr>')

    # fechamento
    L.append(f'<tr><td style="padding:28px 24px 8px;text-align:center"><p style="margin:0 0 12px;{FONT}font-size:15px;color:{INK}">Bons treinos e boas provas! 💜<br><b>Aline</b></p>'
             f'{botao("Seguir @amartinscc no Instagram", "https://www.instagram.com/amartinscc/", INK, "#ffffff")}</td></tr>')
    L.append(f'<tr><td style="padding:18px 24px 24px;{FONT}font-size:12px;line-height:1.5;color:{MUTED};text-align:center">'
             f'Este e-mail não recebe respostas. Para falar com a Aline, chame no Instagram <a href="https://www.instagram.com/amartinscc/" style="color:{ACCENT}">@amartinscc</a>.<br>'
             f'Alguns links levam a ofertas com link de afiliada: a Aline pode receber comissão, sem custo extra para você.<br>'
             f'Você recebe este e-mail porque se inscreveu no <a href="{E(SITE)}" style="color:{ACCENT}">radardecorrida.com.br</a>. '
             f'<a href="{{$unsubscribe}}" style="color:{ACCENT}">Cancelar inscrição</a> · <a href="{E(SITE)}privacidade/" style="color:{ACCENT}">Privacidade</a></td></tr>')
    L.append('</table></td></tr></table></body></html>')
    saida.write_text(''.join(L))
    print(json.dumps({'assunto': assunto, 'pre_cabecalho': pre, 'provas': len(fds), 'achados': len(escolhidos), 'indicacoes': len(destaques), 'parceiros': len(parc),
                      'datas': datas, 'bytes': saida.stat().st_size}, ensure_ascii=False))


if __name__ == '__main__':
    main()
