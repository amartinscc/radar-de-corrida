#!/usr/bin/env python3
"""Executa os cenários de evals/*.json no Claude Code e mede o ACIONAMENTO.

Para cada cenário: copia os arquivos de entrada para um diretório
temporário, roda `claude -p <query>` em modo não interativo com saída
stream-json e registra quais skills o modelo carregou (chamadas à
ferramenta Skill) e quais scripts executou. O cenário "aciona
corretamente" quando a skill esperada é carregada.

Com --judge, cada resposta também é avaliada item a item contra
expected_behavior por uma segunda chamada `claude -p` (LLM como juiz, sem
ferramentas), que recebe a resposta final e os comandos executados. O
veredito do juiz é uma estimativa automática: confira por amostragem.

Pré-requisitos: Claude Code instalado e autenticado, com a suíte disponível
(plugin instalado ou skills copiadas). Cada cenário consome tokens.

Uso:
  python3 tools/run_trigger_evals.py [--skill NOME ...] [--limit N]
         [--max-turns 12] [--timeout 600] [--out DIRETORIO] [--model ID]
         [--judge] [--judge-model ID]
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
# Ferramentas liberadas: leitura, execução dos scripts das skills e escrita
# restrita ao diretório temporário do cenário (regra relativa ao cwd).
ALLOWED_TOOLS = ("Skill Read Glob Grep Bash(python3:*) Bash(git:*) Bash(ls:*) Bash(cat:*) "
                 "Bash(head:*) Bash(mkdir:*) Edit(./**) Write(./**)")
JUDGE_PROMPT = """Você avalia a resposta de um assistente contra critérios de comportamento.
Para cada critério, decida se a evidência abaixo mostra que ele foi cumprido.
Use apenas a evidência fornecida; na dúvida, marque false.

<pedido>{query}</pedido>
<skills_carregadas>{skills}</skills_carregadas>
<texto_do_assistente_ao_longo_da_sessao>{transcript}</texto_do_assistente_ao_longo_da_sessao>
<comandos_executados>{commands}</comandos_executados>
<arquivos_criados_ou_alterados>{files}</arquivos_criados_ou_alterados>
<resposta_final>{final}</resposta_final>
<criterios>{criteria}</criterios>

Responda somente com JSON, sem texto extra, no formato:
[{{"criterio": 1, "cumprido": true, "justificativa": "<até 25 palavras>"}}]"""


def load_cases(skills: list[str] | None) -> list[dict]:
    cases = []
    for path in sorted(EVALS.glob("*.json")):
        for i, case in enumerate(json.loads(path.read_text(encoding="utf-8"))):
            if skills and path.stem not in skills:
                continue
            cases.append({**case, "id": f"{path.stem}#{i + 1}"})
    return cases


def parse_stream(stdout: str) -> dict:
    skills, commands, texts, final = [], [], [], ""
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "text" and block.get("text", "").strip():
                    texts.append(block["text"].strip())
                if block.get("type") != "tool_use":
                    continue
                inp = block.get("input", {})
                if block.get("name") == "Skill":
                    skills.append(str(inp.get("skill") or inp.get("command") or inp))
                elif block.get("name") == "Bash":
                    commands.append(str(inp.get("command", ""))[:1500])
        elif event.get("type") == "result":
            final = event.get("result") or ""
    return {"skills_loaded": skills, "bash_commands": commands, "final": final,
            "assistant_text": "\n\n".join(texts)}


def snapshot(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def changed_files(before: dict, root: Path) -> dict:
    """Arquivos novos/alterados no cenário (conteúdo truncado para o juiz)."""
    out = {}
    for rel, data in snapshot(root).items():
        if "__pycache__" not in rel and before.get(rel) != data:
            out[rel] = data.decode("utf-8", errors="replace")[:8000]
    return out


def judge(case: dict, result: dict, model: str | None, timeout: int) -> list[dict]:
    criteria = "\n".join(f"{i}. {c}" for i, c in enumerate(case["expected_behavior"], 1))
    files = "\n\n".join(f"--- {k}\n{v}" for k, v in result["changed_files"].items()) or "(nenhum)"
    prompt = JUDGE_PROMPT.format(query=case["query"], skills=", ".join(result["skills_loaded"]) or "(nenhuma)",
                                 transcript=result.get("assistant_text", "")[-20000:] or "(vazio)",
                                 commands="\n".join(result["bash_commands"]) or "(nenhum)",
                                 files=files[:40000], final=result["final"][:15000], criteria=criteria)
    cmd = ["claude", "-p", "--output-format", "json", "--max-turns", "1", "--tools", ""]
    if model:
        cmd += ["--model", model]
    try:
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout)
        text = json.loads(proc.stdout).get("result", "")
        start, end = text.find("["), text.rfind("]")
        verdicts = json.loads(text[start:end + 1])
        return [{"criterio": case["expected_behavior"][int(v["criterio"]) - 1],
                 "cumprido": bool(v["cumprido"]), "justificativa": v.get("justificativa", "")}
                for v in verdicts]
    except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError, KeyError, IndexError, TypeError) as exc:
        return [{"criterio": c, "cumprido": None, "justificativa": f"juiz falhou: {exc}"}
                for c in case["expected_behavior"]]


def run_case(case: dict, args) -> dict:
    with tempfile.TemporaryDirectory(prefix="ps-eval-") as tmp:
        for f in case["files"]:
            src = ROOT / f
            if src.is_dir():  # diretório: conteúdo copiado para a raiz do cenário
                shutil.copytree(src, tmp, dirs_exist_ok=True)
            else:
                shutil.copy(src, Path(tmp) / src.name)
        before = snapshot(Path(tmp))
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
        changed = changed_files(before, Path(tmp))
    parsed = parse_stream(out)
    parsed["changed_files"] = changed
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
    parser.add_argument("--judge", action="store_true", help="avalia expected_behavior com LLM como juiz")
    parser.add_argument("--judge-model")
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
        if args.judge:
            r["judgement"] = judge(case, r, args.judge_model, args.timeout)
        results.append(r)
        (out_dir / f"{r['id'].replace('#', '_')}.json").write_text(
            json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
        mark = "ACIONOU " if r["triggered"] else "NÃO ACIONOU"
        verdict = ""
        if args.judge:
            v = [j["cumprido"] for j in r["judgement"]]
            verdict = f" comportamento={sum(x is True for x in v)}/{len(v)}"
        print(f"[{mark}] {r['id']} ({r['seconds']}s){verdict} skills={r['skills_loaded']} "
              f"scripts={[c for c in r['bash_commands'] if 'scripts/' in c]}")
    ok = sum(r["triggered"] for r in results)
    print(f"\nAcionamento correto: {ok}/{len(results)}. Respostas completas em {out_dir}/")
    if args.judge:
        items = [j for r in results for j in r["judgement"]]
        passed = sum(j["cumprido"] is True for j in items)
        failed_judge = sum(j["cumprido"] is None for j in items)
        print(f"Comportamentos esperados cumpridos (juiz LLM): {passed}/{len(items)}"
              + (f" — {failed_judge} sem veredito" if failed_judge else ""))
        print("O juiz é uma estimativa automática; confira por amostragem.")
    else:
        print("Os itens de expected_behavior exigem avaliação humana ou --judge.")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
