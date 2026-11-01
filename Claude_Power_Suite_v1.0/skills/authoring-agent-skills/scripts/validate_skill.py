#!/usr/bin/env python3
"""Valida um diretório de Agent Skill contra as regras documentadas pela Anthropic.

Regras de ERRO (bloqueiam o uso da skill em pelo menos uma superfície):
  - SKILL.md ausente, sem frontmatter YAML na primeira linha ou sem fechamento.
  - name ausente, > 64 caracteres, fora de [a-z0-9-], com tags XML ou com as
    palavras reservadas "anthropic"/"claude".
  - description ausente/vazia, > 1024 caracteres ou com tags XML.
  - Link relativo no SKILL.md apontando para arquivo inexistente.
  - Caminho com barra invertida (estilo Windows) em link.
  - Script Python do pacote com erro de sintaxe.

Regras de AVISO (boas práticas oficiais; viram erro com --strict):
  - Corpo do SKILL.md com 500 linhas ou mais.
  - name diferente do nome do diretório; hífens no início/fim ou duplicados.
  - description em 1ª/2ª pessoa ou sem indicar QUANDO usar.
  - description + when_to_use acima de 1536 caracteres (corte do Claude Code).
  - Campo de frontmatter desconhecido.
  - Arquivo de referência com mais de 100 linhas sem sumário.
  - Arquivo de referência que aponta para outro .md (aninhamento > 1 nível).
  - Script mencionado no corpo (scripts/...) que não existe.

Uso:
  python3 validate_skill.py CAMINHO_DA_SKILL [CAMINHO ...] [--strict] [--json]

Saída: relatório legível (ou JSON com --json). Código de saída 0 = aprovado,
1 = reprovado, 2 = erro de uso.
Dependências: apenas biblioteca padrão (PyYAML é usado se estiver instalado).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Limites documentados em platform.claude.com/docs (Agent Skills overview e
# best practices) e code.claude.com/docs/en/skills.
NAME_MAX = 64
DESCRIPTION_MAX = 1024
CLAUDE_CODE_LISTING_MAX = 1536  # description + when_to_use no Claude Code
BODY_LINES_RECOMMENDED_MAX = 500
REFERENCE_TOC_THRESHOLD = 100
RESERVED_WORDS = ("anthropic", "claude")

# Campos aceitos pela API/claude.ai (name, description) e pelo Claude Code.
KNOWN_FIELDS = {
    "name", "description", "when_to_use", "argument-hint", "arguments",
    "disable-model-invocation", "user-invocable", "allowed-tools",
    "disallowed-tools", "model", "effort", "context", "agent", "background",
    "hooks", "paths", "shell", "metadata", "license", "compatibility",
}

NAME_RE = re.compile(r"^[a-z0-9-]+$")
XML_TAG_RE = re.compile(r"<\s*/?\s*[A-Za-z][A-Za-z0-9_-]*(\s[^<>]*)?/?\s*>")
MD_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
SCRIPT_MENTION_RE = re.compile(r"(?<![\w/.-])(scripts/[\w./-]+\.(?:py|sh|js|ts|rb))")
FIRST_SECOND_PERSON_RE = re.compile(
    r"^\s*(I |I'm |I can|You |You can|Your |Eu |Posso |Você |Voce |Vocês |Te ajudo)",
    re.IGNORECASE,
)
WHEN_CUE_RE = re.compile(
    r"\b(use when|use it when|when the user|when working|whenever|use quando|"
    r"usar quando|quando o usu[aá]rio|quando houver|quando for|sempre que|"
    r"acione|acionar|aciona)\b",
    re.IGNORECASE,
)
TOC_RE = re.compile(r"^#{1,3}\s*(contents|table of contents|sum[aá]rio|[ií]ndice|conte[uú]do)\b",
                    re.IGNORECASE | re.MULTILINE)


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


class Report:
    def __init__(self, skill_dir: Path):
        self.skill_dir = skill_dir
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: dict = {}

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def passed(self, strict: bool) -> bool:
        return not self.errors and (not strict or not self.warnings)

    def as_dict(self, strict: bool) -> dict:
        return {
            "skill": str(self.skill_dir),
            "passed": self.passed(strict),
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
        }


# ---------------------------------------------------------------- frontmatter
def split_frontmatter(text: str) -> tuple[str | None, str, int]:
    """Retorna (yaml, corpo, linha_inicial_do_corpo). yaml=None se ausente."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text, 1
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[1:idx]), "\n".join(lines[idx + 1:]), idx + 2
    return None, text, 1


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_yaml_minimal(raw: str) -> dict:
    """Parser mínimo para frontmatter simples (fallback quando PyYAML falta).

    Suporta: `chave: valor`, valores entre aspas, escalares em bloco (| e >)
    e mapas/listas aninhados (guardados como texto bruto).
    """
    data: dict = {}
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if line[0] in " \t":
            raise ValueError(f"indentação inesperada na linha {i + 1} do frontmatter")
        if ":" not in line:
            raise ValueError(f"linha {i + 1} do frontmatter não é 'chave: valor'")
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        block: list[str] = []
        j = i + 1
        while j < len(lines) and (not lines[j].strip() or lines[j][0] in " \t"):
            block.append(lines[j])
            j += 1
        if value and value[0] in "|>":
            stripped = [b.strip() for b in block]
            joiner = "\n" if value[0] == "|" else " "
            data[key] = joiner.join(s for s in stripped if s).strip()
        elif value == "" and block:
            data[key] = "\n".join(block)  # mapa/lista aninhado: texto bruto
        else:
            data[key] = _unquote(value)
        i = j
    return data


def parse_frontmatter(raw: str) -> dict:
    try:
        import yaml  # type: ignore
    except ImportError:
        return parse_yaml_minimal(raw)
    loaded = yaml.safe_load(raw)
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError("o frontmatter precisa ser um mapa YAML (chave: valor)")
    return loaded


# --------------------------------------------------------------------- checks
def check_name(rep: Report, name, dir_name: str) -> None:
    if name is None or (isinstance(name, str) and not name.strip()):
        rep.error("frontmatter: campo 'name' ausente (obrigatório na API e no claude.ai)")
        return
    if not isinstance(name, str):
        rep.error(f"frontmatter: 'name' precisa ser texto, recebido {type(name).__name__}")
        return
    if len(name) > NAME_MAX:
        rep.error(f"name: {len(name)} caracteres (máximo {NAME_MAX})")
    if not NAME_RE.match(name):
        rep.error(f"name: '{name}' deve conter apenas letras minúsculas, números e hífens")
    if XML_TAG_RE.search(name):
        rep.error("name: não pode conter tags XML")
    for word in RESERVED_WORDS:
        if word in name.lower():
            rep.error(f"name: contém a palavra reservada '{word}'")
    if name.startswith("-") or name.endswith("-") or "--" in name:
        rep.warn(f"name: '{name}' tem hífen no início/fim ou hífens consecutivos")
    if name != dir_name:
        rep.warn(f"name '{name}' difere do diretório '{dir_name}' "
                 "(o Claude Code usa o diretório como nome padrão; mantenha iguais)")


def check_description(rep: Report, desc, when_to_use) -> None:
    if desc is None or not str(desc).strip():
        rep.error("frontmatter: campo 'description' ausente ou vazio")
        return
    if not isinstance(desc, str):
        rep.error(f"description precisa ser texto, recebido {type(desc).__name__}")
        return
    rep.info["description_chars"] = len(desc)
    if len(desc) > DESCRIPTION_MAX:
        rep.error(f"description: {len(desc)} caracteres (máximo {DESCRIPTION_MAX})")
    if XML_TAG_RE.search(desc):
        rep.error("description: não pode conter tags XML")
    if FIRST_SECOND_PERSON_RE.search(desc):
        rep.warn("description: escreva em 3ª pessoa ('Revisa código...'), "
                 "não em 1ª/2ª pessoa — ela é injetada no prompt de sistema")
    combined = desc + (str(when_to_use) if when_to_use else "")
    if not WHEN_CUE_RE.search(combined):
        rep.warn("description: não indica QUANDO usar a skill "
                 "(ex.: 'Use quando...' / 'Use when...')")
    if len(combined) > CLAUDE_CODE_LISTING_MAX:
        rep.warn(f"description + when_to_use = {len(combined)} caracteres; o Claude Code "
                 f"trunca em {CLAUDE_CODE_LISTING_MAX}")


def iter_links(text: str):
    for lineno, line in iter_unfenced(text):
        for match in MD_LINK_RE.finditer(line):
            yield lineno, match.group(1)


def is_local_link(target: str) -> bool:
    return not re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE) and not target.startswith("#")


def check_links(rep: Report, body: str, body_offset: int) -> list[Path]:
    """Valida links relativos do SKILL.md. Retorna arquivos .md referenciados."""
    referenced: list[Path] = []
    for lineno, target in iter_links(body):
        if not is_local_link(target):
            continue
        where = f"SKILL.md:{lineno + body_offset - 1}"
        if "\\" in target:
            rep.error(f"{where}: link '{target}' usa barra invertida; use '/'")
            continue
        path_part = target.split("#", 1)[0]
        if not path_part:
            continue
        resolved = (rep.skill_dir / path_part).resolve()
        try:
            resolved.relative_to(rep.skill_dir.resolve())
        except ValueError:
            rep.error(f"{where}: link '{target}' aponta para fora do diretório da skill")
            continue
        if not resolved.exists():
            rep.error(f"{where}: link '{target}' aponta para arquivo inexistente")
            continue
        if resolved.suffix.lower() == ".md":
            referenced.append(resolved)
    return referenced


def check_reference_file(rep: Report, path: Path) -> None:
    rel = path.relative_to(rep.skill_dir.resolve()).as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")
    n_lines = len(text.splitlines())
    if n_lines > REFERENCE_TOC_THRESHOLD and not TOC_RE.search(text):
        rep.warn(f"{rel}: {n_lines} linhas sem sumário no topo "
                 "('## Sumário' ou '## Contents')")
    for _, target in iter_links(text):
        if is_local_link(target) and target.split("#", 1)[0].lower().endswith(".md"):
            rep.warn(f"{rel}: referencia '{target}' — mantenha referências a apenas "
                     "um nível de profundidade a partir do SKILL.md")


def check_scripts(rep: Report, body: str) -> None:
    for mention in sorted(set(SCRIPT_MENTION_RE.findall(body))):
        if not (rep.skill_dir / mention).exists():
            rep.warn(f"corpo menciona '{mention}', que não existe no pacote")
    scripts = sorted(rep.skill_dir.rglob("*.py"))
    rep.info["python_scripts"] = [p.relative_to(rep.skill_dir).as_posix() for p in scripts]
    for script in scripts:
        if "__pycache__" in script.parts:
            continue
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except SyntaxError as exc:
            rep.error(f"{script.relative_to(rep.skill_dir).as_posix()}: erro de sintaxe "
                      f"na linha {exc.lineno}: {exc.msg}")


def validate(skill_dir: Path) -> Report:
    rep = Report(skill_dir)
    if not skill_dir.is_dir():
        rep.error(f"'{skill_dir}' não é um diretório")
        return rep
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        candidates = [p.name for p in skill_dir.iterdir() if p.name.lower() == "skill.md"]
        hint = f" (encontrado '{candidates[0]}'; o nome deve ser exatamente SKILL.md)" if candidates else ""
        rep.error("SKILL.md ausente" + hint)
        return rep

    text = skill_md.read_text(encoding="utf-8", errors="replace")
    raw_yaml, body, body_offset = split_frontmatter(text)
    if raw_yaml is None:
        rep.error("SKILL.md deve começar com '---' na primeira linha e fechar o frontmatter com '---'")
        return rep
    try:
        meta = parse_frontmatter(raw_yaml)
    except Exception as exc:  # erro de YAML deve ser reportado, não propagado
        rep.error(f"frontmatter YAML inválido: {exc}")
        return rep

    rep.info["name"] = meta.get("name")
    check_name(rep, meta.get("name"), skill_dir.name)
    check_description(rep, meta.get("description"), meta.get("when_to_use"))
    for field in sorted(set(meta) - KNOWN_FIELDS):
        rep.warn(f"frontmatter: campo desconhecido '{field}' (será ignorado)")

    body_lines = len(body.splitlines())
    rep.info["body_lines"] = body_lines
    if not body.strip():
        rep.error("corpo do SKILL.md vazio: inclua as instruções")
    if body_lines >= BODY_LINES_RECOMMENDED_MAX:
        rep.warn(f"corpo com {body_lines} linhas; mantenha abaixo de "
                 f"{BODY_LINES_RECOMMENDED_MAX} e mova detalhes para arquivos de referência")

    for ref in check_links(rep, body, body_offset):
        check_reference_file(rep, ref)
    check_scripts(rep, body)
    return rep


def format_report(rep: Report, strict: bool) -> str:
    status = "APROVADA" if rep.passed(strict) else "REPROVADA"
    out = [f"[{status}] {rep.skill_dir}"]
    out += [f"  ERRO:  {e}" for e in rep.errors]
    out += [f"  AVISO: {w}" for w in rep.warnings]
    if not rep.errors and not rep.warnings:
        out.append("  nenhum problema encontrado")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Valida diretórios de Agent Skills.")
    parser.add_argument("paths", nargs="+", help="diretório(s) contendo SKILL.md")
    parser.add_argument("--strict", action="store_true", help="avisos também reprovam")
    parser.add_argument("--json", action="store_true", help="saída em JSON")
    args = parser.parse_args(argv)

    reports = [validate(Path(p)) for p in args.paths]
    if args.json:
        print(json.dumps([r.as_dict(args.strict) for r in reports], ensure_ascii=False, indent=2))
    else:
        print("\n\n".join(format_report(r, args.strict) for r in reports))
    return 0 if all(r.passed(args.strict) for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
