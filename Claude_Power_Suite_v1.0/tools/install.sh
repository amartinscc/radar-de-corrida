#!/usr/bin/env bash
# Instala as skills da Power Suite como skills avulsas do Claude Code.
#
# Uso:
#   tools/install.sh --personal              # ~/.claude/skills/
#   tools/install.sh --project CAMINHO       # CAMINHO/.claude/skills/
#   tools/install.sh ... --dry-run           # mostra o que faria, sem copiar
#   tools/install.sh ... --force             # substitui skills de mesmo nome
#   tools/install.sh ... --only NOME[,NOME]  # instala só as skills listadas
#
# Sem --force, uma skill já existente no destino é PULADA (nunca sobrescrita).
# Para instalar como plugin (com namespace /power-suite:...), veja docs/INSTALACAO.md.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/skills"
DEST=""
DRY_RUN=0
FORCE=0
ONLY=""

usage() { sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --personal) DEST="${HOME}/.claude/skills"; shift ;;
    --project)  [[ $# -ge 2 ]] || usage; DEST="$2/.claude/skills"; shift 2 ;;
    --dry-run)  DRY_RUN=1; shift ;;
    --force)    FORCE=1; shift ;;
    --only)     [[ $# -ge 2 ]] || usage; ONLY=",$2,"; shift 2 ;;
    -h|--help)  usage ;;
    *) echo "ERRO: opção desconhecida: $1" >&2; usage ;;
  esac
done
[[ -n "$DEST" ]] || usage

if [[ "$DEST" == */.claude/skills && "$DEST" != "${HOME}/.claude/skills" ]]; then
  project_dir="${DEST%/.claude/skills}"
  [[ -d "$project_dir" ]] || { echo "ERRO: projeto '$project_dir' não existe" >&2; exit 1; }
fi

echo "Validando skills antes de instalar..."
python3 "$SRC/authoring-agent-skills/scripts/validate_skill.py" --strict "$SRC"/*/ >/dev/null || {
  echo "ERRO: validação falhou; rode: python3 $SRC/authoring-agent-skills/scripts/validate_skill.py --strict $SRC/*/" >&2
  exit 1
}

installed=0; skipped=0
[[ $DRY_RUN -eq 1 ]] || mkdir -p "$DEST"
for dir in "$SRC"/*/; do
  name="$(basename "$dir")"
  if [[ -n "$ONLY" && "$ONLY" != *",$name,"* ]]; then continue; fi
  target="$DEST/$name"
  if [[ -e "$target" && $FORCE -eq 0 ]]; then
    echo "PULADA   $name (já existe em $target; use --force para substituir)"
    skipped=$((skipped + 1)); continue
  fi
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "SIMULADO $name -> $target"
  else
    rm -rf "$target"
    cp -R "$dir" "$target"
    find "$target" -name '__pycache__' -type d -prune -exec rm -rf {} +
    echo "INSTALADA $name -> $target"
  fi
  installed=$((installed + 1))
done
echo "Concluído: $installed instalada(s)/simulada(s), $skipped pulada(s). Destino: $DEST"
