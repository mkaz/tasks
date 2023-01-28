from appdirs import AppDirs
import argparse
from pathlib import Path
import sys
import toml
from typing import Dict


cmds = ["add", "done", "note", "show", "edit", "delete", "report"]
VERSION = "2.0.0"


def init_args() -> Dict:
    """Parse and return the arguments."""
    parser = argparse.ArgumentParser(description="task list")
    parser.add_argument("-i", "--info", action="store_true")
    parser.add_argument("--taskdb", help="SQLite file")
    parser.add_argument("-v", "--version", action="store_true")
    parser.add_argument("command", choices=cmds)
    parser.add_argument("args", nargs="*")
    args = vars(parser.parse_args())

    if args["version"]:
        print("task v{}".format(VERSION))
        sys.exit()

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
