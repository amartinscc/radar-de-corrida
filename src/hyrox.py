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

# parceiros do Radar Hyrox (ordem da aba): logo do cadastro do radar principal + texto próprio do Hyrox
PARC_HX = [('Puma', 'Parceira oficial do HYROX', 'Tênis, roupas e acessórios da linha PUMA × HYROX.', 'https://br.puma.com/'),
           ('Decathlon', 'Loja parceira', 'Tênis de treino, kettlebell, corda, luvas e roupas para treinar HYROX, com preço de Decathlon.', 'https://www.decathlon.com.br/')]
_mk = {m['nome']: m for m in data['parceiros']['marcas']}
parc_hx = [{'nome': n, 'selo': sl, 'texto': tx, 'loja': lj, 'logo': _mk[n].get('logo', '')} for n, sl, tx, lj in PARC_HX if n in _mk and not _mk[n].get('oculto')]
dados = {'perfil': {'instagram': (data.get('perfil') or {}).get('instagram', 'amartinscc')},
         'assessoria': data.get('assessoria') or {}, 'treino_em_breve': data.get('treino_em_breve')}

h = (root / 'src' / 'hyrox-template.html').read_text()

# links de afiliada, Modo Aline (senha) e "Meus links de loja": os mesmos do radar principal
ai = t.index('  const AFIL = {amazon'); aj = t.index('  const temAfil', ai)
afil_js = re.sub(r"  const PARAM_SITE = .*?\n", "  const PARAM_SITE = {};\n", t[ai:aj]).rstrip()
adm_hash = re.search(r"const ADM_HASH = '([0-9a-f]{64})';", t).group(1)
li = t.index('  // Meus links de loja'); tela_links = t[li:t.index('  function menuAdm(){', li)].rstrip()

# SEO: dados estruturados gerados do FAQ visível (perguntas e respostas sempre iguais às da página)
import html as _html
def _txt(x): return _html.unescape(re.sub(r'<[^>]+>', '', x)).strip()
faq = [{'@type': 'Question', 'name': _txt(q), 'acceptedAnswer': {'@type': 'Answer', 'text': _txt(r)}}
       for q, r in re.findall(r'<details><summary>(.*?)</summary><p>(.*?)</p></details>', h[h.index('id="o-que-e-hyrox"'):], re.S)]
assert len(faq) >= 8, 'FAQ do Hyrox não encontrado'
URL = 'https://radardecorrida.com.br/hyrox/'
ld = {'@context': 'https://schema.org', '@graph': [
    {'@type': 'WebPage', '@id': URL, 'url': URL, 'name': 'Radar Hyrox da Aline', 'inLanguage': 'pt-BR',
     'description': 'O que é HYROX, as 8 estações, categorias e pesos, provas oficiais, simulados e aulões no Brasil e onde treinar.',
     'about': {'@type': 'Thing', 'name': 'HYROX'}, 'image': URL + 'og.jpg',
     'author': {'@type': 'Person', 'name': 'Aline Martins', 'url': 'https://www.instagram.com/amartinscc/'},
     'isPartOf': {'@type': 'WebSite', 'name': 'Radar de Corrida', 'url': 'https://radardecorrida.com.br/'}},
    {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Radar de Corrida', 'item': 'https://radardecorrida.com.br/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Radar Hyrox', 'item': URL}]},
    {'@type': 'FAQPage', 'mainEntity': faq}]}
jsonld = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace('</', '<\\/') + '</script>'
for k, v in {'__MAIN_CSS__': css, '__TABS__': tabs.rstrip('\n'), '__TREINO_HTML__': treino_html.rstrip('\n'),
             '__TREINO_JS__': treino_js.rstrip('\n'), '__STATES__': states,
             '__DATA__': json.dumps(dados, ensure_ascii=False), '__JSONLD__': jsonld, '__AFIL_JS__': afil_js, '__ADM_HASH__': adm_hash, '__TELA_LINKS__': tela_links, '__PARC_HYROX__': json.dumps(parc_hx, ensure_ascii=False).replace('</', '<\\/')}.items():
    assert k in h, k
    h = h.replace(k, v)
(root / 'hyrox' / 'index.html').write_text(h)
print('hyrox/index.html:', len(h), 'bytes')
