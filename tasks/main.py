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
import webbrowser

# local
import tasks.dbactions as db
import tasks.reports as reports
from tasks.config import init_args


def main() -> None:
    """Main entry point for the task application."""
    args = init_args()

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
        match command:
            case "add":
                handle_add(conn, args)
            case "del":
                handle_delete(conn, args)
            case "do":
                handle_do(conn, args)
            case "edit":
                handle_edit(conn, args)
            case "show":
                handle_show(conn, args)
            case "^":
                handle_priority_change(conn, args, True)
            case "v":
                handle_priority_change(conn, args, False)
            case "mode":
                handle_mode(conn, args)
            case "open":
                handle_open(conn, args)
            case "migrate":
                db.migrate_schema(conn)
            case None:
                handle_show(conn, args)
            case _:
                print(f"Unknown or unimplemented command: {command}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    finally:
        conn.close()


def handle_add(conn: sqlite3.Connection, args: dict) -> None:
    """Handle the add command."""
    task_id = db.insert_task(conn, args["task_description"])
    print(f"Created Task #{task_id}")


def handle_delete(conn: sqlite3.Connection, args: dict) -> None:
    """Handle the delete command."""
    for task_id in args["task_ids"]:
        db.task_delete(conn, task_id)
        print(f"Task #{task_id} deleted.")


def handle_do(conn: sqlite3.Connection, args: dict) -> None:
    """Handle the do command."""
    for task_id in args["task_ids"]:
        db.mark_done(conn, task_id)
        print(f"Task #{task_id} marked done.")


def handle_edit(conn: sqlite3.Connection, args: dict) -> None:
    """Handle the edit command."""
    task = db.get_task(conn, args["task_id"])
    if task:
        new_text = input_prefill(
            f"Update Task Description for #{args['task_id']}: ", task["task"]
        )
        new_url = input_prefill(
            f"Update URL for #{args['task_id']} (current: {task['url']}): ",
            task["url"] or "",
        )

        if new_text is not None:  # Check if new_text is not None (i.e., not cancelled)
            db.task_update(
                conn,
                args["task_id"],
                new_text,
                new_url if new_url is not None else task["url"],
            )
            print(f"Task #{args['task_id']} updated.")
        else:
            print("Edit cancelled.")
    else:
        print(f"> Task #{args['task_id']} not found")


def handle_show(conn: sqlite3.Connection, args: dict) -> None:
    """Handle the show command."""
    if args.get("week"):
        new = db.get_tasks_new(conn, days=7)
        com = db.get_tasks_com(conn, days=7)
        reports.show_tasks_week(new, com)
    elif args.get("task_id"):
        task = db.get_task(conn, args["task_id"])
        reports.show_task_details(task)
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
    conn: sqlite3.Connection, args: dict, increase: bool
) -> None:
    """Handle priority change commands (^ or v)."""
    for task_id in args["task_ids"]:
        if increase:
            db.increase_priority(conn, task_id)
            print(f"Task #{task_id} priority increased.")
        else:
            db.decrease_priority(conn, task_id)
            print(f"Task #{task_id} priority decreased.")


def handle_mode(conn: sqlite3.Connection, args: dict) -> None:
    """Handle the mode command to set task mode."""
    try:
        db.set_task_mode(conn, args["task_id"], args["mode_value"])
        print(f"Task #{args['task_id']} mode set to {args['mode_value']}")
    except ValueError as e:
        print(f"> {e}")


def handle_open(conn: sqlite3.Connection, args: dict) -> None:
    """Handle the open command to open the URL of a task."""
    task = db.get_task(conn, args["task_id"])
    if task:
        if task["url"]:
            print(f"Opening URL for Task #{args['task_id']}: {task['url']}")
            webbrowser.open(task["url"])
        else:
            print(f"> Task #{args['task_id']} has no URL.")
    else:
        print(f"> Task #{args['task_id']} not found.")


if __name__ == "__main__":
    main()
