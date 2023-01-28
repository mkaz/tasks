#!/usr/bin/env python3
"""
Task
A simple command-line task list.
"""

from pathlib import Path
import sqlite3

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
            taskid = insert_task(conn, task)
            print(f"Created task id: {taskid}")
        case "show":
            tasks = get_tasks(conn)
            show_tasks(tasks)
        case _:
            print("Not yet implemented")


if __name__ == "__main__":
    main()
