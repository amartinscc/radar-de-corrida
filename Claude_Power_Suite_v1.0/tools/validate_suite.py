#!/usr/bin/env python3
"""Validação completa da Power Suite (sem rede, só biblioteca padrão).

Verifica:
  1. Cada skill em skills/ com validate_skill.py em modo estrito.
  2. Unicidade dos nomes de skill.
  3. Independência: nenhum SKILL.md/referência aponta para arquivo de outra skill.
  4. Avaliações: evals/<skill>.json existe, tem >= 3 cenários no formato
     {skills, query, files, expected_behavior} e os arquivos citados existem.
  5. Manifesto do plugin e marketplace: JSON válido, campos obrigatórios,
     nome de plugin fora dos prefixos reservados e versão coerente com
     o CHANGELOG.
  6. Markdown da suíte inteira (README, docs, skills) com check_markdown.py.
  7. O orquestrador menciona todas as demais skills.

Uso: python3 tools/validate_suite.py [--json]
Código de saída: 0 tudo aprovado, 1 alguma falha.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
EVALS = ROOT / "evals"
MIN_EVALS = 3  # mínimo recomendado nas boas práticas oficiais
RESERVED_PLUGIN_PREFIXES = ("claude-", "anthropic-", "anthropics-", "cc-plugin-")
ORCHESTRATOR = "orchestrating-power-suite"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


vs = load_module(SKILLS / "authoring-agent-skills/scripts/validate_skill.py", "validate_skill")
cm = load_module(SKILLS / "writing-technical-docs/scripts/check_markdown.py", "check_markdown")


class Results:
    def __init__(self):
        self.checks: list[dict] = []

    def add(self, area: str, ok: bool, detail: str) -> None:
        self.checks.append({"area": area, "ok": ok, "detail": detail})

    @property
    def ok(self) -> bool:
        return all(c["ok"] for c in self.checks)


def skill_dirs() -> list[Path]:
    return sorted(p for p in SKILLS.iterdir() if p.is_dir())


def check_skills(res: Results) -> list[str]:
    names = []
    for d in skill_dirs():
        rep = vs.validate(d)
        problems = rep.errors + rep.warnings
        res.add("skill", rep.passed(strict=True),
                f"{d.name}: " + ("aprovada" if not problems else "; ".join(problems)))
        names.append(rep.info.get("name") or d.name)
    dupes = sorted({n for n in names if names.count(n) > 1})
    res.add("nomes únicos", not dupes, "ok" if not dupes else f"duplicados: {dupes}")
    return names


def check_independence(res: Results) -> None:
    link_re = re.compile(r"\]\(([^)\s]+)\)")
    for d in skill_dirs():
        bad = []
        for md in d.rglob("*.md"):
            for target in link_re.findall(md.read_text(encoding="utf-8")):
                if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                    continue
                resolved = (md.parent / target.split("#")[0]).resolve()
                try:
                    resolved.relative_to(d.resolve())
                except ValueError:
                    bad.append(f"{md.relative_to(ROOT)} -> {target}")
        res.add("independência", not bad, f"{d.name}: " + ("autocontida" if not bad else "; ".join(bad)))


def check_evals(res: Results, names: list[str]) -> None:
    for name in names:
        path = EVALS / f"{name}.json"
        if not path.is_file():
            res.add("avaliações", False, f"{name}: {path.relative_to(ROOT)} ausente")
            continue
        try:
            cases = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            res.add("avaliações", False, f"{name}: JSON inválido: {exc}")
            continue
        problems = []
        if not isinstance(cases, list) or len(cases) < MIN_EVALS:
            problems.append(f"menos de {MIN_EVALS} cenários")
            cases = cases if isinstance(cases, list) else []
        for i, c in enumerate(cases):
            if set(c) != {"skills", "query", "files", "expected_behavior"}:
                problems.append(f"cenário {i}: chaves {sorted(c)}")
                continue
            if c["skills"] != [name]:
                problems.append(f"cenário {i}: skills={c['skills']}")
            if not c["query"].strip() or not c["expected_behavior"]:
                problems.append(f"cenário {i}: query/expected_behavior vazio")
            for f in c["files"]:
                if not (ROOT / f).is_file():
                    problems.append(f"cenário {i}: arquivo {f} não existe")
        res.add("avaliações", not problems,
                f"{name}: {len(cases)} cenários" + ("" if not problems else " — " + "; ".join(problems)))


def check_manifests(res: Results) -> None:
    plugin_path = ROOT / ".claude-plugin/plugin.json"
    market_path = ROOT / ".claude-plugin/marketplace.json"
    try:
        plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
        market = json.loads(market_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        res.add("manifesto", False, f"leitura falhou: {exc}")
        return
    name = plugin.get("name", "")
    problems = []
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
        problems.append(f"plugin.name '{name}' não é kebab-case")
    if name.lower().startswith(RESERVED_PLUGIN_PREFIXES) or name.lower() in {"claude", "anthropic", "claude-code"}:
        problems.append(f"plugin.name '{name}' usa nome reservado")
    for key in ("version", "description", "author"):
        if key not in plugin:
            problems.append(f"plugin.json sem '{key}'")
    for key in ("name", "owner", "plugins"):
        if key not in market:
            problems.append(f"marketplace.json sem '{key}'")
    entries = market.get("plugins", [])
    if not any(e.get("name") == name and str(e.get("source", "")).startswith(".") for e in entries):
        problems.append("marketplace.json não lista o plugin com source relativo")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8") if (ROOT / "CHANGELOG.md").exists() else ""
    if f"[{plugin.get('version')}]" not in changelog:
        problems.append(f"CHANGELOG.md não tem entrada para a versão {plugin.get('version')}")
    res.add("manifesto", not problems, "ok" if not problems else "; ".join(problems))


def check_markdown(res: Results) -> None:
    files = cm.collect([str(ROOT / "README.md"), str(ROOT / "CHANGELOG.md"),
                        str(ROOT / "docs"), str(SKILLS)])
    cache: dict = {}
    errors, warnings = [], []
    for f in files:
        e, w = cm.check_file(f, cache)
        errors += e
        warnings += w
    res.add("markdown", not errors and not warnings,
            f"{len(files)} arquivos" + ("" if not (errors or warnings)
                                        else " — " + "; ".join(errors + warnings)))


def check_orchestrator(res: Results, names: list[str]) -> None:
    text = (SKILLS / ORCHESTRATOR / "SKILL.md").read_text(encoding="utf-8")
    missing = [n for n in names if n != ORCHESTRATOR and f"`{n}`" not in text]
    res.add("orquestrador", not missing, "cobre todas as skills" if not missing else f"faltam: {missing}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Valida a Power Suite inteira.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    res = Results()
    names = check_skills(res)
    check_independence(res)
    check_evals(res, names)
    check_manifests(res)
    check_markdown(res)
    check_orchestrator(res, names)
    if args.json:
        print(json.dumps({"passed": res.ok, "checks": res.checks}, ensure_ascii=False, indent=2))
    else:
        for c in res.checks:
            print(f"[{'OK ' if c['ok'] else 'FALHA'}] {c['area']}: {c['detail']}")
        total, failed = len(res.checks), sum(not c["ok"] for c in res.checks)
        print(f"\n{total - failed}/{total} verificações aprovadas")
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
