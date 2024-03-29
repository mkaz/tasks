# Tasks

A simple command-line tool for your task list.

## Data Storage

Data is stored in a SQLite database.

-   Add Schema info

## Install

Install using pip:

```bash
python3 -m pip install git+https://github.com/mkaz/tasks
```

## Usage

```
USAGE: tasks [flags] [command] [id] [text]

COMMANDS:
  add
	  Add new task, [text] required
  done
	  Mark task as done, [id] ... at least one required
  note
	  Add note to task, [id] and [text] required
  show
	  Show task details, [id] ... at least one required
  edit
	  Open task in editor, [id] required
  delete
	  Delete task, [id] ... at least one required
  report
	  Show completed tasks, [+project] optional
```

## Configuration

Tasks uses a SQLite db to store its data. The program will look in this order for determining what database file to use. Adjust to fit your needs, maybe different databases for differnt projects.

1. If `--taskdb DBFILE` flag on command-line
2. If `tasks.db` file in current directory
3. If environment variable `TASKS_DB` is set
4. Uses your OS data directory

### Why SQLite?

SQLite is a common database format available on all platforms and saves to a single file, this makes it portable and easy to reason about. Additionally, SQLite is extrememly stable, the team has committed to supporting the current API and backwards compatibility to 2050.

### Contributions and License

Tasks is open source and free to use, modify, and distribute. It is licensed under the <a rel="license" href="https://opensource.org/licenses/MIT">MIT License</a>.

This is just a hobby project, if you have any feedback or contributions feel free to use GitHub issues to submit them.

An [mkaz](https://mkaz.blog/) contrivance.
