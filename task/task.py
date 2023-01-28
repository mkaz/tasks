#!/usr/bin/env python3
"""
Task
A simple command-line task list.
"""
from appdirs import AppDirs
import argparse
from pathlib import Path
import sqlite3
import sys
import toml
from typing import Dict

VERSION = "2.0.0"

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

  Task uses a SQLite db to store its data.

  By default it will use your system's default data directory.
  You can override this default using:

      Option 1: Use --task-db DIR flag on command-line
      Option 2: Create task.conf in your OS config dir
      Option 3: Create $HOME/.task.conf

  The task.conf config file uses TOML format and requires taskdb set
  Example:
    taskdb='/home/username/Documents/tasks.db'
"""

cmds = ["add", "done", "note", "show", "edit", "delete", "report"]


def main():
    args = init_args()
    if args["version"]:
        print("task v{}".format(VERSION))
        sys.exit()

    dbfile = Path(args["taskdb"])
    if args["info"]:
        print(f"Using tasks.db {dbfile}")

    # check if taskdb exists
    create_schema = not dbfile.is_file()

    con = sqlite3.connect(dbfile)
    cur = con.cursor()
    if create_schema:
        cur.execute("CREATE TABLE tasks (task TEXT, completed, dt_created) ")


def init_args() -> Dict:
    """Parse and return the arguments."""
    parser = argparse.ArgumentParser(description="task list")
    parser.add_argument("-i", "--info", action="store_true")
    parser.add_argument("--taskdb", help="SQLite file")
    parser.add_argument("-v", "--version", action="store_true")
    parser.add_argument("command", choices=cmds)
    args = vars(parser.parse_args())

    if args["taskdb"] is None:
        args["taskdb"] = get_taskdb_loc()

    return args


def get_taskdb_loc() -> str:
    """Figure out where the taskdb file should be"""

    # System specific directories
    dirs = AppDirs("Task", "mkaz")

    # check if task.conf exists
    config_file = Path(dirs.user_config_dir, "task.conf")
    if not config_file.is_file():
        config_file = Path(Path.home(), ".task.conf")

    if config_file.is_file():
        config_text = config_file.read_text()
        config = toml.loads(config_text)
        return config["taskdb"]

    # No config file, default to data dir
    data_dir = Path(dirs.user_data_dir)
    if not data_dir.is_dir():
        data_dir.mkdir()

    return Path(dirs.user_data_dir, "tasks.db")


if __name__ == "__main__":
    main()
