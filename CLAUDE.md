# Claude Code Development Notes

## Testing Commands

To test the application during development:

```bash
# IMPORTANT: Don't run `uv run tasks` without arguments in Claude Code
# It launches the kanban TUI which interferes with the Claude interface

# Run with specific commands
uv run tasks add "Add a new task"
uv run tasks show
uv run tasks migrate

# Run tests
uv run pytest
```

## Key Changes Made

### Mode → State Rename
- Renamed database column from `mode` to `state` for better clarity
- Updated all code references, queries, and documentation
- Migration script handles the column rename automatically
- All tests updated to use new terminology

### CLI Simplification
- Default behavior now launches kanban TUI (no arguments needed)
- Removed CLI commands for: edit, priority up/down, mode setting, open URL
- These operations are now TUI-only for better UX
- **IMPORTANT**: Command-line task addition requires explicit "add" command: `uv run tasks add "Task description"`
- Bare strings without commands now show error message instead of creating tasks

### CLI Argument Validation
- Updated config.py to reject bare strings without proper actions
- `uv run tasks "some text"` now shows error instead of creating a task
- Must use `uv run tasks add "some text"` to create tasks
- Provides helpful error message with usage instructions

## Database Migration
The migration script automatically:
1. Detects old `mode` column
2. Recreates table with `state` column
3. Copies all data preserving state values
4. Drops old table

## Development Notes
- Use `uv run` instead of `pip install` for testing during development
- Tests use temporary databases and don't affect real data
- Kanban TUI provides full task management interface