#!/usr/bin/env python3
"""Verificações estruturais de documentação Markdown.

ERRO   link relativo para arquivo inexistente
ERRO   âncora (#secao) inexistente no arquivo de destino
ERRO   bloco de código (```) não fechado
AVISO  mais de um título H1 / nenhum H1
AVISO  salto de nível de título (ex.: ## seguido de ####)
AVISO  link com texto vazio ou genérico ("aqui", "clique aqui", "here", "link")
AVISO  bloco de código sem linguagem declarada
AVISO  marcadores pendentes (TODO, FIXME, TBD, XXX) fora de blocos de código

Âncoras seguem a regra de slug do GitHub: minúsculas, remove pontuação
(exceto hífens e sublinhados), espaços viram hífens, duplicatas ganham -1, -2.

Uso:
  python3 check_markdown.py ARQUIVO_OU_DIRETORIO [...] [--json] [--strict]
Links http(s) não são verificados (o script não acessa a rede).
Código de saída: 0 aprovado, 1 com erros (ou avisos com --strict), 2 uso.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})(.*)$")
PENDING_RE = re.compile(r"\b(TODO|FIXME|TBD|XXX)\b")
GENERIC_LINK_TEXT = {"aqui", "clique aqui", "here", "click here", "link", "este link", "this link", "veja"}


def github_slug(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.strip().lower()
    out = []
    for ch in text:
        cat = unicodedata.category(ch)
        if ch in "-_" or ch.isalnum():
            out.append(ch)
        elif ch == " ":
            out.append("-")
        elif cat.startswith("M"):
            out.append(ch)
    return "".join(out)


def parse(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    headings, links, fences_no_lang, pending = [], [], [], []
    in_fence, fence_start, fence_marker = False, 0, ""
    for lineno, line in enumerate(lines, 1):
        fm = FENCE_RE.match(line)
        if fm:
            if not in_fence:
                in_fence, fence_start, fence_marker = True, lineno, fm.group(1)
                if not fm.group(2).strip():
                    fences_no_lang.append(lineno)
            elif (fm.group(1)[0] == fence_marker[0] and len(fm.group(1)) >= len(fence_marker)
                  and not fm.group(2).strip()):
                in_fence = False  # fechamento: mesmo caractere, comprimento >= abertura
            continue
        if in_fence:
            continue
        hm = HEADING_RE.match(line)
        if hm:
            headings.append((lineno, len(hm.group(1)), hm.group(2)))
        stripped = re.sub(r"`[^`]*`", "", line)
        for m in LINK_RE.finditer(stripped):
            links.append((lineno, m.group(1) == "!", m.group(2), m.group(3)))
        if PENDING_RE.search(stripped):
            pending.append((lineno, stripped.strip()[:80]))
    anchors, seen = set(), {}
    for _, _, text in headings:
        slug = github_slug(text)
        n = seen.get(slug, 0)
        anchors.add(slug if n == 0 else f"{slug}-{n}")
        seen[slug] = n + 1
    return {"headings": headings, "links": links, "anchors": anchors,
            "unclosed_fence": fence_start if in_fence else None,
            "fences_no_lang": fences_no_lang, "pending": pending}


def check_file(path: Path, cache: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    info = cache.setdefault(path.resolve(), parse(path))
    name = path.as_posix()

    if info["unclosed_fence"]:
        errors.append(f"{name}:{info['unclosed_fence']}: bloco de código não fechado")
    h1 = [h for h in info["headings"] if h[1] == 1]
    if len(h1) > 1:
        warnings.append(f"{name}: {len(h1)} títulos H1 (linhas {', '.join(str(h[0]) for h in h1)})")
    if not h1:
        warnings.append(f"{name}: nenhum título H1")
    prev = 0
    for lineno, level, text in info["headings"]:
        if prev and level > prev + 1:
            warnings.append(f"{name}:{lineno}: salto de H{prev} para H{level} em '{text[:50]}'")
        prev = level
    for lineno in info["fences_no_lang"]:
        warnings.append(f"{name}:{lineno}: bloco de código sem linguagem")
    for lineno, text in info["pending"]:
        warnings.append(f"{name}:{lineno}: pendência: {text}")

    for lineno, is_image, text, target in info["links"]:
        if not is_image and (not text.strip() or text.strip().lower() in GENERIC_LINK_TEXT):
            warnings.append(f"{name}:{lineno}: texto de link vazio/genérico '{text}'")
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
            continue  # http, https, mailto: fora do escopo (sem rede)
        file_part, _, anchor = target.partition("#")
        dest = path if not file_part else (path.parent / file_part)
        if file_part and not dest.exists():
            errors.append(f"{name}:{lineno}: link para arquivo inexistente '{target}'")
            continue
        if anchor and dest.is_file() and dest.suffix.lower() == ".md":
            dest_info = cache.setdefault(dest.resolve(), parse(dest))
            if anchor.lower() not in dest_info["anchors"]:
                errors.append(f"{name}:{lineno}: âncora '#{anchor}' não existe em {dest.name}")
    return errors, warnings


def collect(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for p in map(Path, paths):
        if p.is_dir():
            files += sorted(x for x in p.rglob("*.md") if ".git" not in x.parts and "node_modules" not in x.parts)
        elif p.is_file():
            files.append(p)
        else:
            raise FileNotFoundError(f"'{p}' não existe")
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verifica estrutura de arquivos Markdown.")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="avisos também reprovam")
    args = parser.parse_args(argv)
    try:
        files = collect(args.paths)
    except FileNotFoundError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2
    cache: dict = {}
    all_errors, all_warnings = [], []
    for f in files:
        e, w = check_file(f, cache)
        all_errors += e
        all_warnings += w
    failed = bool(all_errors) or (args.strict and bool(all_warnings))
    if args.json:
        print(json.dumps({"files": len(files), "errors": all_errors, "warnings": all_warnings,
                          "passed": not failed}, ensure_ascii=False, indent=2))
    else:
        for e in all_errors:
            print(f"ERRO:  {e}")
        for w in all_warnings:
            print(f"AVISO: {w}")
        print(f"{len(files)} arquivo(s): {len(all_errors)} erro(s), {len(all_warnings)} aviso(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
