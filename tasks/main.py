#!/usr/bin/env python3
"""
Task
A simple command-line task list.
"""

import sqlite3
import sys
from pathlib import Path
from prompt_toolkit import prompt
from typing import List, Optional

# local
import tasks.dbactions as db
import tasks.reports as reports
from tasks.config import init_args


def handle_add(conn: sqlite3.Connection, task_description: str) -> None:
    """Handle the add command."""
    task_id = db.insert_task(conn, task_description)
    print(f"Created Task #{task_id}")


def handle_delete(conn: sqlite3.Connection, task_ids: List[int]) -> None:
    """Handle the delete command."""
    for task_id in task_ids:
        db.task_delete(conn, task_id)
        print(f"Task #{task_id} deleted.")


def handle_do(conn: sqlite3.Connection, task_ids: List[int]) -> None:
    """Handle the do command."""
    for task_id in task_ids:
        db.mark_done(conn, task_id)
        print(f"Task #{task_id} marked done.")


def handle_edit(conn: sqlite3.Connection, task_id: int) -> None:
    """Handle the edit command."""
    task = db.get_task(conn, task_id)
    if task:
        new_text = input_prefill(f"Update #{task_id}: ", task[1])
        if new_text:
            db.task_update(conn, task_id, new_text)
        else:
            print("Edit cancelled.")
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


def input_prefill(prompt_str: str, text: str) -> str:
    """Prefill input with existing text."""
    try:
        result = prompt(prompt_str, default=text, auto_suggest=None)
        return result
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled")
        sys.exit(1)


def handle_priority_change(
    conn: sqlite3.Connection, task_ids: List[int], increase: bool
) -> None:
    """Handle priority change commands (^ or v)."""
    for task_id in task_ids:
        if increase:
            db.increase_priority(conn, task_id)
            print(f"Task #{task_id} priority increased.")
        else:
            db.decrease_priority(conn, task_id)
            print(f"Task #{task_id} priority decreased.")


def handle_mode(conn: sqlite3.Connection, task_id: int, mode: str) -> None:
    """Handle the mode command to set task mode."""
    try:
        db.set_task_mode(conn, task_id, mode)
        print(f"Task #{task_id} mode set to {mode}")
    except ValueError as e:
        print(f"> {e}")


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
        else:
            # Migrate existing database if needed
            db.migrate_schema(conn)

        command = args["command"]
        if command == "add":
            handle_add(conn, args["task_description"])
        elif command == "del":
            handle_delete(conn, args["task_ids"])
        elif command == "do":
            handle_do(conn, args["task_ids"])
        elif command == "edit":
            handle_edit(conn, args["task_id"])
        elif command == "show":
            handle_show(conn, args["week"])
        elif command == "^":
            handle_priority_change(conn, args["task_ids"], True)
        elif command == "v":
            handle_priority_change(conn, args["task_ids"], False)
        elif command == "mode":
            handle_mode(conn, args["task_id"], args["mode_value"])
        elif command is None:
             handle_show(conn, args["week"])
        else:
             print(f"Unknown or unimplemented command: {command}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
