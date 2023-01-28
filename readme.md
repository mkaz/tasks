# Task

A simple command-line tool for your task list.

## Data Storage

Data is stored in a SQLite database.

-   Add Schema info

## Install

:shrug-emoji:


## Configuration

Task requires a directory to be set to store task files

The task directory can be set:

-   Option 1: Use `--task-db FILE` flag on command-line
-   Option 2: Create task.conf in `XDG_CONFIG_DIR`
-   Option 3: Create `$HOME/.task.conf`

The config file uses TOML format and requires TaskDB set

Example:

    TaskDB='/home/username/Documents/tasks.db'

### Contributions and License

Task is open source and free to use, modify, and distribute. It is licensed under the <a rel="license" href="https://opensource.org/licenses/MIT">MIT License</a>.

All contributions are welcome. Use Github issues to report a bug, or submit a feature request. This is just a side project for me, so I may not respond quickly.

An [mkaz](https://mkaz.blog/) contrivance.
