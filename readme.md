
# Task

A -lsimple command-line tool for your task list.

## Data Storage

Data is stored as plain-text files in TOML format. The files can be edited, searched, or managed as any text files, there is no database or stored state outside of the TOML files.

A top level TASKDIR is used, see configuration section below. The files are stored in project directories using their unique task id and state. 

For example, task id 13 in sriracha project is stored at: `TASKDIR/sriracha/13.toml`

When task 13 is marked complete, renamed to: `TASKDIR/sriracha/13.done.toml`

The directory structure, file format, and naming allows for using any set of command-line text processing tools, not just task program.

## Install

Install using `go get github.com/mkaz/task`

or Download from Github releases: https://github.com/mkaz/task/releases

## Configuration

Task requires a directory to be set to store task files

The task directory can be set:
- Option 1: Use `--task-dir DIR` flag on command-line
- Option 2: Create task.conf in `XDG_CONFIG_DIR`
- Option 3: Create `$HOME/.task.conf`

The config file uses TOML format and requires TaskDir set
Example:

	TaskDir='/home/username/Documents/tasks'
 


### Contributions and License

Task is open source and free to use, modify, and distribute. It is licensed under the <a rel="license" href="https://opensource.org/licenses/MIT">MIT License</a>.

I welcome any contributions. Please feel free to open an issue to report a bug, or submit a feature request. Pull requests are also welcome.

An [mkaz](https://mkaz.blog/) contrivance.

