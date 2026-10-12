# Regera index.html a partir de src/template.html, mantendo os dados atuais (bloco radar-data do index.html).
# Uso: python3 src/build.py [URL_DO_SITE]
import json, re, sys, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
SITE_URL = sys.argv[1] if len(sys.argv) > 1 else (root / 'CNAME').read_text().strip() if (root / 'CNAME').exists() else 'amartinscc.github.io/radar-de-corrida'
if not SITE_URL.startswith('http'): SITE_URL = 'https://' + SITE_URL.strip('/') + '/'
cur = (root / 'index.html').read_text()
data = json.loads(re.search(r'<script id="radar-data" type="application/json">(.*?)</script>', cur, re.S).group(1))
t = (root / 'src' / 'template.html').read_text()
body = t.replace('__DATA__', json.dumps(data, ensure_ascii=False, indent=1))
body = re.sub(r"const RADAR_URL = '[^']*';", "const RADAR_URL = '" + SITE_URL + "';", body)
head = cur[:cur.index('<title>')]
head = re.sub(r'(og:url" content=")[^"]*', r'\g<1>' + SITE_URL, head)
head = re.sub(r'(og:image" content=")[^"]*', r'\g<1>' + SITE_URL + 'og.jpg', head)
(root / 'index.html').write_text(head + body + '\n</body>\n</html>\n')
print('ok')
