#!/usr/bin/env python3
"""Gera um ZIP por skill (para upload no claude.ai ou via API) em dist/.

Cada ZIP contém a pasta da skill na raiz (ex.: reviewing-code/SKILL.md).
Antes de empacotar, valida cada skill em modo estrito e aborta se alguma
falhar. Arquivos __pycache__, *.pyc e .DS_Store são excluídos.

Uso: python3 tools/package_skills.py [--out dist] [--skill NOME ...]
Código de saída: 0 sucesso, 1 validação falhou, 2 skill inexistente.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
EXCLUDE_NAMES = {"__pycache__", ".DS_Store"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}

_spec = importlib.util.spec_from_file_location(
    "validate_skill", SKILLS / "authoring-agent-skills/scripts/validate_skill.py")
vs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vs)  # type: ignore[union-attr]


def included(path: Path) -> bool:
    return not (set(path.parts) & EXCLUDE_NAMES) and path.suffix not in EXCLUDE_SUFFIXES


def package(skill_dir: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{skill_dir.name}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(skill_dir.rglob("*")):
            if f.is_file() and included(f.relative_to(skill_dir)):
                zf.write(f, (Path(skill_dir.name) / f.relative_to(skill_dir)).as_posix())
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Empacota skills em ZIP.")
    parser.add_argument("--out", default=str(ROOT / "dist"))
    parser.add_argument("--skill", action="append", help="empacota só esta skill (repetível)")
    args = parser.parse_args(argv)

    dirs = sorted(p for p in SKILLS.iterdir() if p.is_dir())
    if args.skill:
        wanted = set(args.skill)
        missing = wanted - {d.name for d in dirs}
        if missing:
            print(f"ERRO: skill(s) inexistente(s): {sorted(missing)}", file=sys.stderr)
            return 2
        dirs = [d for d in dirs if d.name in wanted]

    failed = [d.name for d in dirs if not vs.validate(d).passed(strict=True)]
    if failed:
        print(f"ERRO: validação falhou para {failed}; rode validate_skill.py --strict", file=sys.stderr)
        return 1
    for d in dirs:
        path = package(d, Path(args.out))
        with zipfile.ZipFile(path) as zf:
            n = len(zf.namelist())
        print(f"{path}  ({n} arquivos, {path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
