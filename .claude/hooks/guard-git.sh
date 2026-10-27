#!/usr/bin/env bash
# PreToolUse (Bash): bloquea acciones git que rompen las reglas de contribución.
entrada=$(cat)
if command -v jq >/dev/null 2>&1; then
  cmd=$(jq -r '.tool_input.command // ""' <<<"$entrada")
else
  # Sin jq se saca la orden a mano: dejar pasar todo sería peor que leerla con menos precisión
  cmd=$(sed -zE 's/.*"command"[[:space:]]*:[[:space:]]*"(.*)"[[:space:]]*}[[:space:]]*}[[:space:]]*$/\1/;s/\\"/"/g' <<<"$entrada")
fi

deny() { echo "Bloqueado: $1" >&2; exit 2; }

cmd_sin_example=$(sed -E 's/(^|[ /])\.env\.example([ /]|$)/\1\2/g' <<<"$cmd")
grep -qE 'git +(add|commit)' <<<"$cmd" && grep -qE '(^|[ /])\.env(\.[A-Za-z0-9_-]+)?( |$)' <<<"$cmd_sin_example" \
  && deny "no se suben ficheros .env (secretos). .env.example sí está permitido."

# Solo la parte del push: un «rm -rf» en la misma línea no es forzar
push=$(grep -oE 'git +push[^;&|]*' <<<"$cmd")
if [ -n "$push" ]; then
  grep -qE '(--force(-with-lease)?(=[^ ]*)?( |$)|(^| )-[a-zA-Z]*f[a-zA-Z]*( |$)|( |:)\+[^ ]+)' <<<"$push" \
    && deny "nunca se fuerza un push: si hay que corregir algo ya subido, haz un commit nuevo."
  grep -qE '(origin +|:)(main|develop)( |$)' <<<"$push" \
    && deny "no se hace push directo a main/develop: usa una rama y una PR."
fi

# Solo el mensaje del commit, lo que va desde «git commit»: el nombre de un fichero no cuenta
if grep -qE 'git +commit' <<<"$cmd"; then
  mensaje=$(sed -zE 's/.*git +commit//' <<<"$cmd" | sed 's/\.claude//g')
  grep -qiE 'co-authored-by|generated with|anthropic|claude' <<<"$mensaje" \
    && deny "el mensaje de commit no debe mencionar IA/Claude ni llevar trailers."
fi
exit 0
