#!/usr/bin/env python3
"""Executa os cenários de evals/*.json no Claude Code e mede o ACIONAMENTO.

Para cada cenário: copia os arquivos de entrada para um diretório
temporário, roda `claude -p <query>` em modo não interativo com saída
stream-json e registra quais skills o modelo carregou (chamadas à
ferramenta Skill) e quais scripts executou. O cenário "aciona
corretamente" quando a skill esperada é carregada.

O que este script NÃO faz: julgar os itens de expected_behavior. Eles
continuam exigindo leitura humana (ou um juiz próprio) da resposta salva
em --out.

Pré-requisitos: Claude Code instalado e autenticado, com a suíte disponível
(plugin instalado ou skills copiadas). Cada cenário consome tokens.

Uso:
  python3 tools/run_trigger_evals.py [--skill NOME ...] [--limit N]
         [--max-turns 12] [--timeout 600] [--out DIRETORIO] [--model ID]
Código de saída: 0 se todos acionaram a skill esperada, 1 caso contrário,
2 se o executável `claude` não existir.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVALS = ROOT / "evals"
# Ferramentas liberadas: leitura e execução dos scripts das skills. Sem
# Write/Edit para que o cenário não altere nada além do diretório temporário.
ALLOWED_TOOLS = "Skill Read Glob Grep Bash(python3:*) Bash(git:*) Bash(ls:*) Bash(cat:*) Bash(head:*)"


def load_cases(skills: list[str] | None) -> list[dict]:
    cases = []
    for path in sorted(EVALS.glob("*.json")):
        for i, case in enumerate(json.loads(path.read_text(encoding="utf-8"))):
            if skills and path.stem not in skills:
                continue
            cases.append({**case, "id": f"{path.stem}#{i + 1}"})
    return cases


def parse_stream(stdout: str) -> dict:
    skills, commands, final = [], [], ""
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") != "tool_use":
                    continue
                inp = block.get("input", {})
                if block.get("name") == "Skill":
                    skills.append(str(inp.get("skill") or inp.get("command") or inp))
                elif block.get("name") == "Bash":
                    commands.append(str(inp.get("command", ""))[:200])
        elif event.get("type") == "result":
            final = event.get("result") or ""
    return {"skills_loaded": skills, "bash_commands": commands, "final": final}


def run_case(case: dict, args) -> dict:
    with tempfile.TemporaryDirectory(prefix="ps-eval-") as tmp:
        for f in case["files"]:
            src = ROOT / f
            shutil.copy(src, Path(tmp) / src.name)
        cmd = ["claude", "-p", case["query"], "--output-format", "stream-json", "--verbose",
               "--max-turns", str(args.max_turns), "--allowedTools", ALLOWED_TOOLS]
        if args.model:
            cmd += ["--model", args.model]
        start = time.time()
        try:
            proc = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, timeout=args.timeout)
            out, rc = proc.stdout, proc.returncode
        except subprocess.TimeoutExpired as exc:
            out, rc = (exc.stdout or b"").decode() if isinstance(exc.stdout, bytes) else (exc.stdout or ""), -1
    parsed = parse_stream(out)
    # `skills` lista as skills que DEVEM ser acionadas; basta uma delas carregar.
    expected = case["skills"]
    triggered = any(s == e or s.endswith(":" + e) for s in parsed["skills_loaded"] for e in expected)
    return {"id": case["id"], "expected": expected, "triggered": triggered, "exit_code": rc,
            "seconds": round(time.time() - start, 1), **parsed,
            "expected_behavior": case["expected_behavior"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mede acionamento das skills com o Claude Code.")
    parser.add_argument("--skill", action="append")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--max-turns", type=int, default=12)
    parser.add_argument("--timeout", type=int, default=600, help="segundos por cenário")
    parser.add_argument("--out", default=str(ROOT / "dist" / "eval-results"))
    parser.add_argument("--model")
    args = parser.parse_args(argv)
    if shutil.which("claude") is None:
        print("ERRO: executável 'claude' não encontrado no PATH", file=sys.stderr)
        return 2
    cases = load_cases(args.skill)[: args.limit]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for case in cases:
        r = run_case(case, args)
        results.append(r)
        (out_dir / f"{r['id'].replace('#', '_')}.json").write_text(
            json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
        mark = "ACIONOU " if r["triggered"] else "NÃO ACIONOU"
        print(f"[{mark}] {r['id']} ({r['seconds']}s) skills={r['skills_loaded']} "
              f"scripts={[c for c in r['bash_commands'] if 'scripts/' in c]}")
    ok = sum(r["triggered"] for r in results)
    print(f"\nAcionamento correto: {ok}/{len(results)}. Respostas completas em {out_dir}/")
    print("Os itens de expected_behavior exigem avaliação humana das respostas salvas.")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
