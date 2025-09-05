import argparse
import importlib.metadata
import os
import sys
from pathlib import Path
from typing import Dict

from appdirs import AppDirs

# Define available commands and their descriptions
# Use a dictionary for easier management and help text generation
COMMANDS = {
    "add": "Add a new task.",
    "del": "Delete one or more tasks by ID.",
    "do": "Mark one or more tasks as done by ID.",
    "edit": "Edit an existing task by ID.",
    "show": "Show tasks (default command). Filter by status or search term.",
    "^": "Increase priority of one or more tasks by ID.",
    "v": "Decrease priority of one or more tasks by ID.",
    "mode": "Set the mode (A, B, C) for a task.",
    "open": "Open the URL associated with a task by ID.",
    "migrate": "Migrate the database schema.",
    "kanban": "Open the kanban board TUI.",
}

__version__ = importlib.metadata.version(__package__)


def init_args(skip_local=False) -> Dict:
    """Parse and return the command-line arguments.

    Args:
        skip_local: If True, skip checking for a local tasks.db file (useful for testing)
    """
    # First check for global flags that cause early exit
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument(
        "--version", action="store_true", help="Show the application version and exit."
    )
    pre_parser.add_argument(
        "--info",
        action="store_true",
        help="Display task database location and version information.",
    )
    pre_parser.add_argument(
        "--db",
        help="Specify a path to the SQLite database file (overrides default locations).",
    )
    pre_args, remaining = pre_parser.parse_known_args()

    # Handle immediate exit flags
    if pre_args.version:
        print(f"task v{__version__}")
        sys.exit()

    # Get the database location before potentially showing info
    db_loc = pre_args.db if pre_args.db else get_taskdb_loc(skip_local=skip_local)

    if pre_args.info:
        print(f"Task db: {db_loc}")
        print(f"Version: v{__version__}")
        sys.exit()

    # Main parser with common arguments for default 'show' command
    parser = argparse.ArgumentParser(
        description="A simple command-line task manager.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Add global arguments and 'show' command arguments to main parser
    parser.add_argument(
        "--db",
        help="Specify a path to the SQLite database file (overrides default locations).",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Display task database location and version information.",
    )
    parser.add_argument(
        "--version", action="store_true", help="Show the application version and exit."
    )

    # Add subparsers
    subparsers = parser.add_subparsers(
        dest="command",
        title="Available commands",
        help="Run 'task <command> -h' for more information on a specific command.",
    )

    # Add command
    parser_add = subparsers.add_parser("add", help=COMMANDS["add"])
    parser_add.add_argument(
        "task_entry", nargs="+", help="The text for the task to add."
    )

    # Del command
    parser_del = subparsers.add_parser("del", help=COMMANDS["del"])
    parser_del.add_argument(
        "task_ids", nargs="+", type=int, help="The ID(s) of the task(s) to delete."
    )

    # Do command
    parser_do = subparsers.add_parser("do", help=COMMANDS["do"])
    parser_do.add_argument(
        "task_ids",
        nargs="+",
        type=int,
        help="The ID(s) of the task(s) to mark as done.",
    )

    # Edit command
    parser_edit = subparsers.add_parser("edit", help=COMMANDS["edit"])
    parser_edit.add_argument("task_id", type=int, help="The ID of the task to edit.")

    # Show command - duplicate the arguments from main parser
    parser_show = subparsers.add_parser("show", help=COMMANDS["show"])
    parser_show.add_argument(
        "-w",
        "--week",
        action="store_true",
        help="Show tasks added or completed in the last week.",
    )
    parser_show.add_argument(
        "--now",
        action="store_true",
        help="Show only tasks with mode 'Now'.",
    )
    parser_show.add_argument(
        "--go",
        action="store_true",
        help="Combined with task_id to open URL in browser.",
    )
    parser_show.add_argument(
        "task_id",
        nargs="?",
        default=[],
        help="Task ID to show details for.",
    )

    # Priority Up command
    parser_prio_up = subparsers.add_parser("^", help=COMMANDS["^"])
    parser_prio_up.add_argument(
        "task_ids",
        nargs="+",
        type=int,
        help="The ID(s) of the task(s) to increase priority for.",
    )

    # Priority Down command
    parser_prio_down = subparsers.add_parser("v", help=COMMANDS["v"])
    parser_prio_down.add_argument(
        "task_ids",
        nargs="+",
        type=int,
        help="The ID(s) of the task(s) to decrease priority for.",
    )

    # Mode command
    parser_mode = subparsers.add_parser("mode", help=COMMANDS["mode"])
    parser_mode.add_argument(
        "task_id", type=int, help="The ID of the task to set the mode for."
    )
    parser_mode.add_argument(
        "mode_value", choices=["Now", "Later"], help="The mode to set (Now, Later)."
    )

    # Open command
    parser_open = subparsers.add_parser("open", help=COMMANDS["open"])
    parser_open.add_argument(
        "task_id", type=int, help="The ID of the task to open the URL for."
    )

    # Migrate command
    subparsers.add_parser("migrate", help=COMMANDS["migrate"])
    
    # Kanban command
    subparsers.add_parser("kanban", help=COMMANDS["kanban"])

    # Parse the arguments
    args_for_main_parser = list(remaining)

    # Prepend 'show' if no command is given or if the first arg is not a command
    # and not requesting help for the main parser.
    if not ("-h" in args_for_main_parser or "--help" in args_for_main_parser):
        if (
            not args_for_main_parser
            or args_for_main_parser[0] not in subparsers.choices
        ):
            args_for_main_parser.insert(0, "show")

    parsed_ns = parser.parse_args(args_for_main_parser)
    parsed_args = vars(parsed_ns)

    # Set database location
    if parsed_args["db"] is None:
        parsed_args["db"] = db_loc

    # Re-check info flag in case it was specified with a command
    if parsed_args["info"]:
        print(f"Task db: {parsed_args['db']}")
        print(f"Version: v{__version__}")
        sys.exit()

    # Convert 'task_description' list to a single string for 'add' command
    if parsed_args["command"] == "add" and "task_entry" in parsed_args:
        parsed_args["task_entry"] = " ".join(parsed_args["task_entry"])

    return parsed_args


def get_taskdb_loc(skip_local=False) -> Path:
    """Figure out where the taskdb file should be.
    See README for spec

    Args:
        skip_local: If True, skip checking for a local tasks.db file (useful for testing)
    """

    # check if tasks.db exists in current dir
    if not skip_local:
        cur_dir = Path(Path.cwd(), "tasks.db")
        if cur_dir.is_file():
            return cur_dir

    # check for env TASKS_DB
    env_var = os.environ.get("TASKS_DB")
    if env_var is not None:
        return Path(env_var)

    # Finally use system specific data dir
    dirs = AppDirs("Tasks", "mkaz")

    # No config file, default to data dir
    data_dir = Path(dirs.user_data_dir)
    if not data_dir.is_dir():
        data_dir.mkdir()

    return Path(dirs.user_data_dir, "tasks.db")
