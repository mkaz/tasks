from appdirs import AppDirs
import argparse
import os
from pathlib import Path
import sys
from typing import Dict


cmds = ["add", "del", "do", "edit", "note", "show"]
VERSION = "2.0.0"


def init_args() -> Dict:
    """Parse and return the arguments."""
    parser = argparse.ArgumentParser(description="task list")
    parser.add_argument("-w", "--week", action="store_true", help="Weekly report")
    parser.add_argument("-i", "--info", action="store_true")
    parser.add_argument("--taskdb", help="SQLite file")
    parser.add_argument("-v", "--version", action="store_true")
    parser.add_argument("command", choices=cmds, nargs="?")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = vars(parser.parse_args())

    if args["version"]:
        print(f"task v{VERSION}")
        sys.exit()

    # if not specified on command-line figure it out
    if args["taskdb"] is None:
        args["taskdb"] = get_taskdb_loc()

    if args["command"] is None:
        args["command"] = "show"

    return args


def get_taskdb_loc() -> str:
    """Figure out where the taskdb file should be.
    See README for spec"""

    # check if tasks.db exists in current dir
    cur_dir = Path(Path.cwd(), "tasks.db")
    if cur_dir.is_file():
        return cur_dir

    # check for env TASKS_DB
    env_var = os.environ.get("TASKS_DB")
    if env_var is not None:
        return env_var

    # Finally use system specific data dir
    dirs = AppDirs("Tasks", "mkaz")

    # No config file, default to data dir
    data_dir = Path(dirs.user_data_dir)
    if not data_dir.is_dir():
        data_dir.mkdir()

    return Path(dirs.user_data_dir, "tasks.db")
