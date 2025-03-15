#!/usr/bin/env python3
"""
Task
A simple command-line task list.
"""

import readline
import sqlite3
import sys
from pathlib import Path
from typing import List, Optional

# local
import tasks.dbactions as db
import tasks.reports as reports
from tasks.config import init_args


def validate_task_id(task_id: str) -> Optional[int]:
    """Validate and convert task ID string to integer."""
    try:
        return int(task_id)
    except ValueError:
        print(f"> Invalid task id {task_id}")
        return None


def handle_add(conn: sqlite3.Connection, args: List[str]) -> None:
    """Handle the add command."""
    task = " ".join(args)
    task_id = db.insert_task(conn, task)
    print(f"Created Task #{task_id}")


def handle_delete(conn: sqlite3.Connection, args: List[str]) -> None:
    """Handle the delete command."""
    if not args:
        print("> No task id specified.")
        print("> Use: task del ID [ID] [ID]")
        sys.exit(1)

    for arg in args:
        task_id = validate_task_id(arg)
        if task_id is not None:
            db.task_delete(conn, task_id)
            print(f"Task #{task_id} deleted.")


def handle_do(conn: sqlite3.Connection, args: List[str]) -> None:
    """Handle the do command."""
    if not args:
        print("> No task id specified.")
        print("> Use: task do ID [ID] [ID]")
        sys.exit(1)

    for arg in args:
        task_id = validate_task_id(arg)
        if task_id is not None:
            db.mark_done(conn, task_id)
            print(f"Task #{task_id} marked done.")


def handle_edit(conn: sqlite3.Connection, args: List[str]) -> None:
    """Handle the edit command."""
    if len(args) != 1:
        print("> edit command takes a single task id")
        print("> Use: task edit ID")
        sys.exit(1)

    task_id = validate_task_id(args[0])
    if task_id is not None:
        task = db.get_task(conn, task_id)
        if task:
            new_text = input_prefill(f"Update #{task_id}: ", task[1])
            db.task_update(conn, task_id, new_text)
        else:
            print(f"> Task #{task_id} not found")


def handle_show(conn: sqlite3.Connection, week: bool) -> None:
    """Handle the show command."""
    if week:
        new = db.get_tasks_new(conn, days=7)
        com = db.get_tasks_com(conn, days=7)
        reports.show_tasks_week(new, com)
    else:
        tasks = db.get_tasks(conn)
        reports.show_tasks(tasks)


def input_prefill(prompt: str, text: str) -> str:
    """Prefill input with existing text."""
    def hook():
        readline.insert_text(text)
        readline.redisplay()

    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result


def main() -> None:
    """Main entry point for the task application."""
    args = init_args()

    dbfile = Path(args["taskdb"])
    if args["info"]:
        print(f"Using tasks.db {dbfile}")

    # check if taskdb exists
    is_new_db = not dbfile.is_file()

    try:
        # if dbfile did not exist will be created
        conn = sqlite3.connect(dbfile)
        if is_new_db:
            db.create_schema(conn)

        command = args["command"]
        if command == "add":
            handle_add(conn, args["args"])
        elif command == "del":
            handle_delete(conn, args["args"])
        elif command == "do":
            handle_do(conn, args["args"])
        elif command == "edit":
            handle_edit(conn, args["args"])
        elif command == "show":
            handle_show(conn, args["week"])
        else:
            print("Not yet implemented")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
