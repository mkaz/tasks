# Task

A simple command-line tool for your task list.

## Data Storage

Data is stored in a SQLite database.

-   Add Schema info

## Install

:shrug-emoji:

## Usage

```
USAGE: task [flags] [command] [id] [text]

COMMANDS:
  add
	  Add new task, [text] required
  done
	  Mark task as done, [id] required
  note
	  Add note to task, [id] and [text] required
  show
	  Show task details, [id] required
  edit
	  Open task in editor, [id] required
  delete
	  Delete task, [id] required
  report
	  Show completed tasks, [+project] optional
```

## Configuration

Task uses a SQLite db to store its data.

By default it will use your system's default data directory. You can override this default using one of the following options:

- Option 1: Use --task-db DIR flag on command-line
- Option 2: Create task.conf in your OS config dir
- Option 3: Create $HOME/.task.conf

The task.conf config file uses TOML format and requires "taskdb" set:

```toml
taskdb='/home/username/Documents/tasks.db'
```

### Contributions and License

Task is open source and free to use, modify, and distribute. It is licensed under the <a rel="license" href="https://opensource.org/licenses/MIT">MIT License</a>.

All contributions are welcome. Use Github issues to report a bug, or submit a feature request. This is just a side project for me, so I may not respond quickly.

An [mkaz](https://mkaz.blog/) contrivance.
