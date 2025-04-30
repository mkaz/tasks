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
    # "note": "Add a note to a task by ID.", # Not implemented yet
    "show": "Show tasks (default command). Filter by status or search term.",
    "^": "Increase priority of one or more tasks by ID.",
    "v": "Decrease priority of one or more tasks by ID.",
    "mode": "Set the mode (A, B, C) for a task."
}
# cmds = list(COMMANDS.keys()) # No longer needed directly for choices
__version__ = importlib.metadata.version(__package__)


def init_args() -> Dict:
    """Parse and return the command-line arguments."""

    parser = argparse.ArgumentParser(
        description="A simple command-line task manager.",
        # No longer need epilog with command list, subparsers handle this
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-i", "--info", action="store_true", help="Display task database location and version information.")
    parser.add_argument("--taskdb", help="Specify a path to the SQLite database file (overrides default locations).")
    parser.add_argument("--version", "-V", action="store_true", help="Show the application version and exit.") # Changed -v to -V to avoid conflict with subparser 'v'

    subparsers = parser.add_subparsers(dest="command", title="Available commands",
                                       help="Run 'task <command> -h' for more information on a specific command.")
    subparsers.required = False # Allow running 'task' without a command (defaults to show)

    # --- Add command ---
    parser_add = subparsers.add_parser("add", help=COMMANDS["add"])
    parser_add.add_argument("task_description", nargs="+", help="The description of the task to add.")

    # --- Del command ---
    parser_del = subparsers.add_parser("del", help=COMMANDS["del"])
    parser_del.add_argument("task_ids", nargs="+", type=int, help="The ID(s) of the task(s) to delete.")

    # --- Do command ---
    parser_do = subparsers.add_parser("do", help=COMMANDS["do"])
    parser_do.add_argument("task_ids", nargs="+", type=int, help="The ID(s) of the task(s) to mark as done.")

    # --- Edit command ---
    parser_edit = subparsers.add_parser("edit", help=COMMANDS["edit"])
    parser_edit.add_argument("task_id", type=int, help="The ID of the task to edit.")

    # --- Show command ---
    parser_show = subparsers.add_parser("show", help=COMMANDS["show"])
    parser_show.add_argument("-w", "--week", action="store_true", help="Show tasks added or completed in the last week.")
    # Add other show filters later if needed (e.g., search term)

    # --- Priority Up command ---
    parser_prio_up = subparsers.add_parser("^", help=COMMANDS["^"])
    parser_prio_up.add_argument("task_ids", nargs="+", type=int, help="The ID(s) of the task(s) to increase priority for.")

    # --- Priority Down command ---
    parser_prio_down = subparsers.add_parser("v", help=COMMANDS["v"]) # Used 'v' as command name
    parser_prio_down.add_argument("task_ids", nargs="+", type=int, help="The ID(s) of the task(s) to decrease priority for.")

    # --- Mode command ---
    parser_mode = subparsers.add_parser("mode", help=COMMANDS["mode"])
    parser_mode.add_argument("task_id", type=int, help="The ID of the task to set the mode for.")
    parser_mode.add_argument("mode_value", choices=['A', 'B', 'C'], help="The mode to set (A, B, or C).")


    # Manually handle default command 'show' if no command is provided
    # Parse known args first to check for global flags like --version or --taskdb before checking command
    args, unknown = parser.parse_known_args()
    parsed_args = vars(args)

    if parsed_args["version"]:
        print(f"task v{__version__}")
        sys.exit()

    # If no command was explicitly given, default to 'show'
    # Need to re-parse with the default command if necessary
    if parsed_args["command"] is None:
        # Re-parse, inserting 'show' if no command was given
        # This feels a bit hacky, maybe there's a cleaner argparse way?
        # Check if sys.argv contains any known command AFTER the script name
        has_command = any(cmd in COMMANDS for cmd in sys.argv[1:])
        if not has_command:
             # Insert 'show' command if none was provided
             sys.argv.insert(1, 'show')
             parsed_args = vars(parser.parse_args())
        else:
             # A command was likely provided but maybe after an option like --taskdb
             # Reparse all arguments
             parsed_args = vars(parser.parse_args())


    # Default command logic if still None (e.g. just 'task' was run)
    if parsed_args["command"] is None:
        parsed_args["command"] = "show"
        # Ensure 'week' exists for the default show command
        if 'week' not in parsed_args:
            parsed_args['week'] = False # Default value for show command's week arg

    # Handle taskdb location
    if parsed_args["taskdb"] is None:
        parsed_args["taskdb"] = get_taskdb_loc()

    # Convert 'task_description' list to a single string for 'add' command
    if parsed_args["command"] == "add" and "task_description" in parsed_args:
        parsed_args["task_description"] = " ".join(parsed_args["task_description"])

    # For commands expecting list of IDs, ensure the key exists even if parsing fails
    # Although argparse with nargs='+' should handle this. Add safety checks if needed.

    return parsed_args


def get_taskdb_loc() -> Path:
    """Figure out where the taskdb file should be.
    See README for spec"""

    # check if tasks.db exists in current dir
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
