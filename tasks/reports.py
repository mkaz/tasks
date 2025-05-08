from rich import print
from rich.table import Table
from rich.console import Console
from typing import List


def get_priority_style(priority: int) -> str:
    if priority == 1:
        return "cyan"
    elif priority == 2:
        return "yellow"
    elif priority == 3:
        return "white"
    else:
        return "dim white"


def show_tasks(tasks: List):
    console = Console()

    # Create a single table with two columns for modes
    table = Table(show_header=True, padding=(0, 1), expand=True, width=80)
    table.add_column(" Now", justify="left", ratio=1)
    table.add_column(" Later", justify="left", ratio=1)

    # Group tasks by mode
    now_tasks = []
    later_tasks = []

    for task in tasks:
        mode = task["mode"] if "mode" in task else "Now"
        priority_style = get_priority_style(task["priority"])
        formatted_task = (
            f"{task['id']:>3} [{priority_style}]{task['task']}[/{priority_style}]"
        )

        if mode == "Now":
            now_tasks.append(formatted_task)
        elif mode == "Later":
            later_tasks.append(formatted_task)

    # Find the maximum length to determine number of rows
    max_length = max(len(now_tasks), len(later_tasks))

    # Pad shorter lists with empty strings to match max_length
    now_tasks.extend([""] * (max_length - len(now_tasks)))
    later_tasks.extend([""] * (max_length - len(later_tasks)))

    # Add rows to table
    for i in range(max_length):
        table.add_row(now_tasks[i], later_tasks[i])

    console.print(table)


def show_tasks_list(tasks: List):
    console = Console()
    console.print(make_tasks_table(tasks))


def show_task_details(task):
    print(f"Task ID  : {task['id']}")
    print(f"Task     : {task['task']}")
    print(f"Priority : {task['priority']}")
    print(f"Mode     : {task['mode']}")
    print(f"URL      : {task['url']}")
    print(f"Completed: {task['dt_completed']}")
    print(f"Created  : {task['dt_created']}")


def show_tasks_week(new_tasks: List, com_tasks: List):
    console = Console()
    print("-------------")
    print("[bold magenta]WEEKLY REPORT[/bold magenta]")
    print("-------------\n")

    print("[yellow]New this week[/yellow]")
    console.print(make_tasks_table(new_tasks))

    print("\n")
    print("[green]Completed this week[/green]")
    console.print(make_tasks_table(com_tasks))


# Helper function to make a table of tasks
def make_tasks_table(tasks: List):
    table = Table(show_header=False, padding=(0, 1), width=80)
    table.add_column("ID", justify="right", width=4)
    table.add_column("Task", width=42)
    table.add_column("Priority", justify="left")

    for task in tasks:
        priority_style = get_priority_style(task["priority"])
        table.add_row(
            str(task["id"]),
            f"[{priority_style}]{task['task']}[/{priority_style}]",
            f"[{priority_style}]P{task['priority']}[/{priority_style}]",
        )

    return table
