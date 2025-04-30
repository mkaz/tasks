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

    # Create a single table with three columns for modes
    table = Table(show_header=True, padding=(0, 1), expand=True)
    table.add_column(" A. Now", justify="left", ratio=1)
    table.add_column(" B. Develop", justify="left", ratio=1)
    table.add_column(" C. Tinker", justify="left", ratio=1)

    # Group tasks by mode
    now_tasks = []
    develop_tasks = []
    tinker_tasks = []

    for task in tasks:
        mode = task[5] if len(task) > 5 else 'A'  # Default to 'Now' for backward compatibility
        priority_style = get_priority_style(task[4])
        formatted_task = f"{task[0]:>3} [{priority_style}]{task[1]}[/{priority_style}]"

        if mode == 'A':
            now_tasks.append(formatted_task)
        elif mode == 'B':
            develop_tasks.append(formatted_task)
        elif mode == 'C':
            tinker_tasks.append(formatted_task)

    # Find the maximum length to determine number of rows
    max_length = max(len(now_tasks), len(develop_tasks), len(tinker_tasks))

    # Pad shorter lists with empty strings to match max_length
    now_tasks.extend([''] * (max_length - len(now_tasks)))
    develop_tasks.extend([''] * (max_length - len(develop_tasks)))
    tinker_tasks.extend([''] * (max_length - len(tinker_tasks)))

    # Add rows to table
    for i in range(max_length):
        table.add_row(now_tasks[i], develop_tasks[i], tinker_tasks[i])

    console.print(table)


def show_tasks_list(tasks: List):
    console = Console()
    console.print(make_tasks_table(tasks))


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
    table = Table(show_header=False, padding=(0, 1))
    table.add_column("ID", justify="right", width=4)
    table.add_column("Task", width=42)
    table.add_column("Priority", justify="left")

    for task in tasks:
        priority_style = get_priority_style(task[4])
        table.add_row(
            str(task[0]),
            f"[{priority_style}]{task[1]}[/{priority_style}]",
            f"[{priority_style}]P{task[4]}[/{priority_style}]"
        )

    return table