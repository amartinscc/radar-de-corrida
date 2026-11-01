"""Testes dos scripts das skills e das ferramentas da suíte.

Executar a partir da raiz do projeto:
    python3 -m unittest discover -s tests -v
Somente biblioteca padrão; não acessa a rede; escreve apenas em diretórios
temporários.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
FILES = ROOT / "evals" / "files"


def load(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


sys.path.insert(0, str(SKILLS / "authoring-agent-skills/scripts"))
vs = load("skills/authoring-agent-skills/scripts/validate_skill.py", "validate_skill")
scaffold = load("skills/authoring-agent-skills/scripts/scaffold_skill.py", "scaffold_skill")
lint = load("skills/engineering-prompts/scripts/lint_prompt.py", "lint_prompt")
adr = load("skills/architecting-software/scripts/new_adr.py", "new_adr")
hot = load("skills/reviewing-code/scripts/diff_hotspots.py", "diff_hotspots")
logs = load("skills/debugging-systematically/scripts/log_signatures.py", "log_signatures")
md = load("skills/writing-technical-docs/scripts/check_markdown.py", "check_markdown")
prof = load("skills/analyzing-tabular-data/scripts/profile_csv.py", "profile_csv")
pkg = load("tools/package_skills.py", "package_skills")
suite = load("tools/validate_suite.py", "validate_suite")
runner = load("tools/run_trigger_evals.py", "run_trigger_evals")


def quiet(fn, *args, **kwargs):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = fn(*args, **kwargs)
    return rc, out.getvalue(), err.getvalue()


class TempDirTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="power-suite-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def make_skill(self, dirname: str, frontmatter: str, body: str = "# T\n\nCorpo.\n") -> Path:
        d = self.tmp / dirname
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")
        return d


# ------------------------------------------------------------ validate_skill
class ValidateSkillTests(TempDirTest):
    GOOD = "name: good-skill\ndescription: Faz X com Y. Use quando o usuário pedir Z."

    def test_all_suite_skills_pass_strict(self):
        for d in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
            rep = vs.validate(d)
            self.assertTrue(rep.passed(strict=True), f"{d.name}: {rep.errors + rep.warnings}")

    def test_valid_minimal_skill(self):
        rep = vs.validate(self.make_skill("good-skill", self.GOOD))
        self.assertEqual(rep.errors, [])
        self.assertEqual(rep.warnings, [])

    def test_missing_skill_md_and_wrong_case(self):
        d = self.tmp / "x"
        d.mkdir()
        (d / "skill.md").write_text("---\nname: x\n---\n")
        rep = vs.validate(d)
        self.assertTrue(any("exatamente SKILL.md" in e for e in rep.errors))

    def test_no_frontmatter(self):
        d = self.tmp / "nofm"
        d.mkdir()
        (d / "SKILL.md").write_text("# Sem frontmatter\n")
        self.assertTrue(any("primeira linha" in e for e in vs.validate(d).errors))

    def test_name_rules(self):
        cases = {
            "Bad_Name": "apenas letras minúsculas",
            "claude-helper": "palavra reservada 'claude'",
            "my-anthropic-tool": "palavra reservada 'anthropic'",
            "a" * 65: "máximo 64",
        }
        for name, expected in cases.items():
            d = self.make_skill(f"d{abs(hash(name))}", f"name: {name}\ndescription: Faz X. Use quando Y.")
            errors = vs.validate(d).errors
            self.assertTrue(any(expected in e for e in errors), f"{name}: {errors}")

    def test_name_mismatch_and_hyphens_are_warnings(self):
        rep = vs.validate(self.make_skill("other-dir", "name: bad--name-\ndescription: Faz X. Use quando Y."))
        self.assertEqual(rep.errors, [])
        self.assertEqual(len(rep.warnings), 2)
        self.assertFalse(rep.passed(strict=True))
        self.assertTrue(rep.passed(strict=False))

    def test_description_rules(self):
        long_desc = "Faz X. Use quando Y. " + "a" * 1100
        cases = {
            'description: ""': "ausente ou vazio",
            f"description: {long_desc}": "máximo 1024",
            "description: Use quando <tag> aparecer.": "tags XML",
        }
        for fm, expected in cases.items():
            dirname = f"s{abs(hash(fm))}"
            d = self.make_skill(dirname, f"name: {dirname}\n{fm}")
            errors = vs.validate(d).errors
            self.assertTrue(any(expected in e for e in errors), f"{fm[:40]}: {errors}")

    def test_description_style_warnings(self):
        rep = vs.validate(self.make_skill("good-skill", "name: good-skill\ndescription: Eu posso ajudar com relatórios."))
        joined = " ".join(rep.warnings)
        self.assertIn("3ª pessoa", joined)
        self.assertIn("QUANDO", joined)

    def test_unknown_field_warning_and_known_fields_ok(self):
        rep = vs.validate(self.make_skill("good-skill", self.GOOD + "\nfoo: bar\nallowed-tools: Read Grep"))
        self.assertEqual(rep.warnings, ["frontmatter: campo desconhecido 'foo' (será ignorado)"])

    def test_invalid_yaml(self):
        rep = vs.validate(self.make_skill("good-skill", "name: [unclosed\ndescription: x"))
        self.assertTrue(any("YAML inválido" in e for e in rep.errors))

    def test_links_scripts_and_references(self):
        body = ("# T\n\nVeja [ref](reference/long.md), [faltando](reference/nope.md), "
                "[win](reference\\x.md).\n\nExecute `scripts/missing.py`.\n\n"
                "```text\n[ignorado](dentro/de/bloco.md)\n```\n")
        d = self.make_skill("good-skill", self.GOOD, body)
        (d / "reference").mkdir()
        (d / "reference" / "long.md").write_text("# Long\n" + "linha\n" * 120 + "[n](other.md)\n")
        (d / "scripts").mkdir()
        (d / "scripts" / "broken.py").write_text("def x(:\n")
        rep = vs.validate(d)
        errs, warns = " ".join(rep.errors), " ".join(rep.warnings)
        self.assertIn("reference/nope.md", errs)
        self.assertIn("barra invertida", errs)
        self.assertIn("erro de sintaxe", errs)
        self.assertNotIn("dentro/de/bloco.md", errs)
        self.assertIn("sem sumário", warns)
        self.assertIn("um nível de profundidade", warns)
        self.assertIn("scripts/missing.py", warns)

    def test_link_outside_skill(self):
        d = self.make_skill("good-skill", self.GOOD, "# T\n[fora](../outside.md)\n")
        (self.tmp / "outside.md").write_text("# fora\n")
        self.assertTrue(any("fora do diretório" in e for e in vs.validate(d).errors))

    def test_body_too_long_warning(self):
        rep = vs.validate(self.make_skill("good-skill", self.GOOD, "# T\n" + "x\n" * 520))
        self.assertTrue(any("500" in w for w in rep.warnings))

    def test_minimal_yaml_parser_fallback(self):
        raw = "name: a\ndescription: >\n  linha um\n  linha dois\nmetadata:\n  k: v\nq: 'x: y'"
        data = vs.parse_yaml_minimal(raw)
        self.assertEqual(data["description"], "linha um linha dois")
        self.assertEqual(data["q"], "x: y")
        self.assertIn("k: v", data["metadata"])

    def test_cli_json_and_exit_codes(self):
        good = self.make_skill("good-skill", self.GOOD)
        rc, out, _ = quiet(vs.main, [str(good), "--json"])
        self.assertEqual(rc, 0)
        self.assertTrue(json.loads(out)[0]["passed"])
        bad = self.make_skill("bad", "name: Bad\ndescription: x")
        rc, _, _ = quiet(vs.main, [str(bad)])
        self.assertEqual(rc, 1)


# ------------------------------------------------------------ scaffold_skill
class ScaffoldTests(TempDirTest):
    def test_creates_valid_skill_and_refuses_overwrite(self):
        target = scaffold.build("making-reports", "Gera relatórios: mensal e semanal. Use quando pedirem relatório.",
                                self.tmp, with_scripts=True, with_reference=True)
        rep = vs.validate(target)
        self.assertTrue(rep.passed(strict=True), rep.errors + rep.warnings)
        self.assertTrue((target / "scripts/run.py").exists())
        self.assertTrue(os.access(target / "scripts/run.py", os.X_OK))
        with self.assertRaises(FileExistsError):
            scaffold.build("making-reports", "Outra. Use quando X.", self.tmp, False, False)

    def test_rejects_invalid_name(self):
        with self.assertRaises(ValueError):
            scaffold.build("Claude-Tool", "Faz X. Use quando Y.", self.tmp, False, False)
        self.assertFalse((self.tmp / "Claude-Tool").exists())

    def test_cli(self):
        rc, out, _ = quiet(scaffold.main, ["x-skill", "--description", "Faz X. Use quando Y.", "--dest", str(self.tmp)])
        self.assertEqual(rc, 0)
        self.assertIn("[APROVADA]", out)
        rc, _, err = quiet(scaffold.main, ["x-skill", "--description", "Faz X. Use quando Y.", "--dest", str(self.tmp)])
        self.assertEqual(rc, 1)
        self.assertIn("já existe", err)


# --------------------------------------------------------------- lint_prompt
class LintPromptTests(unittest.TestCase):
    def test_fixture_prompt(self):
        r = lint.lint((FILES / "prompt_ruim.txt").read_text(encoding="utf-8"))
        errs, warns = " ".join(r["errors"]), " ".join(r["warnings"])
        self.assertIn("<email> aberta e nunca fechada", errs)
        self.assertIn("{{email_do_cliente}}", errs)
        self.assertIn("ênfase em maiúsculas", warns)
        self.assertIn("termos vagos", warns)
        self.assertIn("formato de saída", warns)
        self.assertFalse(r["passed"])

    def test_good_prompt(self):
        text = ("<role>Analista de suporte.</role>\n<instructions>\n1. Leia o ticket.\n"
                "2. Classifique.\n</instructions>\n<output_format>Responda em JSON com a chave label.</output_format>\n"
                "<example><input>a</input><output>b</output></example>\n")
        r = lint.lint(text)
        self.assertEqual(r["errors"], [])
        self.assertEqual(r["warnings"], [])
        self.assertIn("role", r["stats"]["xml_tags"])

    def test_negative_instructions_and_mismatched_tags(self):
        text = "Responda em JSON.\n" + "".join(f"- Não faça {i}\n" for i in range(5)) + "<a><b></a>\n"
        r = lint.lint(text)
        self.assertTrue(any("proibições" in w for w in r["warnings"]))
        self.assertTrue(any("<b> não foi fechada" in e for e in r["errors"]))

    def test_tags_inside_code_fence_ignored(self):
        r = lint.lint("Responda em JSON.\n````text\n```\n<open>\n```\n````\n")
        self.assertEqual(r["errors"], [])

    def test_cli_codes(self):
        rc, _, _ = quiet(lint.main, [str(FILES / "prompt_ruim.txt")])
        self.assertEqual(rc, 1)
        rc, _, _ = quiet(lint.main, ["/nao/existe.txt"])
        self.assertEqual(rc, 2)


# -------------------------------------------------------------------- new_adr
class AdrTests(TempDirTest):
    def test_numbering_supersede_and_no_overwrite(self):
        d = self.tmp / "adr"
        p1 = adr.create_adr("Usar PostgreSQL", d, date="2026-01-02")
        p2 = adr.create_adr("Adotar fila de pedidos", d)
        self.assertEqual(p1.name, "0001-usar-postgresql.md")
        self.assertTrue(p2.name.startswith("0002-"))
        p3 = adr.create_adr("Trocar cache local por Redis", d, supersedes=1)
        self.assertIn("Substituído por ADR-0003", p1.read_text())
        self.assertIn("Substitui: ADR-0001", p3.read_text())
        self.assertIn("Data: 2026-01-02", p1.read_text())

    def test_slug_and_validation(self):
        self.assertEqual(adr.slugify("Decisão: Ação & Reação!"), "decisao-acao-reacao")
        with self.assertRaises(ValueError):
            adr.create_adr("x", self.tmp, status="Talvez")
        with self.assertRaises(FileNotFoundError):
            adr.create_adr("x", self.tmp, supersedes=9)
        with self.assertRaises(ValueError):
            adr.create_adr("x", self.tmp, date="02/01/2026")

    def test_cli(self):
        rc, out, _ = quiet(adr.main, ["Primeira decisão", "--dir", str(self.tmp)])
        self.assertEqual(rc, 0)
        self.assertTrue(Path(out.strip()).exists())


# --------------------------------------------------------------- diff_hotspots
class DiffHotspotsTests(unittest.TestCase):
    def test_fixture_diff(self):
        files = hot.parse_unified_diff((FILES / "change.diff").read_text())
        self.assertEqual(files[0].path, "src/payments/charge.py")
        self.assertEqual(len(files[0].added), 8)
        r = hot.analyze(files)
        msgs = [(f["level"], f["message"], f["line"]) for f in r["findings"]]
        self.assertIn(("ALTO", "possível segredo: chave de API no formato sk-", 17), msgs)
        self.assertTrue(any(l == "MÉDIO" and "sem nenhum teste" in m for l, m, _ in msgs))
        self.assertTrue(any(l == "BAIXO" and "TODO" in m for l, m, _ in msgs))
        self.assertTrue(any(l == "BAIXO" and "depuração" in m for l, m, _ in msgs))
        self.assertEqual(r["findings"][0]["level"], "ALTO")

    def test_sensitive_paths_and_removed_tests(self):
        diff = ("diff --git a/db/migrations/001.sql b/db/migrations/001.sql\n+++ b/db/migrations/001.sql\n@@ -0,0 +1 @@\n+ALTER TABLE x;\n"
                "diff --git a/tests/test_x.py b/tests/test_x.py\ndeleted file mode 100644\n--- a/tests/test_x.py\n+++ /dev/null\n@@ -1,2 +0,0 @@\n-a\n-b\n")
        r = hot.analyze(hot.parse_unified_diff(diff))
        msgs = " ".join(f["message"] for f in r["findings"])
        self.assertIn("migração de banco", msgs)
        self.assertIn("teste removido", msgs)
        self.assertEqual(r["summary"]["files"], 2)

    def test_git_mode_in_temp_repo(self):
        if shutil.which("git") is None:
            self.skipTest("git indisponível")
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                   "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}
            run = lambda *a: subprocess.run(["git", *a], cwd=tmp, check=True, capture_output=True, env=env)
            run("init", "-q")
            Path(tmp, "app.py").write_text("x = 1\n")
            run("add", ".")
            run("commit", "-qm", "init")
            Path(tmp, "app.py").write_text("x = 1\npassword = 'hunter2hunter2'\n")
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                rc, out, _ = quiet(hot.main, ["--git", "HEAD", "--json"])
            finally:
                os.chdir(cwd)
            self.assertEqual(rc, 0)
            self.assertIn("credencial literal", out)

    def test_empty_diff(self):
        rc, out, _ = quiet(hot.main, [os.devnull])
        self.assertEqual(rc, 0)
        self.assertIn("vazio", out)


# ------------------------------------------------------------- log_signatures
class LogSignatureTests(unittest.TestCase):
    def test_fixture_log(self):
        lines = (FILES / "app.log").read_text().splitlines()
        r = logs.analyze([("app.log", lines)], None)
        top = r["signatures"][0]
        self.assertEqual(top["count"], 3)
        self.assertIn("timeout acquiring connection", top["signature"])
        self.assertEqual(top["first"], "app.log:4")
        self.assertEqual(top["last"], "app.log:7")
        self.assertEqual(r["tracebacks"], 1)
        self.assertIn("sqlalchemy.exc.TimeoutError", r["exceptions"])
        self.assertEqual(r["levels"]["ERROR"], 5)

    def test_level_filter_and_normalization(self):
        self.assertEqual(logs.normalize("2026-01-01T10:00:00Z id=0xff ip 10.1.2.3:80 took 35ms 'q'"),
                         "<TS> id=<HEX> ip <IP> took <N> <STR>")
        r = logs.analyze([("x", ["INFO a", "WARN b", "ERROR c 1", "ERROR c 2"])], "ERROR")
        self.assertEqual([g["count"] for g in r["signatures"]], [2])

    def test_cli_bad_level(self):
        rc, _, err = quiet(logs.main, [str(FILES / "app.log"), "--level", "LOUD"])
        self.assertEqual(rc, 2)


# --------------------------------------------------------------- check_markdown
class CheckMarkdownTests(TempDirTest):
    def test_detects_problems(self):
        (self.tmp / "other.md").write_text("# Outro\n\n## Seção Ação\n")
        (self.tmp / "doc.md").write_text(
            "# Título\n\n#### Pulo\n\n[aqui](other.md) [ok](other.md#seção-ação) [ruim](other.md#nao) "
            "[x](missing.md) [web](https://example.com)\n\nTODO revisar\n\n```\nsem linguagem\n```\n\n```python\naberto\n")
        cache = {}
        errors, warnings = md.check_file(self.tmp / "doc.md", cache)
        e, w = " ".join(errors), " ".join(warnings)
        self.assertIn("missing.md", e)
        self.assertIn("'#nao'", e)
        self.assertNotIn("seção-ação", e)
        self.assertIn("não fechado", e)
        self.assertIn("salto de H1 para H4", w)
        self.assertIn("genérico 'aqui'", w)
        self.assertIn("pendência", w)
        self.assertIn("sem linguagem", w)

    def test_nested_fences_and_duplicate_anchors(self):
        (self.tmp / "a.md").write_text("# A\n\n## X\n\n## X\n\n[s](#x-1)\n\n````markdown\n```bash\nls\n```\n````\n")
        errors, warnings = md.check_file(self.tmp / "a.md", {})
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_slug(self):
        self.assertEqual(md.github_slug("Configurar o `banco` (v2)!"), "configurar-o-banco-v2")

    def test_cli_strict(self):
        (self.tmp / "w.md").write_text("sem h1\n")
        self.assertEqual(quiet(md.main, [str(self.tmp)])[0], 0)
        self.assertEqual(quiet(md.main, [str(self.tmp), "--strict"])[0], 1)
        self.assertEqual(quiet(md.main, [str(self.tmp / "nada.md")])[0], 2)


# ---------------------------------------------------------------- profile_csv
class ProfileCsvTests(TempDirTest):
    def test_fixture_csv(self):
        r = prof.profile(FILES / "vendas.csv", None, None, None, 3)
        self.assertEqual(r["delimiter"], ";")
        self.assertEqual(r["rows"], 12)
        self.assertEqual(r["duplicate_rows"], 1)
        cols = {c["name"]: c for c in r["profile"]}
        self.assertEqual(cols["valor"]["type"], "decimal")
        self.assertEqual(cols["valor"]["nulls"], 1)
        self.assertEqual(cols["valor"]["max"], 95000)
        self.assertGreaterEqual(cols["valor"]["outliers"], 1)
        self.assertEqual(cols["data"]["type"], "data")
        self.assertEqual(cols["cancelado"]["type"], "booleano")
        self.assertEqual(cols["vendedor"]["leading_trailing_spaces"], 1)
        self.assertEqual(cols["vendedor"]["case_variants"], 1)

    def test_encoding_ragged_and_number_formats(self):
        p = self.tmp / "l1.csv"
        p.write_bytes("nome,qtd,preço\nJoão,1,2.5\nZé,2\nAçaí,1.000,3.75\n".encode("latin-1"))
        r = prof.profile(p, None, None, None, 3)
        self.assertEqual(r["encoding"], "cp1252")
        self.assertEqual(r["ragged_rows"]["count"], 1)
        cols = {c["name"]: c for c in r["profile"]}
        self.assertEqual(cols["qtd"]["type"], "inteiro")
        self.assertEqual(cols["qtd"]["max"], 1000)
        self.assertEqual(cols["preço"]["type"], "decimal")

    def test_number_parsing(self):
        self.assertEqual(prof.to_number("1.234,56"), (1234.56, "float"))
        self.assertEqual(prof.to_number("1,234.56"), (1234.56, "float"))
        self.assertEqual(prof.to_number("-42"), (-42.0, "int"))
        self.assertEqual(prof.to_number("abc"), (None, None))

    def test_cli(self):
        rc, out, _ = quiet(prof.main, [str(FILES / "vendas.csv")])
        self.assertEqual(rc, 0)
        self.assertIn("| valor | decimal |", out)
        empty = self.tmp / "e.csv"
        empty.write_text("")
        self.assertEqual(quiet(prof.main, [str(empty)])[0], 2)
        rc, out, _ = quiet(prof.main, [str(FILES / "vendas.csv"), "--json", "--max-rows", "5"])
        self.assertTrue(json.loads(out)["truncated"])


# ------------------------------------------------------------- suite tools
class SuiteToolTests(TempDirTest):
    def test_validate_suite_passes(self):
        rc, out, _ = quiet(suite.main, [])
        self.assertEqual(rc, 0, out)

    def test_package_skills(self):
        rc, out, _ = quiet(pkg.main, ["--out", str(self.tmp)])
        self.assertEqual(rc, 0, out)
        zips = sorted(self.tmp.glob("*.zip"))
        self.assertEqual(len(zips), len([p for p in SKILLS.iterdir() if p.is_dir()]))
        with zipfile.ZipFile(self.tmp / "reviewing-code.zip") as zf:
            names = zf.namelist()
        self.assertIn("reviewing-code/SKILL.md", names)
        self.assertTrue(all(n.startswith("reviewing-code/") for n in names))
        self.assertFalse(any("__pycache__" in n for n in names))
        self.assertEqual(quiet(pkg.main, ["--out", str(self.tmp), "--skill", "nope"])[0], 2)

    def test_trigger_runner_parsing_and_case_loading(self):
        stream = "\n".join([
            json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Skill", "input": {"skill": "power-suite:reviewing-code"}},
                {"type": "tool_use", "name": "Bash", "input": {"command": "python3 scripts/diff_hotspots.py -"}}]}}),
            "linha que não é JSON",
            json.dumps({"type": "result", "result": "Solicitar mudanças"}),
        ])
        parsed = runner.parse_stream(stream)
        self.assertEqual(parsed["skills_loaded"], ["power-suite:reviewing-code"])
        self.assertEqual(parsed["bash_commands"], ["python3 scripts/diff_hotspots.py -"])
        self.assertEqual(parsed["final"], "Solicitar mudanças")
        cases = runner.load_cases(["reviewing-code"])
        self.assertEqual([c["id"] for c in cases], [f"reviewing-code#{i}" for i in (1, 2, 3)])
        self.assertEqual(len(runner.load_cases(None)), 24)

    def test_install_script_respects_existing(self):
        if shutil.which("bash") is None:
            self.skipTest("bash indisponível")
        home = self.tmp / "home"
        home.mkdir()
        existing = home / ".claude/skills/reviewing-code"
        existing.mkdir(parents=True)
        (existing / "SKILL.md").write_text("original")
        env = {**os.environ, "HOME": str(home)}
        script = str(ROOT / "tools/install.sh")
        dry = subprocess.run(["bash", script, "--personal", "--dry-run"], env=env, capture_output=True, text=True)
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertEqual(sorted(p.name for p in (home / ".claude/skills").iterdir()), ["reviewing-code"])
        real = subprocess.run(["bash", script, "--personal"], env=env, capture_output=True, text=True)
        self.assertEqual(real.returncode, 0, real.stderr)
        self.assertIn("PULADA   reviewing-code", real.stdout)
        self.assertEqual((existing / "SKILL.md").read_text(), "original")
        self.assertTrue((home / ".claude/skills/engineering-prompts/SKILL.md").exists())
        forced = subprocess.run(["bash", script, "--personal", "--force", "--only", "reviewing-code"],
                                env=env, capture_output=True, text=True)
        self.assertEqual(forced.returncode, 0, forced.stderr)
        self.assertNotEqual((existing / "SKILL.md").read_text(), "original")
        proj = subprocess.run(["bash", script, "--project", str(self.tmp / "nao-existe")],
                              env=env, capture_output=True, text=True)
        self.assertEqual(proj.returncode, 1)


if __name__ == "__main__":
    unittest.main()
