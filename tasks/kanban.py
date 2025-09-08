#!/usr/bin/env python3
"""
Kanban TUI for tasks using Textual
"""

import sqlite3
from pathlib import Path
from typing import List, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Header, Footer, Static, ListItem, ListView, Input, Button
from textual.binding import Binding
from textual.screen import ModalScreen

import tasks.dbactions as db
from tasks.config import get_taskdb_loc
from tasks.task import Task as TaskModel


class AddModal(ModalScreen):
    """Modal screen for adding a new task."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Grid(id="add_modal"):
            yield Static("Add New Task", id="add_title")
            yield Input(placeholder="Enter task description...", id="task_input")
            yield Input(placeholder="Enter URL (optional)...", id="url_input")
            with Horizontal(id="add_buttons"):
                yield Button("Add", variant="primary", id="add_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        task_input = self.query_one("#task_input", Input)
        url_input = self.query_one("#url_input", Input)
        self.dismiss({"task": task_input.value, "url": url_input.value})

    def action_close(self) -> None:
        """Close the modal screen."""
        self.dismiss(None)


class EditModal(ModalScreen):
    """Modal screen for editing an existing task."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]

    def __init__(self, task: TaskModel):
        super().__init__()
        self.task_model = task

    def compose(self) -> ComposeResult:
        with Grid(id="edit_modal"):
            yield Static(f"Edit Task #{self.task_model.id}", id="edit_title")
            yield Input(
                value=self.task_model.task,
                placeholder="Enter task description...",
                id="task_input",
            )
            yield Input(
                value=self.task_model.url or "",
                placeholder="Enter URL (optional)...",
                id="url_input",
            )
            with Horizontal(id="edit_buttons"):
                yield Button("Save", variant="primary", id="save_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        task_input = self.query_one("#task_input", Input)
        url_input = self.query_one("#url_input", Input)
        self.dismiss({"task": task_input.value, "url": url_input.value})

    def action_close(self) -> None:
        """Close the modal screen."""
        self.dismiss(None)


class BoardSwitcherModal(ModalScreen):
    """Modal screen for switching between boards."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]

    def __init__(self, boards: List[dict], active_board_id: int):
        super().__init__()
        self.boards = boards
        self.active_board_id = active_board_id

    def compose(self) -> ComposeResult:
        with Grid(id="board_modal"):
            yield Static("Switch Board", id="board_title")
            yield ListView(id="board_list")

    def on_mount(self) -> None:
        """Populate the board list after mounting."""
        board_list = self.query_one("#board_list", ListView)
        
        # Add existing boards
        for board in self.boards:
            is_active = "⭐ " if board['id'] == self.active_board_id else "   "
            board_item = ListItem(Static(f"{is_active}{board['title']}"))
            board_item.board_id = board['id']  # Store board_id on the item
            board_list.append(board_item)
        
        # Add "Create New Board" option
        create_item = ListItem(Static("➕ Create New Board"))
        create_item.board_id = "create_new"  # Special marker for create action
        board_list.append(create_item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle board selection."""
        if hasattr(event.item, 'board_id'):
            if event.item.board_id == "create_new":
                # Show input for new board name
                self.dismiss({"action": "create_new"})
            else:
                # Switch to selected board
                self.dismiss({"action": "switch", "board_id": event.item.board_id})

    def action_close(self) -> None:
        """Close the modal screen."""
        self.dismiss(None)


class CreateBoardModal(ModalScreen):
    """Modal screen for creating a new board."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Grid(id="create_board_modal"):
            yield Static("Create New Board", id="create_board_title")
            yield Input(placeholder="Enter board name...", id="board_name_input")
            with Horizontal(id="create_board_buttons"):
                yield Button("Create", variant="primary", id="create_board_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        board_name_input = self.query_one("#board_name_input", Input)
        if board_name_input.value.strip():
            self.dismiss({"board_name": board_name_input.value.strip()})
        else:
            self.app.notify("Board name cannot be empty", severity="error")

    def action_close(self) -> None:
        """Close the modal screen."""
        self.dismiss(None)


class TaskListItem(ListItem):
    """Custom list item that holds a task."""

    def __init__(self, task: TaskModel, *args, **kwargs):
        self._task_model = task  # Use private attribute to avoid property conflicts
        priority_indicators = ["🔴", "🟡", "🟢", "🟢", "🟢"]
        priority_indicator = priority_indicators[min(task.priority, 4)]
        url_indicator = " 🔗" if task.url else ""

        label = f"{task.id:>3} {priority_indicator} {task.task}{url_indicator}"
        super().__init__(Static(label, classes="task-item"), *args, **kwargs)

    @property
    def task_model(self) -> TaskModel:
        """Get the associated task."""
        return self._task_model


class TaskListView(ListView):
    """A ListView that highlights the first item on focus."""

    def on_focus(self) -> None:
        if len(self) > 0:
            self.highlighted = 0

    def key_enter(self):
        """Handle Enter key press to open URL."""
        if self.highlighted_child and hasattr(self.highlighted_child, "task_model"):
            task = self.highlighted_child.task_model
            if task and task.url:
                try:
                    import webbrowser

                    webbrowser.open(task.url)
                    self.app.notify(f"Opened URL for task #{task.id}")
                except Exception as e:
                    self.app.notify(f"Error opening URL: {e}", severity="error")
            else:
                self.app.notify("No URL to open")


class TaskColumn(Container):
    """A column representing a task state (Later, Now, Done, Archive)."""

    def __init__(self, title: str, state: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = title
        self.state = state
        self.tasks: List[TaskModel] = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(f"[bold]{self.title}[/bold]", classes="column-header")
            yield TaskListView(id=f"list_{self.state.lower()}", classes="task-list")

    def refresh_tasks(self, tasks: List[TaskModel]) -> None:
        """Update the tasks displayed in this column."""
        self.tasks = tasks
        list_view = self.query_one(f"#list_{self.state.lower()}", ListView)
        list_view.clear()

        for task in tasks:
            list_view.append(TaskListItem(task))


class KanbanBoard(App):
    """Kanban board TUI application."""

    CSS = """
    AddModal, EditModal, BoardSwitcherModal, CreateBoardModal {
        align: center middle;
    }

    #add_modal, #edit_modal, #create_board_modal {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: auto 3 3 auto;
        padding: 0 1;
        width: 80w;
        height: 15;
        border: thick $primary 80%;
        background: $surface;
    }

    #board_modal {
        grid-size: 1;
        grid-gutter: 1 2;
        grid-rows: auto 1fr;
        padding: 0 1;
        width: 60w;
        height: 20;
        border: thick $primary 80%;
        background: $surface;
    }

    #add_title, #edit_title, #board_title, #create_board_title {
        column-span: 2;
        text-align: center;
        width: 100%;
    }

    #board_title {
        column-span: 1;
        text-align: center;
        width: 100%;
    }

    #task_input, #url_input, #board_name_input {
        column-span: 2;
        width: 100%;
        height: 3;
    }

    #add_buttons, #edit_buttons, #create_board_buttons {
        column-span: 2;
        width: 100%;
        content-align: center middle;
    }

    #board_list {
        height: 1fr;
        border: solid $primary;
    }

    .column-header {
        text-align: center;
        background: $primary;
        color: $text;
        padding: 0 1;
        margin: 0 0 1 0;
    }

    .task-list {
        border: solid $primary;
        height: 1fr;
    }

    .task-item {
        padding: 0 1;
    }

    TaskColumn {
        width: 1fr;
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("a", "add_task", "Add Task"),
        Binding("<", "move_left", "> Move"),
        Binding(">", "slide_right", ""),
        Binding("r", "refresh", "Refresh"),
        Binding("x", "delete_task", "Delete"),
        Binding("+", "increase_priority", "- Priority"),
        Binding("-", "decrease_priority", ""),
        Binding("e", "edit_task", "Edit"),
        Binding("u", "undo", "Undo"),
        Binding("b", "switch_board", "Switch Board"),
    ]

    def __init__(self):
        super().__init__()
        self.conn: Optional[sqlite3.Connection] = None
        self.current_focus_column = 0  # 0=Later, 1=Now, 2=Done
        self.columns = []
        self.last_action: Optional[tuple] = None
        self.current_board_id: Optional[int] = None
        self.current_board_title: str = "General"

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="board"):
            self.later_column = TaskColumn("Later", "Later")
            self.now_column = TaskColumn("Now", "Now")
            self.done_column = TaskColumn("Done", "Done")

            yield self.later_column
            yield self.now_column
            yield self.done_column

        self.columns = [self.later_column, self.now_column, self.done_column]

        yield Footer()

    def update_title(self) -> None:
        """Update the app title with the current board name."""
        self.title = f"Tasks - {self.current_board_title}"

    def on_mount(self) -> None:
        """Initialize database connection and load tasks."""
        try:
            dbfile = Path(get_taskdb_loc())
            self.conn = sqlite3.connect(dbfile)
            self.conn.row_factory = sqlite3.Row

            # Ensure database schema exists
            if not dbfile.is_file():
                db.create_schema(self.conn)

            # Ensure Archive state exists in schema
            self.ensure_archive_state()

            # Load the active board
            self.load_active_board()

            # Update the title with board name
            self.update_title()

            self.refresh_all_tasks()

            # Focus the Now column initially
            self.set_focus(self.now_column.query_one(".task-list"))

        except Exception as e:
            self.notify(f"Database error: {e}", severity="error")

    def load_active_board(self) -> None:
        """Load the currently active board."""
        active_board = db.get_active_board(self.conn)
        if active_board:
            self.current_board_id = active_board['id']
            self.current_board_title = active_board['title']
        else:
            # Fallback to default board
            self.current_board_id = 1
            self.current_board_title = "General"

    def ensure_archive_state(self) -> None:
        """Ensure the database supports Archive state."""
        try:
            # Check if we have any tasks with Archive state
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM tasks WHERE state = 'Archive'")
            # This will work if the state column exists and can handle 'Archive'
        except sqlite3.Error:
            # If there's an issue, run migration to ensure proper schema
            db.migrate_schema(self.conn)

    def refresh_all_tasks(self) -> None:
        """Refresh tasks in all columns."""
        try:
            # Get tasks by state for current board
            later_tasks = db.get_tasks_by_state(self.conn, "Later", self.current_board_id)
            now_tasks = db.get_tasks_by_state(self.conn, "Now", self.current_board_id)

            # Get completed tasks (not archived) for current board
            cur = self.conn.cursor()
            if self.current_board_id:
                cur.execute("""
                    SELECT * FROM tasks
                    WHERE dt_completed > 0 
                        AND (state != 'Archive' OR state IS NULL)
                        AND board_id = ?
                    ORDER BY dt_completed DESC
                """, [self.current_board_id])
            else:
                cur.execute("""
                    SELECT * FROM tasks
                    WHERE dt_completed > 0 AND (state != 'Archive' OR state IS NULL)
                    ORDER BY dt_completed DESC
                """)
            done_rows = cur.fetchall()
            done_tasks = [TaskModel(**dict(row)) for row in done_rows]

            self.later_column.refresh_tasks(later_tasks)
            self.now_column.refresh_tasks(now_tasks)
            self.done_column.refresh_tasks(done_tasks)

        except Exception as e:
            self.notify(f"Error refreshing tasks: {e}", severity="error")

    def action_refresh(self) -> None:
        """Refresh the board."""
        self.refresh_all_tasks()
        self.notify("Board refreshed")

    def action_add_task(self) -> None:
        """Show input for adding a new task."""
        target_state = "Now"
        if self.focused and isinstance(self.focused, TaskListView):
            if self.focused.id == "list_later":
                target_state = "Later"

        def handle_add_task(result):
            if result and result["task"]:
                try:
                    task_entry = result["task"]
                    if result["url"] and result["url"].strip():
                        task_entry = f"{task_entry} {result['url']}"

                    args = {
                        "task_entry": task_entry,
                        "board_id": self.current_board_id
                    }
                    task_id = TaskModel.create(self.conn, args)
                    if task_id:
                        db.set_task_state(self.conn, task_id, target_state)
                        self.notify(f"Created Task #{task_id} in {target_state}")
                        self.refresh_all_tasks()
                    else:
                        self.notify("Failed to create task", severity="error")
                except Exception as e:
                    self.notify(f"Error creating task: {e}", severity="error")

        self.push_screen(AddModal(), handle_add_task)

    def get_current_task(self) -> Optional[TaskModel]:
        """Get the currently selected task."""
        focused = self.focused
        if not focused or not hasattr(focused, "highlighted_child"):
            return None

        highlighted = focused.highlighted_child
        if highlighted and hasattr(highlighted, "task_model"):
            return highlighted.task_model
        return None

    def action_move_left(self) -> None:
        """Move selected task left (Later <- Now <- Done)."""
        task = self.get_current_task()
        if not task:
            return

        try:
            if task.state == "Now":
                db.set_task_state(self.conn, task.id, "Later")
                self.notify(f"Moved task #{task.id} to Later")
            elif task.dt_completed and task.dt_completed != "0":
                # Reopen completed task and move to Now
                cur = self.conn.cursor()
                cur.execute("UPDATE tasks SET dt_completed = 0 WHERE id = ?", [task.id])
                self.conn.commit()
                db.set_task_state(self.conn, task.id, "Now")
                self.notify(f"Reopened task #{task.id} and moved to Now")

            self.refresh_all_tasks()

        except Exception as e:
            self.notify(f"Error moving task: {e}", severity="error")

    def action_move_right(self) -> None:
        """Move selected task right (Later -> Now -> Done)."""
        task = self.get_current_task()
        if not task:
            return

        try:
            if task.state == "Later":
                db.set_task_state(self.conn, task.id, "Now")
                self.notify(f"Moved task #{task.id} to Now")
            elif task.state == "Now":
                task.mark_done(self.conn)
                self.notify(f"Completed task #{task.id}")

            self.refresh_all_tasks()

        except Exception as e:
            self.notify(f"Error moving task: {e}", severity="error")

    def action_slide_right(self) -> None:
        """Slide task right: Later -> Now -> Done -> Archive."""
        task = self.get_current_task()
        if not task:
            return

        try:
            if task.state == "Later":
                db.set_task_state(self.conn, task.id, "Now")
                self.notify(f"Moved task #{task.id} to Now")
            elif task.state == "Now":
                task.mark_done(self.conn)
                self.notify(f"Completed task #{task.id}")
            elif task.dt_completed and task.dt_completed != "0":
                # Task is in Done column, archive it
                db.set_task_state(self.conn, task.id, "Archive")
                self.notify(f"Archived task #{task.id}")

            self.refresh_all_tasks()

        except Exception as e:
            self.notify(f"Error sliding task: {e}", severity="error")

    def action_delete_task(self) -> None:
        """Delete the selected task."""
        task = self.get_current_task()
        if not task:
            return

        try:
            # Store the state before deleting for undo
            self.last_action = ("delete", task)
            task.delete(self.conn)
            self.notify(f"Deleted task #{task.id}")
            self.refresh_all_tasks()
        except Exception as e:
            self.notify(f"Error deleting task: {e}", severity="error")

    def action_increase_priority(self) -> None:
        """Increase priority of selected task (lower number = higher priority)."""
        task = self.get_current_task()
        if not task:
            return

        try:
            new_priority = max(0, task.priority - 1)
            if new_priority != task.priority:
                cur = self.conn.cursor()
                cur.execute(
                    "UPDATE tasks SET priority = ? WHERE id = ?",
                    [new_priority, task.id],
                )
                self.conn.commit()
                self.notify(f"Increased priority of task #{task.id} to {new_priority}")
                self.refresh_all_tasks()
            else:
                self.notify("Task already at highest priority")
        except Exception as e:
            self.notify(f"Error updating priority: {e}", severity="error")

    def action_decrease_priority(self) -> None:
        """Decrease priority of selected task (higher number = lower priority)."""
        task = self.get_current_task()
        if not task:
            return

        try:
            new_priority = min(4, task.priority + 1)
            if new_priority != task.priority:
                cur = self.conn.cursor()
                cur.execute(
                    "UPDATE tasks SET priority = ? WHERE id = ?",
                    [new_priority, task.id],
                )
                self.conn.commit()
                self.notify(f"Decreased priority of task #{task.id} to {new_priority}")
                self.refresh_all_tasks()
            else:
                self.notify("Task already at lowest priority")
        except Exception as e:
            self.notify(f"Error updating priority: {e}", severity="error")

    def action_edit_task(self) -> None:
        """Edit the selected task."""
        task = self.get_current_task()
        if not task:
            return

        def handle_edit_task(result):
            if result and result["task"]:
                try:
                    cur = self.conn.cursor()
                    cur.execute(
                        "UPDATE tasks SET task = ?, url = ? WHERE id = ?",
                        [
                            result["task"],
                            result["url"] if result["url"].strip() else None,
                            task.id,
                        ],
                    )
                    self.conn.commit()
                    self.notify(f"Updated task #{task.id}")
                    self.refresh_all_tasks()
                except Exception as e:
                    self.notify(f"Error updating task: {e}", severity="error")

        self.push_screen(EditModal(task), handle_edit_task)

    def action_undo(self) -> None:
        """Undo the last action."""
        if not self.last_action:
            self.notify("No action to undo")
            return

        action_type, data = self.last_action

        try:
            if action_type == "delete":
                task_to_restore: TaskModel = data
                # Since we have the full task model, we can re-insert it.
                # This is a simplified approach. A robust implementation
                # might need to handle ID collisions if a new task was created
                # with the same ID, but that's unlikely in this app.
                cur = self.conn.cursor()
                cur.execute(
                    """
                    INSERT INTO tasks (id, task, url, priority, dt_created, dt_completed, state)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task_to_restore.id,
                        task_to_restore.task,
                        task_to_restore.url,
                        task_to_restore.priority,
                        task_to_restore.dt_created,
                        task_to_restore.dt_completed,
                        task_to_restore.state,
                    ),
                )
                self.conn.commit()
                self.notify(f"Restored task #{task_to_restore.id}")
                self.refresh_all_tasks()
                self.last_action = None  # Clear undo state
            else:
                self.notify("Undo for this action is not implemented")
        except Exception as e:
            self.notify(f"Error undoing action: {e}", severity="error")

    def action_archive_done(self) -> None:
        """Archive all completed tasks."""
        try:
            cur = self.conn.cursor()
            cur.execute("""
                UPDATE tasks
                SET state = 'Archive'
                WHERE dt_completed > 0 AND (state != 'Archive' OR state IS NULL)
            """)
            archived_count = cur.rowcount
            self.conn.commit()

            self.notify(f"Archived {archived_count} completed tasks")
            self.refresh_all_tasks()

        except Exception as e:
            self.notify(f"Error archiving tasks: {e}", severity="error")

    def action_switch_board(self) -> None:
        """Show board switcher modal."""
        try:
            boards = db.get_boards(self.conn)
            if not boards:
                self.notify("No boards found", severity="error")
                return

            def handle_board_action(result):
                if result:
                    if result["action"] == "switch":
                        self.switch_to_board(result["board_id"])
                    elif result["action"] == "create_new":
                        self.show_create_board_modal()

            self.push_screen(
                BoardSwitcherModal(boards, self.current_board_id), 
                handle_board_action
            )
        except Exception as e:
            self.notify(f"Error loading boards: {e}", severity="error")

    def switch_to_board(self, board_id: int) -> None:
        """Switch to the specified board."""
        try:
            if db.set_active_board(self.conn, board_id):
                # Reload active board
                self.load_active_board()
                self.update_title()
                self.refresh_all_tasks()
                self.notify(f"Switched to board: {self.current_board_title}")
            else:
                self.notify("Failed to switch board", severity="error")
        except Exception as e:
            self.notify(f"Error switching board: {e}", severity="error")

    def show_create_board_modal(self) -> None:
        """Show modal to create a new board."""
        def handle_create_board(result):
            if result and result.get("board_name"):
                try:
                    board_id = db.create_board(self.conn, result["board_name"])
                    if board_id:
                        self.switch_to_board(board_id)
                        self.notify(f"Created board: {result['board_name']}")
                    else:
                        self.notify("Failed to create board", severity="error")
                except Exception as e:
                    self.notify(f"Error creating board: {e}", severity="error")

        self.push_screen(CreateBoardModal(), handle_create_board)

    def on_unmount(self) -> None:
        """Clean up database connection."""
        if self.conn:
            self.conn.close()


def run_kanban():
    """Run the kanban board TUI."""
    app = KanbanBoard()
    app.run()


if __name__ == "__main__":
    run_kanban()
