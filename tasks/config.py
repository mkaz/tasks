import argparse
import importlib.metadata
import os
import sys
from pathlib import Path
from typing import Dict

# Define available commands and their descriptions
# Use a dictionary for easier management and help text generation
COMMANDS = {
    "add": "Add a new task.",
    "show": "Show tasks (default command). Filter by status or search term.",
    "edit": "Interactively edit an existing task.",
    "do": "Mark task as done",
}

__version__ = importlib.metadata.version(__package__)


def init_args(skip_local=False) -> Dict:
    """Parse and return the command-line arguments.

    Args:
        skip_local: If True, skip checking for a local tasks.db file (useful for testing)
    """
    parser = argparse.ArgumentParser(
        description="A simple command-line task manager.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global arguments
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
    parser_add.add_argument(
        "-s",
        "--state",
        help="Set the initial state for the task (defaults to Backlog).",
    )
    parser_add.add_argument(
        "-p",
        "--priority",
        type=int,
        choices=range(0, 5),
        metavar="{0-4}",
        help="Set the initial priority (0=highest ... 4=lowest).",
    )

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

    # Edit command
    parser_edit = subparsers.add_parser("edit", help=COMMANDS["edit"])
    parser_edit.add_argument(
        "task_id",
        help="Task ID to edit.",
    )

    # Complete command
    parser_edit = subparsers.add_parser("do", help=COMMANDS["edit"])
    parser_edit.add_argument(
        "task_id",
        help="Task ID to mark complete.",
    )


    # Parse the arguments
    parsed_ns = parser.parse_args()
    parsed_args = vars(parsed_ns)

    # Handle early exit flags
    if parsed_args["version"]:
        print(f"task v{__version__}")
        sys.exit()

    # Set database location
    db_loc = parsed_args["db"] or get_taskdb_loc(skip_local=skip_local)
    parsed_args["db"] = db_loc

    if parsed_args["info"]:
        print(f"Task db: {db_loc}")
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
    return Path.home() / "Documents" / "tasks.db"
