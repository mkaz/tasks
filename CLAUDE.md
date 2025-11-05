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
- Left pane (30%): Shows tasks for current section (Backlog, Now, or Done)
- Right pane (70%): Shows detail view for selected task
- Detail pane includes: task text, priority, state, URL, notes, timestamps
- Detail pane layout stays consistent between read and edit modes (fields just become editable)

### Updated Key Bindings

**Simplified Global Bindings:**
- `q`: Quit application
- `Ctrl+n`: Create new task
- `b`: Cycle through sections (Backlog → Now → Done → Backlog)
- `p`: Switch projects
- `r`: Refresh current section
- `x`: Delete selected task

**Task List Navigation:**
- `↑/↓`: Navigate tasks
- `Enter`: Open selected task for editing in detail pane

**Detail Pane Editing:**
- When you press Enter on a task, detail pane opens in edit mode
- Edit any field: task title, priority (dropdown), URL, notes
- `Tab/Shift+Tab`: Navigate between fields
- `Esc`: Save all changes and return to read mode
- Priority is a dropdown selector - no more +/- shortcuts

**What Changed:**
- Removed all the confusing shortcuts (l/n/d/a, +/-, etc.)
- Single way to edit: Press Enter, edit fields, press Esc to save
- Priority is now a visual dropdown selector
- Much simpler and cleaner workflow

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