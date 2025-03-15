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

    console.print(table)


def show_tasks_week(new_tasks: List, com_tasks: List):
    console = Console()
    print("")
    print("[bold magenta]WEEKLY REPORT[/bold magenta]")
    print("-------------\n")

    print("[yellow]New this week[/yellow]")
    new_table = Table(show_header=False, padding=(0, 1))
    new_table.add_column("ID", justify="right", width=4)
    new_table.add_column("Task", width=42)
    new_table.add_column("Priority", justify="left")

    for task in new_tasks:
        priority_style = get_priority_style(task[4])
        new_table.add_row(
            str(task[0]),
            f"[{priority_style}]{task[1]}[/{priority_style}]",
            f"[{priority_style}]P{task[4]}[/{priority_style}]"
        )

    console.print(new_table)

    print("\n")
    print("[green]Completed this week[/green]")
    com_table = Table(show_header=False, padding=(0, 1))
    com_table.add_column("ID", justify="right", width=4)
    com_table.add_column("Task", width=42)
    com_table.add_column("Priority", justify="left")
    com_table.add_column("Status", justify="left")

    for task in com_tasks:
        priority_style = get_priority_style(task[4])
        com_table.add_row(
            str(task[0]),
            f"[{priority_style}]{task[1]}[/{priority_style}]",
            f"[{priority_style}]P{task[4]}[/{priority_style}]",
            "✅"
        )

    console.print(com_table)
