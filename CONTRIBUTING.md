# Contributing guide

## Branches

- `main`: stable code, ready to deliver.
- `develop`: integration of ongoing work. **All PRs target this branch.**
- `feat/<name>/<task>`: one short-lived branch per task (for example `feat/moni/setup-ci`).

Do not commit directly to `main` or `develop`.

## Workflow

1. Start from an issue with a clear definition of done.
2. Update `develop` and create your branch:
   ```bash
   git switch develop
   git pull --rebase
   git switch -c feat/<name>/<task>
   ```
3. Make small, atomic commits.
4. Before pushing, check that everything passes locally (see [Checks](#checks)).
5. Keep your branch up to date with `develop` using **rebase**, never merge:
   ```bash
   git fetch origin
   git rebase origin/develop
   ```
6. Push the branch and open a PR to `develop`, with the template filled in and the issue linked (`Closes #N`).
7. Wait for CI to pass and for a review. The approval of **one** team member is enough
   (see `.github/CODEOWNERS`). Answer comments with new commits.
8. After the merge, delete the branch.

**Do not use `git push --force`.** If you need to fix something already pushed, add a new commit.

## Commit messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional scope>): <description in imperative mood>
```

| Type | Use |
| --- | --- |
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Add or fix tests |
| `refactor` | Code change that does not alter behavior |
| `chore` | Configuration, dependencies, CI |

Example: `feat(backend): add speaking time metric`.

## Checks

Backend (from `backend/`):

```bash
uv sync
uv run ruff check src/ tests/ scripts/
uv run python -m pytest tests -q
```

Frontend (from `frontend/`, once the project exists):

```bash
pnpm install
pnpm lint
pnpm test
pnpm build
```

## Pull requests

- Small and focused on a single thing (ideally under 400 lines).
- With tests for the new code.
- With the template checklist completed.
- Write the PR title and description in Spanish (the PR template is in Spanish).

## Security

- Never push secrets: `.env`, tokens or credentials. Use environment variables or GitHub Secrets.
- Do not push caches or dependencies (`.venv`, `__pycache__`, `node_modules`). `.gitignore` already excludes them.
- If you push a secret by mistake, tell the team and revoke it immediately: removing it from the history is not enough.
