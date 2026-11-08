# Gera hyrox/index.html (Radar Hyrox) a partir de src/hyrox-template.html, reaproveitando do radar principal
# (src/template.html e index.html): o CSS inteiro, as abas redondas, o mapa dos estados (STATES) e a aba Treine comigo.
# Uso: python3 src/hyrox.py   (rodar de novo quando mudar o visual do radar principal ou a assessoria)
import json, re, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
t = (root / 'src' / 'template.html').read_text()
idx = (root / 'index.html').read_text()
data = json.loads(re.search(r'<script id="radar-data" type="application/json">(.*?)</script>', idx, re.S).group(1))

css = t[t.index('<style>') + len('<style>'):t.index('</style>')]
states = re.search(r'const STATES = (\{.*?\});\n', t).group(1)

def tab(id_):
    return re.search(r'    <button class="tab" role="tab" id="' + id_ + r'".*?</button>\n', t).group(0)
tabs = tab('tab-provas').replace('<span class="lb">Provas</span>', '<span class="lb">Radar</span>')
tabs += tab('tab-tenis')
tabs += tab('tab-roupas')
tabs += (tab('tab-result').replace('class="tab" role="tab" id="tab-result" aria-controls="p-result"', 'class="tab" role="tab" id="tab-result" disabled title="Em breve"')
         .replace('<span class="c" id="c-result"></span>', '<span class="c">em breve</span>'))
tabs += tab('tab-treino')
tabs = re.sub(r'<span class="c" id="c-(provas|tenis|roupas)"></span>', '<span class="c"></span>', tabs)
tabs = tabs.replace('<span class="lb">Parceiros</span>', '<span class="lb">Parceiros</span>')

i = t.index('<section class="tr-soon"')
treino_html = '    ' + t[i:t.index('<div class="news" data-origem="treine"', i)].rstrip() + '\n'
j = t.index('  // assessoria (prévia)')
treino_js = t[j:t.index('  // compartilhar nos stories', j)]

pm = next(m for m in data['parceiros']['marcas'] if m['nome'] == 'Puma')
dados = {'perfil': {'instagram': (data.get('perfil') or {}).get('instagram', 'amartinscc')},
         'assessoria': data.get('assessoria') or {}, 'treino_em_breve': data.get('treino_em_breve')}

h = (root / 'src' / 'hyrox-template.html').read_text()
for k, v in {'__MAIN_CSS__': css, '__TABS__': tabs.rstrip('\n'), '__TREINO_HTML__': treino_html.rstrip('\n'),
             '__TREINO_JS__': treino_js.rstrip('\n'), '__STATES__': states,
             '__DATA__': json.dumps(dados, ensure_ascii=False), '__PUMA_LOGO__': pm.get('logo', '')}.items():
    assert k in h, k
    h = h.replace(k, v)
(root / 'hyrox' / 'index.html').write_text(h)
print('hyrox/index.html:', len(h), 'bytes')
