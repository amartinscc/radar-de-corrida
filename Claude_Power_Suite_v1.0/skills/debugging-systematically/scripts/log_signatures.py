#!/usr/bin/env python3
"""Agrupa linhas de log por "assinatura" para revelar os erros dominantes.

A assinatura é a linha com partes variáveis normalizadas: timestamps, UUIDs,
hashes hexadecimais, IPs, números, strings entre aspas e caminhos de arquivo
temporário. Assim, 10.000 ocorrências de "timeout ao chamar pedido 8812"
viram uma única assinatura com contagem, primeira e última linha.

Uso:
  python3 log_signatures.py app.log [outro.log ...] [--top 20]
                            [--level ERROR] [--json]
  cat app.log | python3 log_signatures.py -

Também extrai tipos de exceção (Python "XError:", Java "x.y.ZException")
e conta tracebacks.
Código de saída: 0 sucesso, 2 erro de leitura.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

LEVELS = ["TRACE", "DEBUG", "INFO", "NOTICE", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL", "PANIC"]
LEVEL_RANK = {"TRACE": 0, "DEBUG": 1, "INFO": 2, "NOTICE": 2, "WARN": 3, "WARNING": 3,
              "ERROR": 4, "CRITICAL": 5, "FATAL": 5, "PANIC": 5}
LEVEL_RE = re.compile(r"\b(" + "|".join(LEVELS) + r")\b", re.IGNORECASE)

# Ordem importa: padrões mais específicos primeiro.
NORMALIZERS = [
    (re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?"), "<TS>"),
    (re.compile(r"\b\d{2}/\d{2}/\d{4}[ T]\d{2}:\d{2}:\d{2}\b"), "<TS>"),
    (re.compile(r"\b\d{2}:\d{2}:\d{2}(?:[.,]\d+)?\b"), "<TIME>"),
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I), "<UUID>"),
    (re.compile(r"\b0x[0-9a-f]+\b", re.I), "<HEX>"),
    (re.compile(r"\b[0-9a-f]{12,}\b", re.I), "<HEX>"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\b"), "<IP>"),
    (re.compile(r"\"[^\"]*\"|'[^']*'"), "<STR>"),
    (re.compile(r"(?:/tmp|/var/tmp)/\S+"), "<TMP>"),
    (re.compile(r"\b\d+(?:\.\d+)?(?:ms|s|kb|mb|gb|b)?\b", re.I), "<N>"),
]
EXCEPTION_RE = re.compile(r"\b((?:[a-z_][\w]*\.)*[A-Z]\w*(?:Error|Exception|Exit|Interrupt|Fault|Panic))\b")
TRACEBACK_RE = re.compile(r"^Traceback \(most recent call last\):|^\s+at [\w$.<>]+\(.*\)$|^goroutine \d+ \[")


def normalize(line: str) -> str:
    sig = line.strip()
    for regex, repl in NORMALIZERS:
        sig = regex.sub(repl, sig)
    return re.sub(r"\s+", " ", sig)[:300]


def detect_level(line: str) -> str | None:
    m = LEVEL_RE.search(line)
    if not m:
        return None
    lvl = m.group(1).upper()
    return "WARN" if lvl == "WARNING" else lvl


def analyze(sources: list[tuple[str, list[str]]], min_level: str | None) -> dict:
    groups: "OrderedDict[str, dict]" = OrderedDict()
    exceptions: Counter = Counter()
    levels: Counter = Counter()
    tracebacks = 0
    total = 0
    min_rank = LEVEL_RANK.get(min_level.upper(), 0) if min_level else None
    for name, lines in sources:
        for lineno, line in enumerate(lines, 1):
            if not line.strip():
                continue
            total += 1
            if TRACEBACK_RE.search(line):
                if line.startswith("Traceback") or line.startswith("goroutine"):
                    tracebacks += 1
                continue  # frames de stack não viram assinatura própria
            for exc in EXCEPTION_RE.findall(line):
                exceptions[exc] += 1
            level = detect_level(line)
            levels[level or "SEM_NIVEL"] += 1
            if min_rank is not None and (level is None or LEVEL_RANK.get(level, 0) < min_rank):
                continue
            sig = normalize(line)
            g = groups.get(sig)
            loc = f"{name}:{lineno}"
            if g is None:
                groups[sig] = {"signature": sig, "count": 1, "level": level,
                               "first": loc, "last": loc, "example": line.strip()[:300]}
            else:
                g["count"] += 1
                g["last"] = loc
    ranked = sorted(groups.values(), key=lambda g: (-g["count"], g["first"]))
    return {
        "total_lines": total,
        "levels": dict(levels.most_common()),
        "tracebacks": tracebacks,
        "exceptions": dict(exceptions.most_common(20)),
        "unique_signatures": len(groups),
        "signatures": ranked,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agrupa logs por assinatura.")
    parser.add_argument("files", nargs="+", help="arquivos de log ou '-' para stdin")
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--level", help="nível mínimo (ex.: WARN, ERROR)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.level and args.level.upper() not in LEVEL_RANK:
        print(f"ERRO: nível desconhecido '{args.level}'", file=sys.stderr)
        return 2
    sources = []
    for f in args.files:
        try:
            text = sys.stdin.read() if f == "-" else Path(f).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"ERRO: {exc}", file=sys.stderr)
            return 2
        sources.append(("stdin" if f == "-" else f, text.splitlines()))

    result = analyze(sources, args.level)
    result["signatures"] = result["signatures"][: args.top]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    print(f"{result['total_lines']} linhas, {result['unique_signatures']} assinaturas únicas, "
          f"{result['tracebacks']} stack traces")
    print("Níveis: " + ", ".join(f"{k}={v}" for k, v in result["levels"].items()))
    if result["exceptions"]:
        print("Exceções: " + ", ".join(f"{k}×{v}" for k, v in result["exceptions"].items()))
    print(f"\nTop {len(result['signatures'])} assinaturas:")
    for g in result["signatures"]:
        print(f"{g['count']:>7}  [{g['level'] or '-'}] {g['signature']}")
        print(f"         primeira {g['first']}  última {g['last']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
