#!/usr/bin/env python3
"""Análise estática (heurística) de um prompt em texto puro.

O script NÃO avalia a qualidade das respostas do modelo; ele apenas detecta
sinais objetivos no texto que costumam causar respostas ruins:

  ERRO  tags XML abertas/fechadas de forma desbalanceada
  ERRO  marcadores não preenchidos: {{variavel}}, [INSERIR ...], TODO, XXX, TBD
  AVISO nenhum formato de saída declarado
  AVISO nenhum exemplo (quando o prompt passa de 150 palavras)
  AVISO excesso de ÊNFASE EM MAIÚSCULAS (MUST/NEVER/SEMPRE/NUNCA...)
  AVISO muitas instruções só negativas ("não faça X") sem alternativa positiva
  AVISO termos vagos ("etc", "adequado", "alguns", "as needed"...)

Uso:
  python3 lint_prompt.py ARQUIVO [--json]
  cat prompt.txt | python3 lint_prompt.py - [--json]

Código de saída: 0 sem erros, 1 com erros, 2 erro de uso.
A contagem de tokens é uma ESTIMATIVA (caracteres/4), não a tokenização real.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Acima de ~150 palavras um prompt geralmente descreve uma tarefa com formato
# não trivial, onde exemplos melhoram a aderência ao formato.
EXAMPLES_WORD_THRESHOLD = 150
# A partir de 3 palavras de ênfase em maiúsculas o padrão deixa de ser um
# destaque pontual e vira tom geral; modelos recentes seguem instruções
# literais com precisão e tendem a sobre-aplicar regras gritadas.
SHOUT_THRESHOLD = 3
# Se mais da metade das frases imperativas for proibição, o modelo recebe pouco
# sinal sobre o que FAZER.
NEGATIVE_RATIO_THRESHOLD = 0.5
NEGATIVE_MIN_COUNT = 4

TAG_RE = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9_-]*)(\s[^<>]*)?(/?)>")
PLACEHOLDER_RES = [
    (re.compile(r"\{\{\s*[\w.-]+\s*\}\}"), "variável de template não preenchida"),
    (re.compile(r"\[(INSERIR|INSERT|PREENCHER|FILL|SEU|YOUR)[^\]]*\]", re.IGNORECASE),
     "marcador de preenchimento"),
    (re.compile(r"\b(TODO|FIXME|XXX|TBD)\b"), "pendência"),
]
OUTPUT_FORMAT_RE = re.compile(
    r"(formato de sa[ií]da|output format|responda (em|no formato|com)|respond (in|with)|"
    r"\bjson\b|\byaml\b|\bcsv\b|markdown|tabela|\btable\b|schema|<output|"
    r"retorne (apenas|somente|um|uma)|return (only|a|an)\b)",
    re.IGNORECASE,
)
EXAMPLE_RE = re.compile(r"(<example|exemplo|example|por exemplo|e\.g\.|ex\.:)", re.IGNORECASE)
SHOUT_RE = re.compile(
    r"\b(MUST|NEVER|ALWAYS|IMPORTANT|CRITICAL|DO NOT|DON'T|NUNCA|SEMPRE|"
    r"IMPORTANTE|CR[IÍ]TICO|OBRIGAT[OÓ]RIO|N[AÃ]O)\b"
)
NEGATIVE_RE = re.compile(r"^\s*[-*\d.)]*\s*(n[aã]o |nunca |jamais |evite |don't |do not |never |avoid )",
                         re.IGNORECASE)
IMPERATIVE_RE = re.compile(r"^\s*[-*\d.)]+\s+\S")
VAGUE_TERMS = [
    "etc", "adequado", "adequada", "apropriado", "apropriada", "alguns", "algumas",
    "coisas", "bom", "boa", "melhor possível", "se necessário", "conforme necessário",
    "appropriate", "properly", "as needed", "some", "stuff", "things", "good", "etc.",
]
VAGUE_RE = re.compile(r"\b(" + "|".join(re.escape(t) for t in VAGUE_TERMS) + r")\b", re.IGNORECASE)
SELF_CLOSING = {"br", "hr", "img"}


FENCE_LINE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})(.*)$")


def iter_unfenced(text: str):
    """Gera (nº da linha, linha) fora de blocos de código cercados.

    Segue a regra do CommonMark: o bloco fecha com o mesmo caractere e
    comprimento >= ao da abertura, sem texto após a cerca.
    """
    marker = None
    for lineno, line in enumerate(text.splitlines(), 1):
        m = FENCE_LINE_RE.match(line)
        if m:
            fence, info = m.groups()
            if marker is None:
                marker = fence
                continue
            if fence[0] == marker[0] and len(fence) >= len(marker) and not info.strip():
                marker = None
                continue
        if marker is None:
            yield lineno, line


def check_tags(text: str) -> list[str]:
    errors: list[str] = []
    stack: list[tuple[str, int]] = []
    for lineno, line in iter_unfenced(text):
        for m in TAG_RE.finditer(line):
            closing, name, _, self_close = m.groups()
            name_l = name.lower()
            if self_close or name_l in SELF_CLOSING:
                continue
            if not closing:
                stack.append((name_l, lineno))
            elif stack and stack[-1][0] == name_l:
                stack.pop()
            elif any(n == name_l for n, _ in stack):
                while stack and stack[-1][0] != name_l:
                    open_name, open_line = stack.pop()
                    errors.append(f"linha {open_line}: <{open_name}> não foi fechada antes de </{name}>")
                stack.pop()
            else:
                errors.append(f"linha {lineno}: </{name}> fecha uma tag que não foi aberta")
    errors += [f"linha {ln}: <{n}> aberta e nunca fechada" for n, ln in stack]
    return errors


def lint(text: str) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    words = re.findall(r"\w+", text)
    lines = text.splitlines()

    errors += check_tags(text)
    for regex, label in PLACEHOLDER_RES:
        for lineno, line in enumerate(lines, 1):
            for m in regex.finditer(line):
                errors.append(f"linha {lineno}: {label}: '{m.group(0)}'")

    if not OUTPUT_FORMAT_RE.search(text):
        warnings.append("nenhum formato de saída declarado (ex.: 'Responda em JSON com as chaves...')")
    if len(words) > EXAMPLES_WORD_THRESHOLD and not EXAMPLE_RE.search(text):
        warnings.append(f"prompt com {len(words)} palavras e nenhum exemplo; "
                        "1–3 exemplos em <example> aumentam a consistência")

    shouts = SHOUT_RE.findall(text)
    if len(shouts) >= SHOUT_THRESHOLD:
        common = ", ".join(f"{w}×{c}" for w, c in Counter(shouts).most_common(4))
        warnings.append(f"{len(shouts)} palavras de ênfase em maiúsculas ({common}); "
                        "prefira explicar o PORQUÊ da regra em tom normal")

    imperative = [l for l in lines if IMPERATIVE_RE.match(l)]
    negatives = [l for l in lines if NEGATIVE_RE.match(l)]
    if len(negatives) >= NEGATIVE_MIN_COUNT and imperative and \
            len(negatives) / max(len(imperative), 1) > NEGATIVE_RATIO_THRESHOLD:
        warnings.append(f"{len(negatives)} de {len(imperative)} instruções em lista são proibições; "
                        "diga o que fazer em vez do que não fazer")

    vague = Counter(m.group(0).lower() for m in VAGUE_RE.finditer(text))
    if vague:
        listed = ", ".join(f"'{t}'×{c}" for t, c in vague.most_common(6))
        warnings.append(f"termos vagos: {listed}; substitua por critérios verificáveis")

    return {
        "stats": {
            "characters": len(text),
            "words": len(words),
            "lines": len(lines),
            "estimated_tokens": round(len(text) / 4),
            "xml_tags": sorted({m.group(2).lower() for m in TAG_RE.finditer(text) if not m.group(1)}),
        },
        "errors": errors,
        "warnings": warnings,
        "passed": not errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint heurístico de prompts.")
    parser.add_argument("file", help="arquivo do prompt ou '-' para stdin")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        text = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"ERRO: não foi possível ler '{args.file}': {exc}", file=sys.stderr)
        return 2
    if not text.strip():
        print("ERRO: prompt vazio", file=sys.stderr)
        return 2

    result = lint(text)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        s = result["stats"]
        print(f"{s['words']} palavras, {s['lines']} linhas, ~{s['estimated_tokens']} tokens (estimativa)")
        if s["xml_tags"]:
            print("tags XML: " + ", ".join(s["xml_tags"]))
        for e in result["errors"]:
            print(f"ERRO:  {e}")
        for w in result["warnings"]:
            print(f"AVISO: {w}")
        print("RESULTADO: " + ("sem erros" if result["passed"] else "com erros"))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
