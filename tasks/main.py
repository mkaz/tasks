#!/usr/bin/env python3
"""
Task
A simple command-line task list.
"""

import readline
import sqlite3
import sys
from pathlib import Path

# local
import tasks.dbactions as db
import tasks.reports as reports
from tasks.config import init_args


def main():
    args = init_args()

    dbfile = Path(args["taskdb"])
    if args["info"]:
        print(f"Using tasks.db {dbfile}")

    # check if taskdb exists
    is_new_db = not dbfile.is_file()

    # if dbfile did not exist will be created
    conn = sqlite3.connect(dbfile)
    if is_new_db:
        db.create_schema(conn)

    match args["command"]:
        case "add":
            task = " ".join(args["args"])
            task_id = db.insert_task(conn, task)
            print(f"Created Task #{task_id}")

        case "del":
            # check we have arguments
            if len(args["args"]) < 0:
                print("> No task id specified.")
                print("> Use: task do ID [ID] [ID]")
                sys.exit(1)
            for arg in args["args"]:
                # check arg is an int
                try:
                    task_id = int(arg)
                    db.task_delete(conn, task_id)
                    print(f"Task #{task_id} deleted.")
                except ValueError:
                    print(f"> Invalid task id {task_id}")
                    print(f"> Variable is type {type(task_id)}")

        case "do":
            # check we have arguments
            if len(args["args"]) < 0:
                print("> No task id specified.")
                print("> Use: task do ID [ID] [ID]")
                sys.exit(1)
            for arg in args["args"]:
                # check arg is an int
                try:
                    task_id = int(arg)
                    db.mark_done(conn, task_id)
                    print(f"Task #{task_id} marked done.")
                except ValueError:
                    print(f"> Invalid task id {task_id}")
                    print(f"> Variable is type {type(task_id)}")
        case "edit":
            if len(args["args"]) != 1:
                print("> edit command takes a single task id")
                print("> Use: task edit ID")
                sys.exit(1)
            try:
                task_id = int(args["args"][0])
                task = db.get_task(conn, task_id)
                new_text = input_prefill(f"Update #{task_id}: ", task[1])
                db.task_update(conn, task_id, new_text)
            except ValueError:
                print(f"> Invalid task id {task_id}")

        case "show":
            if args["week"]:
                new = db.get_tasks_new(conn, days=7)
                com = db.get_tasks_com(conn, days=7)
                reports.show_tasks_week(new, com)
            else:
                tasks = db.get_tasks(conn)
                reports.show_tasks(tasks)

        case _:
            print("Not yet implemented")


def input_prefill(prompt, text):
    def hook():
        readline.insert_text(text)
        readline.redisplay()

    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result


if __name__ == "__main__":
    main()
