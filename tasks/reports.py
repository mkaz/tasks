from typing import List, Optional

from rich import box, print
from rich.console import Console
from rich.table import Table

# local
from tasks.task import Task


def get_priority_style(priority: int) -> str:
    if priority == 0:
        return "bold red"
    if priority == 1:
        return "bold yellow"
    return "green"  # Default for 2 and anything higher


def show_tasks(tasks: List[Task]):
    console = Console()
    if not tasks:
        print("[dim]No active tasks.[/dim]")
        return

    console.print(make_tasks_table(tasks, include_state=True))


def show_tasks_list(tasks: List[Task]):
    console = Console()
    console.print(make_tasks_table(tasks))


def show_task_details(task: Optional[Task]):
    if task:
        print(f"Task ID  : {task.id}")
        print(f"Title    : {task.title}")
        print(f"Priority : {task.priority}")
        print(f"State    : {task.state}")
        print(f"Notes    : {task.notes}")
        print(f"URL      : {task.url}")
        print(f"Completed: {task.dt_completed}")
        print(f"Created  : {task.dt_created}")
    else:
        print("No task found.")


def show_tasks_week(new_tasks: List[Task], com_tasks: List[Task]):
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
def make_tasks_table(tasks: List[Task], include_state: bool = False) -> Table:
    table = Table(
        show_header=True,
        padding=(0, 1),
        width=80,
        box=box.ASCII,
        expand=False,
    )
    table.add_column("ID", justify="right", width=4, style="bold cyan")
    table.add_column("Title", width=42)
    if include_state:
        table.add_column("State", justify="left", style="magenta")
    table.add_column("Priority", justify="left")

    for task in tasks:
        priority_style = get_priority_style(task.priority)
        url_indicator = " 🔗" if task.url else ""
        row = [
            str(task.id),
            f"[{priority_style}]{task.title}{url_indicator}[/{priority_style}]",
        ]

        if include_state:
            state_style = "green" if task.state == "Done" else "cyan"
            row.append(f"[{state_style}]{task.state}[/{state_style}]")

        row.append(f"[{priority_style}]P{task.priority}[/{priority_style}]")
        table.add_row(*row)

    return table
