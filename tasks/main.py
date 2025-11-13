#!/usr/bin/env python3
"""
Task
A simple command-line task list.
"""

import sqlite3
from pathlib import Path

# local
import tasks.dbactions as db
import tasks.reports as reports
from tasks.config import init_args
from tasks.editor import edit_task_interactive
from tasks.task import Task


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

    try:
        # if dbfile did not exist will be created
        conn = sqlite3.connect(dbfile)
        conn.row_factory = sqlite3.Row

        if is_new_db:
            db.create_schema(conn)

        command = args["command"] or "show"

        # Command handler mapping
        command_handlers = {
            "add": handle_add,
            "show": handle_show,
            "edit": handle_edit,
            "migrate": lambda c, a: db.migrate_schema(c),
        }

        handler = command_handlers.get(command)
        if handler:
            handler(conn, args)
        else:
            print(f"Unknown or unimplemented command: {command}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


def handle_add(conn: sqlite3.Connection, args: dict) -> None:
    """Handle the add command."""
    task_id = Task.create(conn, args)
    if task_id:
        print(f"Created Task #{task_id}")
    else:
        print("Error: Could not create task.")


def handle_show(conn: sqlite3.Connection, args: dict) -> None:
    """Handle the show command."""
    if args.get("week"):
        new = db.get_tasks_new(conn, days=7)
        com = db.get_tasks_com(conn, days=7)
        reports.show_tasks_week(new, com)
    elif args.get("task_id"):
        task = db.get_task(conn, args["task_id"])
        reports.show_task_details(task)
    elif args.get("now"):
        tasks = db.get_tasks_by_state(conn, "Now")
        reports.show_tasks(tasks)
    else:
        tasks = db.get_tasks(conn)
        reports.show_tasks(tasks)


def handle_edit(conn: sqlite3.Connection, args: dict) -> None:
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

    task = db.get_task(conn, task_id)
    if not task:
        print(f"No task found with ID {task_id}.")
        return

    edit_task_interactive(conn, task)


if __name__ == "__main__":
    main()
