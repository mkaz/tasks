from typing import List


def show_tasks(tasks: List):
    print("----- ---------------------------------- ")
    row = "{id:4d}   {task:32s}   ".format
    for task in tasks:
        print(row(id=task[0], task=task[1]))


def show_tasks_week(new_tasks: List, com_tasks: List):
    print("")
    print("WEEKLY REPORT")
    print("-------------\n")
    print("New tasks this week")
    print("----- ---------------------------------- ")
    row = "{id:4d}   {task:32s}   ".format
    for task in new_tasks:
        print(row(id=task[0], task=task[1]))

    print("\n")
    print("Completed tasks this week")
    print("----- ---------------------------------- ")
    row = "{id:4d}   {task:32s}  ✅".format
    for task in com_tasks:
        print(row(id=task[0], task=task[1]))
