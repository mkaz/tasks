from rich import print
from typing import List


def show_tasks(tasks: List):
    print("----- ---------------------------------- ")
    row = "{id:4d}   {task:32s}   ".format
    for task in tasks:
        print(row(id=task[0], task=task[1]))


def show_tasks_week(new_tasks: List, com_tasks: List):
    print("")
    print("[bold magenta]WEEKLY REPORT[/bold magenta]")
    print("-------------\n")
    print("[yellow]New this week[/yellow]")
    print("----- ---------------------------------- ")
    row = "{id:4d}   {task:32s}   ".format
    for task in new_tasks:
        print(row(id=task[0], task=task[1]))

    print("\n")
    print("[green]Completed this week[/green]")
    print("----- ---------------------------------- ")
    row = "{id:4d}   {task:32s}  ✅".format
    for task in com_tasks:
        print(row(id=task[0], task=task[1]))
