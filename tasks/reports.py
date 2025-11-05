from rich import print
from rich.table import Table
from rich.console import Console
from typing import List

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

    # Create a single table with two columns for states
    table = Table(show_header=True, padding=(0, 1), expand=True, width=80)
    table.add_column(" Backlog", justify="left", ratio=1)
    table.add_column(" Done", justify="left", ratio=1)

    # Group tasks by state
    backlog_tasks = []
    done_tasks = []

    for task in tasks:
        state = task.state
        priority_style = get_priority_style(task.priority)
        url_indicator = " 🔗" if task.url else ""

        if state == "Backlog":
            formatted_task = f"{task.id:>3} [{priority_style}]{task.task}{url_indicator}[/{priority_style}]"
            backlog_tasks.append(formatted_task)
        elif state == "Done":
            # Show checkbox for done tasks instead of priority indicator
            formatted_task = f"{task.id:>3} ✅ {task.task}{url_indicator}"
            done_tasks.append(formatted_task)

    # Find the maximum length to determine number of rows
    max_length = max(len(backlog_tasks), len(done_tasks))

    # Pad shorter lists with empty strings to match max_length
    backlog_tasks.extend([""] * (max_length - len(backlog_tasks)))
    done_tasks.extend([""] * (max_length - len(done_tasks)))

    # Add rows to table
    for i in range(max_length):
        table.add_row(backlog_tasks[i], done_tasks[i])

    console.print(table)


def show_tasks_list(tasks: List[Task]):
    console = Console()
    console.print(make_tasks_table(tasks))


def show_task_details(task: Task):
    print(f"Task ID  : {task.id}")
    print(f"Task     : {task.task}")
    print(f"Priority : {task.priority}")
    print(f"State    : {task.state}")
    print(f"URL      : {task.url}")
    print(f"Completed: {task.dt_completed}")
    print(f"Created  : {task.dt_created}")


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
def make_tasks_table(tasks: List[Task]):
    table = Table(show_header=False, padding=(0, 1), width=80)
    table.add_column("ID", justify="right", width=4)
    table.add_column("Task", width=42)
    table.add_column("Priority", justify="left")

    for task in tasks:
        priority_style = get_priority_style(task.priority)
        url_indicator = " 🔗" if task.url else ""
        table.add_row(
            str(task.id),
            f"[{priority_style}]{task.task}{url_indicator}[/{priority_style}]",
            f"[{priority_style}]P{task.priority}[/{priority_style}]",
        )

    return table
