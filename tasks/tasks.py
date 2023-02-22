#!/usr/bin/env python3
"""
Task
A simple command-line task list.
"""

from pathlib import Path
import readline
import sqlite3
import sys

# local
from config import init_args
from dbactions import *
from reports import *


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
        create_schema(conn)

    match args["command"]:
        case "add":
            task = " ".join(args["args"])
            task_id = insert_task(conn, task)
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
                    task_delete(conn, task_id)
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
                    mark_done(conn, task_id)
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
                task = get_task(conn, task_id)
                new_text = input_prefill(f"Update #{task_id}: ", task[1])
                task_update(conn, task_id, new_text)
            except ValueError:
                print(f"> Invalid task id {task_id}")

        case "show":
            if args["week"]:
                new = get_tasks_new(conn, days=7)
                com = get_tasks_com(conn, days=7)
                show_tasks_week(new, com)
            else:
                tasks = get_tasks(conn)
                show_tasks(tasks)

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