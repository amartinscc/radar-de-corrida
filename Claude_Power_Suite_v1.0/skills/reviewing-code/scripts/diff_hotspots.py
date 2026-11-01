#!/usr/bin/env python3
"""Aponta onde concentrar a revisão de um diff unificado (git diff).

Não substitui a leitura do código: produz uma lista priorizada de sinais
objetivos para orientar a revisão humana ou do modelo.

Sinais detectados:
  ALTO   possível segredo em linha adicionada (chave AWS, chave privada,
         token GitHub/Slack, atribuição password/secret/api_key literal)
  ALTO   arquivo sensível alterado (auth, migrations, CI, Dockerfile, .env,
         lockfiles, infraestrutura)
  MÉDIO  código de produção alterado sem nenhum arquivo de teste no diff
  MÉDIO  arquivo de teste removido ou com mais linhas removidas que adicionadas
  MÉDIO  arquivo com muitas linhas alteradas (> LARGE_FILE_CHANGES)
  BAIXO  TODO/FIXME/HACK, print/console.log/debugger adicionados

Uso:
  git diff main...HEAD | python3 diff_hotspots.py -
  python3 diff_hotspots.py --git "main...HEAD"   (executa git diff no cwd)
  python3 diff_hotspots.py arquivo.diff [--json]

Código de saída: 0 sempre que a análise roda (os achados são informativos);
2 em erro de uso/leitura.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Acima de ~400 linhas alteradas em um arquivo a taxa de detecção de defeitos
# em revisão cai de forma acentuada (estudo SmartBear/Cisco); sinaliza para
# sugerir dividir a mudança.
LARGE_FILE_CHANGES = 400

SECRET_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "chave de acesso AWS"),
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"), "chave privada"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"), "token GitHub"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "token Slack"),
    (re.compile(r"sk-[A-Za-z0-9_-]{20,}"), "chave de API no formato sk-"),
    (re.compile(r"""(?i)\b(password|passwd|senha|secret|api[_-]?key|token)\b\s*[:=]\s*["'][^"'\s]{6,}["']"""),
     "credencial literal atribuída"),
]
SENSITIVE_PATH_PATTERNS = [
    (re.compile(r"(^|/)(auth|security|permissions?|acl|crypto)[^/]*(/|$)", re.I), "autenticação/segurança"),
    (re.compile(r"(^|/)(migrations?|alembic|flyway|liquibase)/", re.I), "migração de banco"),
    (re.compile(r"(^|/)\.github/workflows/|(^|/)\.gitlab-ci\.yml$|(^|/)Jenkinsfile$", re.I), "pipeline de CI"),
    (re.compile(r"(^|/)Dockerfile[^/]*$|(^|/)docker-compose[^/]*\.ya?ml$", re.I), "contêiner"),
    (re.compile(r"(^|/)\.env(\.|$)", re.I), "arquivo de ambiente"),
    (re.compile(r"(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|Pipfile\.lock|go\.sum|Cargo\.lock)$"),
     "lockfile de dependências"),
    (re.compile(r"\.(tf|tfvars)$|(^|/)(k8s|kubernetes|helm|terraform)/", re.I), "infraestrutura"),
]
TEST_PATH_RE = re.compile(r"(^|/)(tests?|__tests__|spec)(/|$)|(_test|\.test|\.spec|_spec)\.[a-z]+$|(^|/)test_[^/]+$", re.I)
CODE_EXT_RE = re.compile(r"\.(py|js|jsx|ts|tsx|go|java|kt|rb|php|cs|rs|c|cc|cpp|h|hpp|swift|scala)$", re.I)
TODO_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
DEBUG_RE = re.compile(r"\b(console\.log|debugger;|print\(|pdb\.set_trace|breakpoint\(\)|var_dump|System\.out\.println)")


@dataclass
class FileDiff:
    path: str
    added: list[tuple[int, str]] = field(default_factory=list)
    removed: int = 0
    deleted_file: bool = False
    new_file: bool = False


def parse_unified_diff(text: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    current: FileDiff | None = None
    new_line = 0
    for raw in text.splitlines():
        if raw.startswith("diff --git "):
            m = re.match(r"diff --git a/(.+?) b/(.+)$", raw)
            current = FileDiff(path=m.group(2) if m else raw[11:])
            files.append(current)
            continue
        if current is None:
            continue
        if raw.startswith("deleted file mode"):
            current.deleted_file = True
        elif raw.startswith("new file mode"):
            current.new_file = True
        elif raw.startswith("+++ "):
            target = raw[4:].strip()
            if target != "/dev/null":
                current.path = target[2:] if target.startswith("b/") else target
        elif raw.startswith("--- "):
            continue
        elif raw.startswith("@@"):
            m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", raw)
            new_line = int(m.group(1)) if m else 0
        elif raw.startswith("+"):
            current.added.append((new_line, raw[1:]))
            new_line += 1
        elif raw.startswith("-"):
            current.removed += 1
        elif raw.startswith(" "):
            new_line += 1
    return files


def analyze(files: list[FileDiff]) -> dict:
    findings: list[dict] = []

    def add(level: str, path: str, msg: str, line: int | None = None) -> None:
        findings.append({"level": level, "file": path, "line": line, "message": msg})

    test_files = [f for f in files if TEST_PATH_RE.search(f.path)]
    prod_code = [f for f in files if CODE_EXT_RE.search(f.path) and f not in test_files and not f.deleted_file]

    for f in files:
        for regex, label in SENSITIVE_PATH_PATTERNS:
            if regex.search(f.path):
                add("ALTO", f.path, f"arquivo sensível alterado ({label})")
                break
        for lineno, content in f.added:
            for regex, label in SECRET_PATTERNS:
                if regex.search(content):
                    add("ALTO", f.path, f"possível segredo: {label}", lineno)
            if TODO_RE.search(content):
                add("BAIXO", f.path, f"marcador adicionado: {content.strip()[:80]}", lineno)
            if CODE_EXT_RE.search(f.path) and f not in test_files and DEBUG_RE.search(content):
                add("BAIXO", f.path, f"instrução de depuração: {content.strip()[:80]}", lineno)
        changed = len(f.added) + f.removed
        if changed > LARGE_FILE_CHANGES:
            add("MÉDIO", f.path, f"{changed} linhas alteradas; considere dividir a mudança")
        if f in test_files and (f.deleted_file or f.removed > len(f.added)):
            add("MÉDIO", f.path, "teste removido ou reduzido "
                f"(+{len(f.added)}/-{f.removed}); confirme que a cobertura não caiu")

    if prod_code and not test_files:
        add("MÉDIO", "(diff)", f"{len(prod_code)} arquivo(s) de código alterado(s) sem nenhum teste no diff")

    order = {"ALTO": 0, "MÉDIO": 1, "BAIXO": 2}
    findings.sort(key=lambda x: (order[x["level"]], x["file"], x["line"] or 0))
    return {
        "summary": {
            "files": len(files),
            "added_lines": sum(len(f.added) for f in files),
            "removed_lines": sum(f.removed for f in files),
            "test_files": len(test_files),
            "by_level": {lvl: sum(1 for x in findings if x["level"] == lvl) for lvl in order},
        },
        "files": sorted(({"file": f.path, "added": len(f.added), "removed": f.removed}
                         for f in files), key=lambda x: -(x["added"] + x["removed"])),
        "findings": findings,
    }


def read_input(args) -> str:
    if args.git:
        proc = subprocess.run(["git", "diff", "--no-color", "--no-ext-diff", args.git],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            raise OSError(proc.stderr.strip() or "git diff falhou")
        return proc.stdout
    if args.file in (None, "-"):
        return sys.stdin.read()
    return Path(args.file).read_text(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hotspots de revisão em um diff.")
    parser.add_argument("file", nargs="?", help="arquivo .diff ou '-' para stdin")
    parser.add_argument("--git", metavar="INTERVALO", help="executa git diff INTERVALO")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        text = read_input(args)
    except OSError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2
    if not text.strip():
        print("Diff vazio: nada a revisar.")
        return 0
    result = analyze(parse_unified_diff(text))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    s = result["summary"]
    print(f"{s['files']} arquivos, +{s['added_lines']}/-{s['removed_lines']} linhas, "
          f"{s['test_files']} arquivo(s) de teste")
    print("Maiores alterações:")
    for f in result["files"][:5]:
        print(f"  {f['file']}  +{f['added']}/-{f['removed']}")
    if not result["findings"]:
        print("Nenhum sinal de risco detectado (ainda assim, leia o diff).")
    for x in result["findings"]:
        loc = f"{x['file']}:{x['line']}" if x["line"] else x["file"]
        print(f"[{x['level']}] {loc} — {x['message']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
