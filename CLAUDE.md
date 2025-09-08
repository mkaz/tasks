# Claude Code Development Notes

## Testing Commands

To test the application during development:

```bash
# Run the application directly with uv
uv run tasks

# Run with specific commands
uv run tasks "Add a new task"
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
- Command-line task addition still works: `uv run tasks "Task description"`

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