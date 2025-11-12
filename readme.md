# Tasks

A simple, fast command-line task list for the terminal.

**Note:** This is just a hobby project for personal use, I do not aim to keep compatibility between versions or support in any way. Feel free to use, fork, learn from, but don't be surprised if things break over time. All in the name of learning, experiments, and play.


## Data Storage

Data is stored in a sqlite3 database.

## Install

Install using pip:

```bash
python3 -m pip install git+https://github.com/mkaz/tasks
```

## Usage

Run tasks without any arguments to show your active tasks sorted by priority:

```bash
tasks
```

### Commands

Use the CLI commands for common operations:

```bash
# Add a new task
tasks add "Your task description"
# Add with initial state and priority
tasks add -s Now -p 1 "High priority task"

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

`tasks` without a subcommand is equivalent to `tasks show`. Use `tasks show --week` when you want a report of what was completed recently.

## Configuration

Tasks uses a SQLite db to store its data. The program will look in this order for determining what database file to use. Point different invocations at different DB files if you want separate contexts.

1. If `--db DBFILE` flag on command-line
2. If `tasks.db` file in current directory
3. If environment variable `TASKS_DB` is set
4. Uses your OS data directory

### Why SQLite?

SQLite is a common database format available on all platforms and saves to a single file, this makes it portable and easy to reason about. Additionally, SQLite is extrememly stable, the team has committed to supporting the current API and backwards compatibility to 2050.

### Contributions and License

Tasks is open source and free to use, modify, and distribute. It is licensed under the <a rel="license" href="https://opensource.org/licenses/MIT">MIT License</a>.

An [mkaz](https://mkaz.blog/) contrivance.
