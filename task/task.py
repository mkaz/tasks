/**
 * Task
 * A simple command-line task list.
 */

version = "2.0.0"

"""
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


CONFIGURATION:

  Task requires a directory to be set to store task files

  The task directory can be set:
	Option 1: Use --task-dir DIR flag on command-line
	Option 2: Create task.conf in XDG_CONFIG_DIR
	Option 3: Create $HOME/.task.conf

  The config file uses TOML format and requires TaskDir set
  Example:
	TaskDir='/home/username/Documents/tasks'
"""

