#!/usr/bin/env bash
# PreToolUse (Bash): bloquea acciones git que rompen las reglas de contribución.
cmd=$(jq -r '.tool_input.command // ""')

deny() { echo "Bloqueado: $1" >&2; exit 2; }

cmd_sin_example=$(sed -E 's/(^|[ /])\.env\.example([ /]|$)/\1\2/g' <<<"$cmd")
grep -qE 'git +(add|commit)' <<<"$cmd" && grep -qE '(^|[ /])\.env(\.[A-Za-z0-9_-]+)?( |$)' <<<"$cmd_sin_example" \
  && deny "no se suben ficheros .env (secretos). .env.example sí está permitido."
grep -qE 'git +push' <<<"$cmd" && grep -qE '(--force(-with-lease)?(=[^ ]*)?( |$)|-f( |$))' <<<"$cmd" \
  && deny "nunca se fuerza un push: si hay que corregir algo ya subido, haz un commit nuevo."
grep -qE 'git +push' <<<"$cmd" && grep -qE '(origin +|:)(main|develop)( |$)' <<<"$cmd" \
  && deny "no se hace push directo a main/develop: usa una rama y una PR."
grep -qE 'git +commit' <<<"$cmd" && sed 's/\.claude//g' <<<"$cmd" | grep -qiE 'co-authored-by|generated with|anthropic|claude' \
  && deny "el mensaje de commit no debe mencionar IA/Claude ni llevar trailers."
exit 0
