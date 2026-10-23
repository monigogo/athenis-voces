## ¿Qué hace este PR?


## Checklist

- [ ] Rama `feat/<nombre>/<tarea>` (no hago commit directo a `main` ni a `develop`)
- [ ] El PR apunta a `develop`
- [ ] Integro los cambios con `git rebase` (sin merge) y no uso `--force`
- [ ] En `backend/`: `uv run ruff check` y `uv run python -m pytest tests -q` en verde
- [ ] No subo secretos (`.env`) ni ficheros innecesarios (`.venv`, `node_modules`, etc.)
