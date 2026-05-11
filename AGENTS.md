# Scope

- These instructions apply to the entire `ai-github-action` repository.
- This repo is a Docker-based GitHub Action that runs Python 3.12 code from `src/` using metadata from `action.yml`.

# Layout

- `action.yml` defines the public GitHub Action inputs and maps them into container environment variables.
- `Dockerfile` builds the action runtime.
- `src/main.py` is the action entrypoint.
- `src/actions/` contains action-type orchestration for PR review, issue analysis, and code scanning.
- `src/github_agents/` contains OpenAI Agents SDK implementations.
- `src/context/` and `src/tools/` isolate GitHub event parsing and GitHub API tool functions.
- `tests/` mirrors the runtime behavior with pytest coverage.

# Change Guidelines

- Keep the public action contract in `action.yml`, `README.md`, and runtime environment handling aligned.
- Preserve the separation between action orchestration, agent behavior, GitHub context parsing, and GitHub API tools.
- Use narrow Python types where practical and keep interfaces simple.
- Add or update docstrings for new or modified Python code, including tests when the purpose is not obvious.
- Prefer small, focused changes; avoid unrelated formatting or refactors.
- Keep Python style compatible with the existing Ruff, mypy, and Python 3.12 configuration in `pyproject.toml`.

# Validation

- Install/update dependencies with `make sync` when dependency state may be stale.
- Run `make lint` after Python changes.
- Run `make mypy` after changing typed interfaces or shared modules.
- Run `make tests` for behavior changes.
- For changes to action inputs, defaults, or documented usage, also inspect `action.yml` and `README.md` together for drift.
