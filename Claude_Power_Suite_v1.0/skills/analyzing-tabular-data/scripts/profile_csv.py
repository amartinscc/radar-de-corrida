#!/usr/bin/env python3
"""Perfil de qualidade de um arquivo CSV/TSV usando só a biblioteca padrão.

Detecta automaticamente: codificação (utf-8, utf-8-sig, cp1252, latin-1),
delimitador (, ; \\t |) e números no formato brasileiro (1.234,56).

Para cada coluna: tipo inferido (inteiro, decimal, data, booleano, texto),
nulos, valores distintos, mín/máx, média, mediana, desvio-padrão, top valores
e outliers pela regra de Tukey (fora de Q1−1,5·IQR … Q3+1,5·IQR).
Para o arquivo: linhas, linhas duplicadas, linhas com nº de campos divergente.

Uso:
  python3 profile_csv.py dados.csv [--json] [--max-rows N] [--delimiter ';']
                         [--encoding latin-1] [--top 5]
Código de saída: 0 sucesso, 2 arquivo ilegível/vazio.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
DELIMITERS = ",;\t|"
NULL_TOKENS = {"", "na", "n/a", "nan", "null", "none", "nil", "-", "--", "?"}
TRUE_TOKENS = {"true", "verdadeiro", "sim", "yes", "y", "s", "t"}
FALSE_TOKENS = {"false", "falso", "nao", "não", "no", "n", "f"}
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                "%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%m/%d/%Y")
# Uma coluna recebe um tipo se >= 95% dos valores não nulos se encaixam nele;
# tolera poucos valores sujos sem rebaixar a coluna inteira para texto.
TYPE_THRESHOLD = 0.95
# Amostra usada para farejar o delimitador: 64 KiB cobre centenas de linhas.
SNIFF_BYTES = 65536

INT_RE = re.compile(r"^[+-]?\d+$")
INT_BR_RE = re.compile(r"^[+-]?\d{1,3}(\.\d{3})+$")
DEC_US_RE = re.compile(r"^[+-]?(\d{1,3}(,\d{3})+|\d+)\.\d+$")
DEC_BR_RE = re.compile(r"^[+-]?(\d{1,3}(\.\d{3})+|\d+),\d+$")


def read_text(path: Path, encoding: str | None) -> tuple[str, str]:
    raw = path.read_bytes()
    for enc in ([encoding] if encoding else ENCODINGS):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("?", raw, 0, 1, "nenhuma codificação conhecida funcionou")


def sniff_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample, delimiters=DELIMITERS).delimiter
    except csv.Error:
        first = sample.splitlines()[0] if sample else ""
        return max(DELIMITERS, key=first.count)


def to_number(value: str) -> tuple[float | None, str | None]:
    v = value.strip().replace(" ", "")
    if INT_RE.match(v):
        return float(v), "int"
    if INT_BR_RE.match(v):
        return float(v.replace(".", "")), "int"
    if DEC_US_RE.match(v):
        return float(v.replace(",", "")), "float"
    if DEC_BR_RE.match(v):
        return float(v.replace(".", "").replace(",", ".")), "float"
    return None, None


def to_date(value: str) -> dt.datetime | None:
    v = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return dt.datetime.strptime(v, fmt)
        except ValueError:
            continue
    return None


def profile_column(name: str, values: list[str], top: int) -> dict:
    non_null = [v for v in values if v.strip().lower() not in NULL_TOKENS]
    col = {"name": name, "count": len(values), "nulls": len(values) - len(non_null),
           "null_pct": round(100 * (len(values) - len(non_null)) / len(values), 2) if values else 0.0,
           "distinct": len(set(non_null))}
    if not non_null:
        col["type"] = "vazia"
        return col

    numbers, kinds = [], Counter()
    for v in non_null:
        num, kind = to_number(v)
        if num is not None:
            numbers.append(num)
            kinds[kind] += 1
    dates = [d for d in (to_date(v) for v in non_null) if d is not None]
    bools = [v for v in non_null if v.strip().lower() in TRUE_TOKENS | FALSE_TOKENS]
    n = len(non_null)

    if len(bools) / n >= TYPE_THRESHOLD and col["distinct"] <= 4:
        col["type"] = "booleano"
    elif len(numbers) / n >= TYPE_THRESHOLD:
        col["type"] = "inteiro" if kinds["float"] == 0 else "decimal"
        col["invalid"] = n - len(numbers)
        col.update(numeric_stats(numbers))
    elif len(dates) / n >= TYPE_THRESHOLD:
        col["type"] = "data"
        col["invalid"] = n - len(dates)
        col["min"], col["max"] = min(dates).isoformat(), max(dates).isoformat()
    else:
        col["type"] = "texto"
        lengths = [len(v) for v in non_null]
        col["min_len"], col["max_len"] = min(lengths), max(lengths)
        stripped = sum(1 for v in non_null if v != v.strip())
        if stripped:
            col["leading_trailing_spaces"] = stripped
        case_groups = Counter(v.strip().lower() for v in non_null)
        variants = sum(1 for k in case_groups if len({v.strip() for v in non_null if v.strip().lower() == k}) > 1) \
            if col["distinct"] <= 5000 else None
        if variants:
            col["case_variants"] = variants
    col["top_values"] = Counter(non_null).most_common(top)
    if col["distinct"] == n and n > 1:
        col["unique"] = True
    return col


def numeric_stats(nums: list[float]) -> dict:
    nums_sorted = sorted(nums)
    out = {"min": nums_sorted[0], "max": nums_sorted[-1],
           "mean": round(statistics.fmean(nums_sorted), 4),
           "median": statistics.median(nums_sorted)}
    if len(nums_sorted) >= 2:
        out["stdev"] = round(statistics.stdev(nums_sorted), 4)
    if len(nums_sorted) >= 4:
        q1, _, q3 = statistics.quantiles(nums_sorted, n=4)
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        out["q1"], out["q3"] = round(q1, 4), round(q3, 4)
        out["outliers"] = sum(1 for x in nums_sorted if x < lo or x > hi)
    for k, v in list(out.items()):
        if isinstance(v, float) and math.isfinite(v) and v.is_integer():
            out[k] = int(v)
    return out


def profile(path: Path, delimiter: str | None, encoding: str | None,
            max_rows: int | None, top: int) -> dict:
    text, enc = read_text(path, encoding)
    if not text.strip():
        raise ValueError("arquivo vazio")
    delim = delimiter or sniff_delimiter(text[:SNIFF_BYTES])
    reader = csv.reader(text.splitlines(), delimiter=delim)
    header = next(reader)
    header = [h.strip() or f"coluna_{i + 1}" for i, h in enumerate(header)]
    rows, ragged, row_counter = [], [], Counter()
    for idx, row in enumerate(reader, start=2):
        if max_rows is not None and len(rows) >= max_rows:
            break
        if not any(c.strip() for c in row):
            continue
        if len(row) != len(header):
            ragged.append(idx)
            row = (row + [""] * len(header))[: len(header)]
        rows.append(row)
        row_counter[tuple(row)] += 1
    dup_header = [h for h, c in Counter(header).items() if c > 1]
    columns = [profile_column(h, [r[i] for r in rows], top) for i, h in enumerate(header)]
    return {
        "file": str(path), "encoding": enc, "delimiter": delim,
        "rows": len(rows), "columns": len(header),
        "duplicate_rows": sum(c - 1 for c in row_counter.values() if c > 1),
        "ragged_rows": {"count": len(ragged), "first_lines": ragged[:10]},
        "duplicate_headers": dup_header,
        "truncated": max_rows is not None and len(rows) >= max_rows,
        "profile": columns,
    }


def render_markdown(r: dict) -> str:
    out = [f"# Perfil de `{Path(r['file']).name}`", "",
           f"- Codificação: {r['encoding']} · Delimitador: `{repr(r['delimiter'])[1:-1]}`",
           f"- Linhas: {r['rows']}{' (amostra truncada)' if r['truncated'] else ''} · Colunas: {r['columns']}",
           f"- Linhas duplicadas: {r['duplicate_rows']} · Linhas com nº de campos divergente: "
           f"{r['ragged_rows']['count']}"
           + (f" (ex.: linhas {r['ragged_rows']['first_lines']})" if r['ragged_rows']['count'] else "")]
    if r["duplicate_headers"]:
        out.append(f"- Cabeçalhos duplicados: {r['duplicate_headers']}")
    out += ["", "| Coluna | Tipo | Nulos % | Distintos | Mín | Máx | Média | Mediana | Outliers |",
            "|---|---|---|---|---|---|---|---|---|"]
    for c in r["profile"]:
        mn = c.get("min", c.get("min_len", ""))
        mx = c.get("max", c.get("max_len", ""))
        out.append(f"| {c['name']} | {c['type']} | {c['null_pct']} | {c['distinct']} | {mn} | {mx} | "
                   f"{c.get('mean', '')} | {c.get('median', '')} | {c.get('outliers', '')} |")
    notes = []
    for c in r["profile"]:
        if c.get("invalid"):
            notes.append(f"- `{c['name']}`: {c['invalid']} valor(es) fora do tipo {c['type']}")
        if c.get("leading_trailing_spaces"):
            notes.append(f"- `{c['name']}`: {c['leading_trailing_spaces']} valor(es) com espaços nas bordas")
        if c.get("case_variants"):
            notes.append(f"- `{c['name']}`: {c['case_variants']} valor(es) com variação de maiúsculas/minúsculas")
        if c["null_pct"] >= 50:
            notes.append(f"- `{c['name']}`: {c['null_pct']}% nulos")
    if notes:
        out += ["", "## Alertas de qualidade", *notes]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Perfil de qualidade de CSV/TSV.")
    parser.add_argument("file")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--delimiter")
    parser.add_argument("--encoding")
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args(argv)
    try:
        result = profile(Path(args.file), args.delimiter, args.encoding, args.max_rows, args.top)
    except (OSError, ValueError, StopIteration, csv.Error) as exc:
        print(f"ERRO: não foi possível perfilar '{args.file}': {exc or 'sem cabeçalho'}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str) if args.json
          else render_markdown(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
