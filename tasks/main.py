"""
Task
A simple command-line task list.
"""

import sqlite3
import webbrowser
from pathlib import Path

# local
from . import reports
from .config import init_args
from .editor import edit_task
from .db import TaskDb


def main(skip_local=False) -> None:
    """Main entry point for the task application.

    Args:
        skip_local: If True, skip checking for a local tasks.db file (useful for testing)
    """
    args = init_args(skip_local=skip_local)

    dbfile = Path(args["db"])
    if args["info"]:
        print(f"Using tasks.db {dbfile}")

    # check if taskdb exists
    is_new_db = not dbfile.is_file()

    # if dbfile did not exist will be created
    with sqlite3.connect(dbfile) as conn:
        conn.row_factory = sqlite3.Row
        task_db = TaskDb(conn)
        if is_new_db:
            task_db.create_schema()

        command = args["command"] or "show"

        # Command handler mapping
        command_handlers = {
            "add": handle_add,
            "show": handle_show,
            "edit": handle_edit,
            "do": handle_complete,
        }

        handler = command_handlers.get(command)
        if handler:
            handler(task_db, args)
        else:
            print(f"Unknown or unimplemented command: {command}")


def handle_add(db: TaskDb, args: dict) -> None:
    """Handle the add command."""
    task_id = db.create_task(args)
    if task_id:
        print(f"Created Task #{task_id}")
    else:
        print("Error: Could not create task.")


def handle_show(db: TaskDb, args: dict) -> None:
    """Handle the show command."""
    if args.get("week"):
        new = db.get_tasks_new(days=7)
        com = db.get_tasks_com(days=7)
        reports.show_tasks_week(new, com)
    elif args.get("task_id"):
        task = db.get_task(args["task_id"])
        if task is None:
            print(f"Task not found: {args.get('task_id')}")
            return
        reports.show_task_details(task)
        ## check for go flag to open URL
        if args.get("go") and task.url:
            webbrowser.open(task.url)
    elif args.get("now"):
        tasks = db.get_tasks_by_state("Now")
        reports.show_tasks(tasks)
    else:
        tasks = db.get_tasks()
        reports.show_tasks(tasks)


def handle_edit(db: TaskDb, args: dict) -> None:
    """Handle the edit command."""
    task_id = args.get("task_id")
    if not task_id:
        print("Error: Task ID required.")
        return

    try:
        task_id = int(task_id)
    except ValueError:
        print("Error: Task ID must be a number.")
        return

    task = db.get_task(task_id)
    if not task:
        print(f"No task found with ID {task_id}.")
        return

    edit_task(db, task)


def handle_complete(db: TaskDb, args: dict) -> None:
    """Handle the complete command."""
    task_id = args.get("task_id")
    if not task_id:
        print("Error: Task ID required.")
        return

    try:
        task_id = int(task_id)
    except ValueError:
        print("Error: Task ID must be a number.")
        return

    task = db.get_task(task_id)
    if not task:
        print(f"No task found with ID {task_id}.")
        return

    if db.mark_task_done(task.id):
        print(f"Task {task.id} marked complete.")
    else:
        print(f"Error: Could not mark task {task.id} complete.")


if __name__ == "__main__":
    main()
