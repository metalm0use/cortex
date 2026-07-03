#!/usr/bin/env bash
set -euo pipefail

if [[ -d /usr/bin ]]; then
  PATH="/usr/bin:/bin:$PATH"
fi

usage() {
  cat <<'EOF'
Usage: scripts/deploy-skills.sh [--agent auto|codex|claude|gemini|all] [--target DIR] [--dry-run]

Deploy Cortex vault skills as managed native SKILL.md wrappers.

Defaults:
  --agent auto    Detect installed agent homes and deploy to those targets.
  --target DIR    Override the native skill folder.
  --dry-run       Print planned writes without changing files.

Known default targets:
  codex   ${CODEX_HOME:-$HOME/.codex}/skills
  claude  ${CLAUDE_HOME:-$HOME/.claude}/skills
  gemini  ${GEMINI_HOME:-$HOME/.gemini}/skills
EOF
}

agent="auto"
target=""
dry_run=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)
      agent="${2:-}"
      shift 2
      ;;
    --target)
      target="${2:-}"
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$agent" in
  auto|codex|claude|gemini|all) ;;
  *)
    echo "ERROR: unsupported agent: $agent" >&2
    exit 2
    ;;
esac

script_path="${BASH_SOURCE[0]}"
script_dir_part="${script_path%/*}"
if [[ "$script_dir_part" == "$script_path" ]]; then
  script_dir_part="."
fi
script_dir="$(cd "$script_dir_part" && pwd)"
vault_root="$(cd "$script_dir/.." && pwd)"
skills_root="$vault_root/skills"

frontmatter_value() {
  local file="$1"
  local key="$2"
  awk -v key="$key" '
    BEGIN { in_fm = 0 }
    NR == 1 && $0 == "---" { in_fm = 1; next }
    in_fm && $0 == "---" { exit }
    in_fm && index($0, key ":") == 1 {
      value = substr($0, length(key) + 2)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
      gsub(/^"|"$/, "", value)
      print value
      exit
    }
  ' "$file"
}

skill_name_for() {
  local skill_id="$1"
  printf 'cortex-%s' "$skill_id" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//'
}

yaml_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

target_for_agent() {
  local name="$1"
  case "$name" in
    codex) printf '%s/skills' "${CODEX_HOME:-$HOME/.codex}" ;;
    claude) printf '%s/skills' "${CLAUDE_HOME:-$HOME/.claude}" ;;
    gemini) printf '%s/skills' "${GEMINI_HOME:-$HOME/.gemini}" ;;
  esac
}

detected_agents() {
  if [[ -n "${CODEX_HOME:-}" || -d "$HOME/.codex" ]]; then echo "codex"; fi
  if [[ -n "${CLAUDE_HOME:-}" || -d "$HOME/.claude" ]]; then echo "claude"; fi
  if [[ -n "${GEMINI_HOME:-}" || -d "$HOME/.gemini" ]]; then echo "gemini"; fi
}

collect_targets() {
  if [[ -n "$target" ]]; then
    echo "${agent}:${target}"
    return
  fi

  case "$agent" in
    auto)
      detected_agents | while read -r detected; do
        [[ -n "$detected" ]] && echo "${detected}:$(target_for_agent "$detected")"
      done
      ;;
    all)
      for name in codex claude gemini; do
        echo "${name}:$(target_for_agent "$name")"
      done
      ;;
    *)
      echo "${agent}:$(target_for_agent "$agent")"
      ;;
  esac
}

write_wrapper() {
  local agent_name="$1"
  local target_root="$2"
  local source_file="$3"

  local skill_id summary model_role status name dest marker wrapper description
  skill_id="$(frontmatter_value "$source_file" skill_id)"
  summary="$(frontmatter_value "$source_file" summary)"
  model_role="$(frontmatter_value "$source_file" model_role)"
  status="$(frontmatter_value "$source_file" status)"

  if [[ -z "$skill_id" ]]; then
    echo "SKIP: $source_file has no skill_id" >&2
    return
  fi

  name="$(skill_name_for "$skill_id")"
  dest="$target_root/$name"
  marker="$dest/.cortex-managed"
  description="Cortex skill ${skill_id}. ${summary} Read the source vault file before acting; updates belong in the Cortex repo."
  description="$(yaml_escape "$description")"

  if [[ -e "$dest" && ! -f "$marker" ]]; then
    echo "SKIP: $dest exists and is not Cortex-managed"
    return
  fi

  echo "DEPLOY: $agent_name $skill_id -> $dest"
  if [[ "$dry_run" -eq 1 ]]; then
    return
  fi

  mkdir -p "$dest"
  cat > "$marker" <<EOF
generated_by=cortex
vault_root=$vault_root
source=$source_file
agent=$agent_name
EOF

  cat > "$dest/SKILL.md" <<EOF
---
name: $name
description: "$description"
---

# Cortex: $skill_id

This is a generated $agent_name wrapper for a Cortex vault skill.

Source of truth: \`$source_file\`
Vault root: \`$vault_root\`
Model role: \`${model_role:-reference}\`
Status: \`${status:-unknown}\`

Before using this skill, read the source file above. For orientation,
read \`$vault_root/skills/meta/index/SKILL.md\`. After learning anything
vault-worthy, follow \`$vault_root/skills/meta/contributing/SKILL.md\`.

Do not edit this generated wrapper directly. Update the source skill in
the Cortex repository, then redeploy wrappers with:

\`\`\`bash
scripts/deploy-skills.sh --agent $agent_name
\`\`\`
EOF
}

mapfile -t targets < <(collect_targets)
if [[ "${#targets[@]}" -eq 0 ]]; then
  echo "ERROR: no agent home detected. Use --agent codex|claude|gemini or --target DIR." >&2
  exit 1
fi

while IFS= read -r -d '' source_file; do
  for entry in "${targets[@]}"; do
    agent_name="${entry%%:*}"
    target_root="${entry#*:}"
    write_wrapper "$agent_name" "$target_root" "$source_file"
  done
done < <(find "$skills_root" -type f -name '*.md' ! -path '*/scripts/*' -print0 | sort -z)
