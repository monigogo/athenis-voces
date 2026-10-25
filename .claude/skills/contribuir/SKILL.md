---
name: contribuir
description: Procedimiento de contribución del equipo para subir o compartir cambios. Úsalo cuando el usuario quiera hacer un commit, un push o abrir una PR, por ejemplo "vamos a subir estos cambios", "quiero hacer un commit", "sube esto", "hazme commit y push", "abre una PR", "subo esto a develop".
---

# Contribuir: subir cambios a develop

Sigue estos pasos en orden. Todas las PRs van contra `develop`. Detalle completo en `CONTRIBUTING.md`.

## Reglas inquebrantables

- **Nunca** subas secretos: `.env`, `.env.*`, tokens o credenciales.
- **Nunca** hagas push con ruff o tests fallando.
- **Nunca** hagas commit ni push directo a `main` o `develop`.

## Paso 1: rama correcta

1. `git branch --show-current` y `git status --short`.
2. Si estás en `main` o `develop`, crea una rama con `git switch -c feat/<nombre>/<tarea>` (ej. `feat/moni/setup-ci`; usa `chore/`, `fix/`, `docs/` según el cambio). Los cambios sin commitear se mueven con la rama.

## Paso 2: qué se sube

1. Revisa `git status` y `git diff`. Añade solo ficheros relevantes, por nombre (nunca `git add -A` a ciegas).
2. Excluye siempre: `.env`, `.env.*`, `.venv/`, `__pycache__/`, `node_modules/`, caches, y ficheros scratch (notas, volcados, `tmp*`, `*.log`, salidas de prueba).
3. Si dudas de un fichero, pregunta al usuario.

## Paso 3: ruff + tests

Desde `backend/`:

```bash
uv run ruff check src/ tests/ scripts/
uv run ruff format --check src/ tests/ scripts/
uv run python -m pytest tests -q
```

Si hay cambios en `frontend/` (cuando exista el proyecto): `pnpm lint`, `pnpm test`, `pnpm build`.

Si algo falla: **para**, enseña el error al usuario y ofrécete a arreglarlo (`ruff format` y `ruff check --fix` para lo automático). No continúes hasta que todo pase.

## Paso 4: sincronizar con develop

```bash
git fetch origin
git rebase origin/develop
```

- Conflictos pequeños: resuélvelos y explica al usuario qué cambiaste.
- Conflictos grandes o dudas: `git rebase --abort` y avisa al usuario para pedir ayuda.
- La rama es pequeña a propósito: el rebase debería ser trivial.
- Anota si hubo rebase real (hace falta `--force-with-lease` en el paso 7).

## Paso 5: preparar el commit

- Un solo commit con todo el cambio.
- Formato Conventional Commits: `<tipo>(<scope opcional>): <descripción>`.
- Tipos: `fix`, `feat`, `chore`, `docs`, `test`, `refactor`.
- Mensaje en español, claro, en imperativo. Ej.: `feat(backend): añadir métrica de tiempo de habla`.

## Paso 6: enseñar el diff y pedir OK

Muestra `git diff --stat` (sobre lo que se va a commitear) y el mensaje de commit propuesto. **Espera confirmación explícita del usuario.** Esta es la única parada del procedimiento; antes y después, sigue sin preguntar.

## Paso 7: push + PR

1. `git commit` con el mensaje aprobado.
2. `git push -u origin <rama>`; si rebasaste de verdad, `git push -u origin <rama> --force-with-lease`. Nunca `--force` a secas.
3. Abre la PR contra `develop` (`gh pr create --base develop`; si `gh` no está disponible, da el enlace `https://github.com/<org>/<repo>/compare/develop...<rama>?expand=1`).
   - Título y descripción en español, siguiendo la plantilla de `.github/`.
   - Enlaza la issue con `Closes #N` si la hay.
4. Termina avisando al usuario con el número de PR: "sigo con la PR #N".
