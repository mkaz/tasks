# Project Guidance

Read [`readme.md`](readme.md) first for the project's purpose, installation, CLI behavior, database selection rules, and license. Do not repeat that information here.

## Stack and tooling

- Python 3.12+ package managed with `uv`; metadata and dependencies live in `pyproject.toml`.
- The `tasks` console script calls `tasks.main:main`.
- Runtime libraries: Pydantic for the task model, Rich for output, and prompt-toolkit for interactive editing. SQLite and argparse come from the standard library.
- Use `pytest` for tests and Ruff for linting. Prefer the `justfile` recipes:
  - `just install`
  - `just test` or `just test tests/test_db.py`
  - `just lint`
  - `just build`

## Code map

- `tasks/config.py`: argument parsing, package version, and database path selection.
- `tasks/main.py`: application entry point and command dispatch. It opens the SQLite connection and sets `sqlite3.Row` as the row factory.
- `tasks/db.py`: `TaskDb`, the persistence boundary for schema creation and task queries/mutations.
- `tasks/task.py`: Pydantic `Task` model, `TaskState`, field normalization, and parsing titles/URLs from new entries.
- `tasks/editor.py`: prompt-toolkit interactive edit flow and input validators.
- `tasks/reports.py`: Rich tables and detail/weekly report rendering.
- `tests/conftest.py`: isolated temporary SQLite database fixtures.
- `tests/test_cli.py`: end-to-end command dispatch tests using patched `sys.argv` and stdout.
- `tests/test_db.py` and `tests/test_task.py`: persistence and model/task behavior tests.

## Important behavior and invariants

- Keep the SQLite connection's row factory set to `sqlite3.Row`; `TaskDb` constructs models with `Task(**dict(row))`.
- Active/completed status is determined by `dt_completed`, not by the task's `state`. The schema uses `0` for incomplete rows, while the Pydantic model normalizes `0`, `"0"`, empty strings, and `None` to `None`.
- Marking a task complete sets `dt_completed`; it does not change `state` to `Done`.
- Priorities range from 0 through 4, with lower numbers representing higher priority. Active lists sort by priority and then ID.
- Valid modeled states are `Now`, `Backlog`, `Later`, `Done`, and `Archive`. Keep CLI/editor validation and `TaskState` aligned when changing them.
- Database writes commit on success and roll back on failure. Preserve parameterized SQL for values.
- Schema creation currently happens only when the selected database file does not exist. Account for this when changing startup or migration behavior.
- Importing `tasks.config` reads the installed package version through `importlib.metadata`; run code through the managed environment rather than as an uninstalled source file.

## Making changes

- Keep CLI parsing in `config.py`, orchestration in `main.py`, SQL in `db.py`, and presentation in `reports.py` or `editor.py`.
- Add or update tests for behavior changes. CLI tests must call `main(skip_local=True)` and point `TASKS_DB` at a temporary database so they never touch a user's database.
- Set `sqlite3.Row` on any test connection passed to `TaskDb`.
- Mock `tasks.editor.prompt` for interactive editor tests and `webbrowser.open` for URL-opening behavior.
- Preserve stdout messages and Rich output intentionally; tests and users may depend on command output.
- Before finishing, run the focused tests, then `just test` and `just lint`. Note that `just lint` checks `tasks/`; running Ruff over `tests/` currently reports pre-existing unused imports.
