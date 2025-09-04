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
            yield Input(value=self.task_model.task, placeholder="Enter task description...", id="task_input")
            yield Input(value=self.task_model.url or "", placeholder="Enter URL (optional)...", id="url_input")
            with Horizontal(id="edit_buttons"):
                yield Button("Save", variant="primary", id="save_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        task_input = self.query_one("#task_input", Input)
        url_input = self.query_one("#url_input", Input)
        self.dismiss({"task": task_input.value, "url": url_input.value})

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
        if self.highlighted_child and hasattr(self.highlighted_child, 'task_model'):
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
    AddModal, EditModal {
        align: center middle;
    }

    #add_modal, #edit_modal {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: auto 3 3 auto;
        padding: 0 1;
        width: 80w;
        height: 15;
        border: thick $primary 80%;
        background: $surface;
    }

    #add_title, #edit_title {
        column-span: 2;
        text-align: center;
        width: 100%;
    }

    #task_input, #url_input {
        column-span: 2;
        width: 100%;
        height: 3;
    }
    
    #add_buttons, #edit_buttons {
        column-span: 2;
        width: 100%;
        content-align: center middle;
    }

    .column-header {
        text-align: center;
        background: $primary;
        color: $text;
        padding: 1;
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
        Binding("<", "move_left", "</> Move"),
        Binding(">", "slide_right", ""),
        Binding("r", "refresh", "Refresh"),
        Binding("x", "delete_task", "Delete"),
        Binding("+", "increase_priority", "+/- Priority"),
        Binding("-", "decrease_priority", ""),
        Binding("e", "edit_task", "Edit"),
    ]
    
    def __init__(self):
        super().__init__()
        self.conn: Optional[sqlite3.Connection] = None
        self.current_focus_column = 0  # 0=Later, 1=Now, 2=Done
        self.columns = []
        
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
        
    def on_mount(self) -> None:
        """Initialize database connection and load tasks."""
        try:
            dbfile = Path(get_taskdb_loc())
            self.conn = sqlite3.connect(dbfile)
            self.conn.row_factory = sqlite3.Row
            
            # Ensure database schema exists
            if not dbfile.is_file():
                db.create_schema(self.conn)
                
            # Ensure Archive mode exists in schema
            self.ensure_archive_mode()
            
            self.refresh_all_tasks()
            
            # Focus the Now column initially
            self.set_focus(self.now_column.query_one(".task-list"))
            
        except Exception as e:
            self.notify(f"Database error: {e}", severity="error")
            
    def ensure_archive_mode(self) -> None:
        """Ensure the database supports Archive mode."""
        try:
            # Check if we have any tasks with Archive mode
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM tasks WHERE mode = 'Archive'")
            # This will work if the mode column exists and can handle 'Archive'
        except sqlite3.Error:
            # If there's an issue, run migration to ensure proper schema
            db.migrate_schema(self.conn)
            
    def refresh_all_tasks(self) -> None:
        """Refresh tasks in all columns."""
        try:
            # Get tasks by mode
            later_tasks = db.get_tasks_by_mode(self.conn, "Later")
            now_tasks = db.get_tasks_by_mode(self.conn, "Now")
            
            # Get completed tasks (not archived)
            cur = self.conn.cursor()
            cur.execute("""
                SELECT * FROM tasks 
                WHERE dt_completed > 0 AND (mode != 'Archive' OR mode IS NULL)
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
        def handle_add_task(result):
            if result and result["task"]:
                try:
                    task_entry = result["task"]
                    if result["url"] and result["url"].strip():
                        task_entry = f"{task_entry} {result['url']}"
                    
                    args = {"task_entry": task_entry}
                    task_id = TaskModel.create(self.conn, args)
                    if task_id:
                        db.set_task_mode(self.conn, task_id, "Now")
                        self.notify(f"Created Task #{task_id}")
                        self.refresh_all_tasks()
                    else:
                        self.notify("Failed to create task", severity="error")
                except Exception as e:
                    self.notify(f"Error creating task: {e}", severity="error")

        self.push_screen(AddModal(), handle_add_task)
        
    def get_current_task(self) -> Optional[TaskModel]:
        """Get the currently selected task."""
        focused = self.focused
        if not focused or not hasattr(focused, 'highlighted_child'):
            return None
            
        highlighted = focused.highlighted_child
        if highlighted and hasattr(highlighted, 'task_model'):
            return highlighted.task_model
        return None
        
    def action_move_left(self) -> None:
        """Move selected task left (Later <- Now <- Done)."""
        task = self.get_current_task()
        if not task:
            return
            
        try:
            if task.mode == "Now":
                db.set_task_mode(self.conn, task.id, "Later")
                self.notify(f"Moved task #{task.id} to Later")
            elif task.dt_completed and task.dt_completed != "0":
                # Reopen completed task and move to Now
                cur = self.conn.cursor()
                cur.execute("UPDATE tasks SET dt_completed = 0 WHERE id = ?", [task.id])
                self.conn.commit()
                db.set_task_mode(self.conn, task.id, "Now")
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
            if task.mode == "Later":
                db.set_task_mode(self.conn, task.id, "Now")
                self.notify(f"Moved task #{task.id} to Now")
            elif task.mode == "Now":
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
            if task.mode == "Later":
                db.set_task_mode(self.conn, task.id, "Now")
                self.notify(f"Moved task #{task.id} to Now")
            elif task.mode == "Now":
                task.mark_done(self.conn)
                self.notify(f"Completed task #{task.id}")
            elif task.dt_completed and task.dt_completed != "0":
                # Task is in Done column, archive it
                db.set_task_mode(self.conn, task.id, "Archive")
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
                cur.execute("UPDATE tasks SET priority = ? WHERE id = ?", [new_priority, task.id])
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
                cur.execute("UPDATE tasks SET priority = ? WHERE id = ?", [new_priority, task.id])
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
                    cur.execute("UPDATE tasks SET task = ?, url = ? WHERE id = ?", 
                              [result["task"], result["url"] if result["url"].strip() else None, task.id])
                    self.conn.commit()
                    self.notify(f"Updated task #{task.id}")
                    self.refresh_all_tasks()
                except Exception as e:
                    self.notify(f"Error updating task: {e}", severity="error")
                    
        self.push_screen(EditModal(task), handle_edit_task)
        
            
    def action_archive_done(self) -> None:
        """Archive all completed tasks."""
        try:
            cur = self.conn.cursor()
            cur.execute("""
                UPDATE tasks 
                SET mode = 'Archive' 
                WHERE dt_completed > 0 AND (mode != 'Archive' OR mode IS NULL)
            """)
            archived_count = cur.rowcount
            self.conn.commit()
            
            self.notify(f"Archived {archived_count} completed tasks")
            self.refresh_all_tasks()
            
        except Exception as e:
            self.notify(f"Error archiving tasks: {e}", severity="error")
            
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