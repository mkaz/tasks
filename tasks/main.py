#!/usr/bin/env python3
"""
Task
A simple command-line task list.
"""

import sqlite3
import sys
from pathlib import Path
from prompt_toolkit import prompt
from typing import Optional
import webbrowser

# local
import tasks.dbactions as db
import tasks.reports as reports
from tasks.config import init_args
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

        command = args["command"]

        # Command handler mapping
        command_handlers = {
            "add": handle_add,
            "del": handle_del,
            "do": handle_do,
            "show": handle_show,
            "migrate": lambda c, a: db.migrate_schema(c),
            None: handle_kanban,
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


def handle_del(conn: sqlite3.Connection, args: dict) -> None:
    """Handle the delete command."""
    for task_id in args["task_ids"]:
        task = db.get_task(conn, task_id)
        if task:
            task.delete(conn)
            print(f"Task #{task_id} deleted.")
        else:
            print(f"> Task #{task_id} not found for deletion.")


def handle_do(conn: sqlite3.Connection, args: dict) -> None:
    """Handle the do command."""
    for task_id in args["task_ids"]:
        task = db.get_task(conn, task_id)
        if task:
            task.mark_done(conn)
            print(f"Task #{task_id} marked done.")
        else:
            print(f"> Task #{task_id} not found to mark as done.")




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
        tasks = db.get_tasks_by_mode(conn, "Now")
        reports.show_tasks(tasks)
    else:
        tasks = db.get_tasks(conn)
        reports.show_tasks(tasks)


def input_prefill(prompt_str: str, text: Optional[str]) -> str:
    """Prefill input with existing text."""
    try:
        # Convert None to empty string to avoid length errors
        default_text = "" if text is None else text
        result = prompt(prompt_str, default=default_text, auto_suggest=None)
        return result
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled")
        sys.exit(1)






def handle_kanban(conn: sqlite3.Connection, args: dict) -> None:
    """Handle the kanban command to open the kanban board TUI."""
    conn.close()  # Close the connection as kanban will create its own
    from tasks.kanban import run_kanban
    run_kanban()


if __name__ == "__main__":
    main()
