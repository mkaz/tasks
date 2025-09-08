# Tasks

A simple task management tool with an interactive kanban board and command-line interface.

## Data Storage

Data is stored in a SQLite database.

-   Add Schema info

## Install

Install using pip:

```bash
python3 -m pip install git+https://github.com/mkaz/tasks
```

## Usage

### Interactive Kanban Board (Primary Interface)

Run tasks without any arguments to launch the interactive kanban board:

```bash
tasks
```

The kanban TUI provides full task management including:
- Creating, editing, and deleting tasks
- Moving tasks between states (Todo, Now, Done)
- Setting priorities
- Adding notes and URLs
- Undo functionality

### Command Line Interface

For quick operations, use these commands:

```bash
# Add a new task
tasks add "Your task description"

# Mark tasks as complete
tasks do 1 2 3

# Delete tasks
tasks del 1 2 3

# Show all tasks
tasks show

# Show tasks from the last week
tasks show --week

# Show only "Now" tasks
tasks show --now

# Show specific task details
tasks show 5

# Migrate database schema
tasks migrate
```

**Note**: Task descriptions must be quoted and use the explicit `add` command. Running `tasks "some text"` without the `add` command will show an error.

## Configuration

Tasks uses a SQLite db to store its data. The program will look in this order for determining what database file to use. Adjust to fit your needs, maybe different databases for differnt projects.

1. If `--db DBFILE` flag on command-line
2. If `tasks.db` file in current directory
3. If environment variable `TASKS_DB` is set
4. Uses your OS data directory

### Why SQLite?

SQLite is a common database format available on all platforms and saves to a single file, this makes it portable and easy to reason about. Additionally, SQLite is extrememly stable, the team has committed to supporting the current API and backwards compatibility to 2050.

### Contributions and License

Tasks is open source and free to use, modify, and distribute. It is licensed under the <a rel="license" href="https://opensource.org/licenses/MIT">MIT License</a>.

This is just a hobby project, if you have any feedback or contributions feel free to use GitHub issues to submit them.

An [mkaz](https://mkaz.blog/) contrivance.
