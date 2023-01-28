from typing import List


def show_tasks(tasks: List):
    print(":-----:----------------------------------:")
    print(":  ID : {:32s} : ".format("TASK"))
    print(":-----:----------------------------------:")
    row = ":{id:4d} : {task:32s} : ".format
    for task in tasks:
        print(row(id=task[0], task=task[1]))
