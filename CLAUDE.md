# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

The project uses `just` as the task runner. Key commands:

- `just install` - Install dependencies using uv
- `just test` - Run pytest tests (use `just test tests/test_file.py::test_name` for specific tests)
- `just lint` - Run ruff linting on tasks/ directory
- `just build` - Build the project (runs install first)
- `just run` - Run the CLI application directly. **Note:** Do not run the `kanban` TUI (`just run kanban`) as it interferes with the Gemini CLI.
- `just clean` - Remove build artifacts and Python cache files

For direct pytest usage: `uv run -m pytest` (configured in pyproject.toml with pythonpath="tasks")

## Architecture Overview

This is a command-line todo list application built in Python with SQLite storage:

**Core Components:**
- `tasks/main.py` - Entry point with command routing and handlers
- `tasks/config.py` - Argument parsing, database location logic, and command definitions
- `tasks/task.py` - Task dataclass with CRUD operations and URL parsing
- `tasks/dbactions.py` - Database schema management and query functions
- `tasks/reports.py` - Rich-based display formatting and table generation

**Database Strategy:**
The app uses SQLite with flexible database location logic:
1. `--db DBFILE` command flag
2. `tasks.db` in current directory
3. `TASKS_DB` environment variable
4. OS-specific data directory (via appdirs)

**Key Design Patterns:**
- Tasks have priority (0-4, lower is higher priority), mode (Now/Later), and optional URLs
- Commands are handled via a dictionary mapping in main.py with dedicated handler functions
- Rich library provides colored terminal output with priority-based styling
- URL extraction from task text is automatic using regex in task.py:88-99

**Testing:**
Tests use pytest with mocking for database interactions. The `skip_local` parameter in main() and config functions allows test isolation from local tasks.db files.
