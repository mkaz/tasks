
# Task

A simple command-line tool for task management.

## Data Storage

Data is stored as plain-text files in TOML format. The files can be edited, searched, or managed as any text files, there is no database or stored state outside of the TOML files.

A top level TASKDIR is used, see configuration section below. The files are stored in project directories using their unique task id and state. 

For example, task id 13 in sriracha project is stored at: `TASKDIR/sriracha/13.toml`

When task 13 is marked complete, renamed to: `TASKDIR/sriracha/13.done.toml`

The directory structure, file format, and naming allows for using any set of command-line text processing tools, not just task program.

## Install

Install using `go get github.com/mkaz/task`

## Configuration

Task requires a directory to be set to store task files

The task directory can be set:
- Option 1: Use --task-dir DIR flag on command-line
- Option 2: Create task.conf in XDG_CONFIG_DIR
- Option 3: Create $HOME/.task.conf

The config file uses TOML format and requires TaskDir set
Example:

	TaskDir='/home/username/Documents/tasks'
 


### License

Task is open source and free to use, it is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>.

I welcome any contributions. Please feel free to open an issues to report a bug, submit a feature. Pull requests are also welcome.

An [mkaz](https://mkaz.blog/) contrivance.

