# Gera os dados do painel de métricas (página privada painel/<PAINEL>/), a partir das duas consultas
# de src/painel-consultas.sql rodadas no PostHog (saída em texto, colunas separadas por |, com cabeçalho).
# Uso: python3 src/painel.py agregado.txt diario.txt
# Grava painel/<PAINEL>/dados.json. Não mexe em mais nada do site.
import datetime, json, pathlib, sys

PAINEL = 'rc-5yecuqq3sbbk9h'  # endereço secreto: radardecorrida.com.br/painel/<PAINEL>/
root = pathlib.Path(__file__).resolve().parent.parent
BRT = datetime.timezone(datetime.timedelta(hours=-3))


def linhas(caminho, colunas):
    txt = pathlib.Path(caminho).read_text(encoding='utf-8')
    out, cab = [], None
    for ln in txt.splitlines():
        ln = ln.rstrip('\r')
        if not ln.strip() or ln.startswith('<') or ln.startswith('- '):
            continue
        partes = ln.split('|')
        if cab is None:
            if partes[:len(colunas)] == colunas:
                cab = partes
            continue
        if len(partes) != len(cab):
            # rótulo com | dentro: junta o excesso no campo de texto
            extra = len(partes) - len(cab)
            if extra > 0 and 'rotulo' in cab:
                i = cab.index('rotulo')
                partes = partes[:i] + ['|'.join(partes[i:i + extra + 1])] + partes[i + extra + 1:]
            else:
                raise SystemExit(f'linha com colunas erradas em {caminho}: {ln!r}')
        out.append(dict(zip(cab, partes)))
    if cab is None:
        raise SystemExit(f'cabeçalho {"|".join(colunas)} não encontrado em {caminho}')
    return out


def main():
    if len(sys.argv) != 3:
        raise SystemExit('uso: python3 src/painel.py agregado.txt diario.txt')
    ag = linhas(sys.argv[1], ['p', 'dim', 'rotulo', 'visitas', 'vezes'])
    di = linhas(sys.argv[2], ['dia', 'visitas', 'instagram'])
    periodos = {}
    for r in ag:
        p = periodos.setdefault(r['p'], {})
        rot = r['rotulo']
        if rot == '(null)':
            rot = ''
        p.setdefault(r['dim'], []).append([rot, int(r['visitas']), int(r['vezes'])])
    if '7' not in periodos or 'evento' not in periodos['7']:
        raise SystemExit('dados sem o período de 7 dias: confira a saída da consulta [1]')
    dados = {
        'gerado': datetime.datetime.now(BRT).strftime('%Y-%m-%dT%H:%M:%S-03:00'),
        'periodos': periodos,
        'diario': [[r['dia'], int(r['visitas']), int(r['instagram'])] for r in di],
    }
    destino = root / 'painel' / PAINEL / 'dados.json'
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(dados, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    v7 = dict((x[0], x[1]) for x in periodos['7']['evento']).get('$pageview', 0)
    print(f'painel: {len(ag)} linhas agregadas, {len(di)} dias, {v7} visitas em 7 dias -> {destino.relative_to(root)}')


if __name__ == '__main__':
    main()
