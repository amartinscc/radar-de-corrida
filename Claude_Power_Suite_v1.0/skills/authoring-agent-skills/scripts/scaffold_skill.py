#!/usr/bin/env python3
"""Cria o esqueleto de uma nova Agent Skill sem sobrescrever nada existente.

Uso:
  python3 scaffold_skill.py NOME --description "Faz X. Use quando Y." \
      [--dest DIRETORIO] [--with-scripts] [--with-reference]

- NOME é validado com as mesmas regras do validate_skill.py (≤64, [a-z0-9-],
  sem 'anthropic'/'claude').
- A description é validada (não vazia, ≤1024, sem tags XML).
- Se DIRETORIO/NOME já existir, o script aborta com código 1.
- Ao final, executa a validação do esqueleto criado e imprime o relatório.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_skill as vs  # noqa: E402

SKILL_TEMPLATE = """---
name: {name}
description: {description}
---

# {title}

## Quando usar
- (Liste situações concretas que acionam esta skill.)

## Fluxo de trabalho

Copie este checklist e marque o progresso:

```
- [ ] Passo 1: entender o pedido e as restrições
- [ ] Passo 2: executar o procedimento principal
- [ ] Passo 3: validar o resultado
```

**Passo 1** — (descreva).

**Passo 2** — (descreva).

**Passo 3** — (descreva como verificar; inclua o laço validar → corrigir → repetir).

## Formato de saída
(Defina o formato exato esperado, com um exemplo.)
{extras}"""

REFERENCE_TEMPLATE = """# Referência — {title}

(Conteúdo detalhado carregado sob demanda. Se passar de 100 linhas,
adicione um '## Sumário' no topo.)
"""

SCRIPT_TEMPLATE = '''#!/usr/bin/env python3
"""Script utilitário da skill {name}.

Uso: python3 scripts/run.py ENTRADA
"""
import sys


def main(argv):
    if len(argv) != 2:
        print("uso: python3 scripts/run.py ENTRADA", file=sys.stderr)
        return 2
    print(f"processando {{argv[1]}}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
'''


def build(name: str, description: str, dest: Path, with_scripts: bool,
          with_reference: bool) -> Path:
    target = dest / name
    if target.exists():
        raise FileExistsError(f"'{target}' já existe; nada foi alterado")

    probe = vs.Report(target)
    vs.check_name(probe, name, name)
    vs.check_description(probe, description, None)
    if probe.errors:
        raise ValueError("; ".join(probe.errors))

    title = name.replace("-", " ").capitalize()
    extras = []
    if with_reference:
        extras.append("\n## Referências\n- Detalhes: [reference/guide.md](reference/guide.md)\n")
    if with_scripts:
        extras.append("\n## Scripts\nExecute (não leia) o utilitário:\n\n"
                      "```bash\npython3 scripts/run.py ENTRADA\n```\n")

    target.mkdir(parents=True)
    safe_desc = description.replace("\n", " ").strip()
    if ":" in safe_desc or safe_desc[:1] in "\"'[{>|*&!%@`#":
        safe_desc = '"' + safe_desc.replace("\\", "\\\\").replace('"', '\\"') + '"'
    (target / "SKILL.md").write_text(
        SKILL_TEMPLATE.format(name=name, description=safe_desc, title=title,
                              extras="".join(extras)),
        encoding="utf-8")
    if with_reference:
        (target / "reference").mkdir()
        (target / "reference" / "guide.md").write_text(
            REFERENCE_TEMPLATE.format(title=title), encoding="utf-8")
    if with_scripts:
        (target / "scripts").mkdir()
        script = target / "scripts" / "run.py"
        script.write_text(SCRIPT_TEMPLATE.format(name=name), encoding="utf-8")
        script.chmod(0o755)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cria o esqueleto de uma Agent Skill.")
    parser.add_argument("name")
    parser.add_argument("--description", required=True)
    parser.add_argument("--dest", default=".", help="diretório onde a skill será criada")
    parser.add_argument("--with-scripts", action="store_true")
    parser.add_argument("--with-reference", action="store_true")
    args = parser.parse_args(argv)
    try:
        target = build(args.name, args.description, Path(args.dest),
                       args.with_scripts, args.with_reference)
    except (FileExistsError, ValueError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1
    print(f"Skill criada em {target}")
    print(vs.format_report(vs.validate(target), strict=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
