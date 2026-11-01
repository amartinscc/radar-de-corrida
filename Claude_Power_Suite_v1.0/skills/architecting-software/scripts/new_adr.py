#!/usr/bin/env python3
"""Cria um novo Architecture Decision Record (ADR) numerado sequencialmente.

Uso:
  python3 new_adr.py "Título da decisão" [--dir docs/adr] [--status Proposto]
                     [--supersedes 3] [--date AAAA-MM-DD]

- Procura arquivos NNNN-*.md no diretório e usa o próximo número livre.
- Nunca sobrescreve um arquivo existente.
- Com --supersedes N, atualiza a linha 'Status:' do ADR N para
  'Substituído por ADR-XXXX' (única alteração feita em arquivo existente).
- Imprime o caminho do arquivo criado.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import unicodedata
from pathlib import Path

VALID_STATUS = ("Proposto", "Aceito", "Rejeitado", "Obsoleto", "Substituído")
ADR_FILE_RE = re.compile(r"^(\d{4})-.*\.md$")

TEMPLATE = """# ADR-{number:04d}: {title}

- Status: {status}
- Data: {date}
- Decisores: (nomes ou papéis)
{supersedes_line}
## Contexto

Qual problema exige uma decisão agora? Inclua forças em jogo (requisitos,
restrições, prazos, atributos de qualidade) com números quando houver.

## Opções consideradas

1. **Opção A** — resumo.
2. **Opção B** — resumo.
3. **Não fazer nada** — consequência de manter o estado atual.

## Decisão

Escolhemos **...** porque ... (ligue a justificativa às forças do Contexto).

## Consequências

- Positivas: ...
- Negativas / custos aceitos: ...
- Riscos e mitigação: ...

## Critérios de revisão

Reavaliar esta decisão se: (gatilho mensurável, ex.: "p95 > 300 ms por 7 dias").
"""


def slugify(title: str) -> str:
    norm = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", norm).strip("-").lower()
    return slug[:60].rstrip("-") or "decisao"


def next_number(adr_dir: Path) -> int:
    numbers = [int(m.group(1)) for p in adr_dir.glob("*.md") if (m := ADR_FILE_RE.match(p.name))]
    return max(numbers, default=0) + 1


def find_adr(adr_dir: Path, number: int) -> Path | None:
    matches = sorted(adr_dir.glob(f"{number:04d}-*.md"))
    return matches[0] if matches else None


def create_adr(title: str, adr_dir: Path, status: str = "Proposto",
               supersedes: int | None = None, date: str | None = None) -> Path:
    if not title.strip():
        raise ValueError("o título não pode ser vazio")
    if status not in VALID_STATUS:
        raise ValueError(f"status inválido '{status}'; use um de: {', '.join(VALID_STATUS)}")
    date = date or dt.date.today().isoformat()
    dt.date.fromisoformat(date)  # valida o formato

    adr_dir.mkdir(parents=True, exist_ok=True)
    old: Path | None = None
    if supersedes is not None:
        old = find_adr(adr_dir, supersedes)
        if old is None:
            raise FileNotFoundError(f"ADR {supersedes:04d} não encontrado em {adr_dir}")

    number = next_number(adr_dir)
    path = adr_dir / f"{number:04d}-{slugify(title)}.md"
    if path.exists():
        raise FileExistsError(f"{path} já existe")
    supersedes_line = f"- Substitui: ADR-{supersedes:04d}\n" if supersedes is not None else ""
    path.write_text(TEMPLATE.format(number=number, title=title.strip(), status=status,
                                    date=date, supersedes_line=supersedes_line),
                    encoding="utf-8")

    if old is not None:
        text = old.read_text(encoding="utf-8")
        new_text, count = re.subn(r"^- Status: .*$", f"- Status: Substituído por ADR-{number:04d}",
                                  text, count=1, flags=re.MULTILINE)
        if count:
            old.write_text(new_text, encoding="utf-8")
        else:
            print(f"AVISO: linha '- Status:' não encontrada em {old.name}; atualize manualmente",
                  file=sys.stderr)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cria um ADR numerado.")
    parser.add_argument("title")
    parser.add_argument("--dir", default="docs/adr")
    parser.add_argument("--status", default="Proposto")
    parser.add_argument("--supersedes", type=int)
    parser.add_argument("--date")
    args = parser.parse_args(argv)
    try:
        path = create_adr(args.title, Path(args.dir), args.status, args.supersedes, args.date)
    except (ValueError, FileExistsError, FileNotFoundError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
