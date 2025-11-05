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

### Board → Project Rename
- Renamed "boards" to "projects" throughout the codebase
- Database table `boards` migrated to `projects`
- Column `board_id` migrated to `project_id`
- Updated all function names, variables, and UI text

### Notes Field Addition
- Added `notes` field to tasks table for multi-line note-taking
- Migration automatically adds column to existing databases
- Notes are editable in the detail pane

### New UI Layout
- Changed from 3-column kanban view to single-section view with detail pane
- Left pane (30%): Shows tasks for current section (Later, Now, or Done)
- Right pane (70%): Shows detail view for selected task
- Detail pane includes: task text, priority, state, URL, notes, timestamps

### Updated Key Bindings
- `b`: Cycle through sections (Later → Now → Done → Later)
- `p`: Switch projects (formerly `b` for boards)
- `a`: Add new task (creates placeholder, use detail pane to edit)
- `>`: Slide task right (Later → Now → Done → Archive)
- `+/-`: Increase/decrease priority
- `x`: Delete task
- `u`: Undo last delete
- `r`: Refresh current section
- `q`: Quit

**Removed key bindings:**
- `<`: Move left (removed for simplicity)
- `e`: Edit task (now use detail pane)
- `Enter`: Open URL (now done from detail pane)

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
1. Detects old `mode` column and renames to `state`
2. Detects `boards` table and renames to `projects`
3. Detects `board_id` column and renames to `project_id`
4. Adds `notes` column if missing
5. Copies all data preserving values

## Development Notes
- Use `uv run` instead of `pip install` for testing during development
- Tests use temporary databases and don't affect real data
- Kanban TUI provides full task management interface