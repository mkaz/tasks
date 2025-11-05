#!/usr/bin/env python3
"""
Kanban TUI for tasks using Textual
"""

import sqlite3
from pathlib import Path
from typing import List, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Header, Footer, Static, ListItem, ListView, Input, Button, TextArea
from textual.binding import Binding
from textual.screen import ModalScreen

import tasks.dbactions as db
from tasks.config import get_taskdb_loc
from tasks.task import Task as TaskModel


class ProjectSwitcherModal(ModalScreen):
    """Modal screen for switching between projects."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]

    def __init__(self, projects: List[dict], active_project_id: int):
        super().__init__()
        self.projects = projects
        self.active_project_id = active_project_id

    def compose(self) -> ComposeResult:
        with Grid(id="project_modal"):
            yield Static("Switch Project", id="project_title")
            yield ListView(id="project_list")

    def on_mount(self) -> None:
        """Populate the project list after mounting."""
        project_list = self.query_one("#project_list", ListView)

        # Add existing projects
        for project in self.projects:
            is_active = "⭐ " if project['id'] == self.active_project_id else "   "
            project_item = ListItem(Static(f"{is_active}{project['title']}"))
            project_item.project_id = project['id']  # Store project_id on the item
            project_list.append(project_item)

        # Add "Create New Project" option
        create_item = ListItem(Static("➕ Create New Project"))
        create_item.project_id = "create_new"  # Special marker for create action
        project_list.append(create_item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle project selection."""
        if hasattr(event.item, 'project_id'):
            if event.item.project_id == "create_new":
                # Show input for new project name
                self.dismiss({"action": "create_new"})
            else:
                # Switch to selected project
                self.dismiss({"action": "switch", "project_id": event.item.project_id})

    def action_close(self) -> None:
        """Close the modal screen."""
        self.dismiss(None)


class CreateProjectModal(ModalScreen):
    """Modal screen for creating a new project."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Grid(id="create_project_modal"):
            yield Static("Create New Project", id="create_project_title")
            yield Input(placeholder="Enter project name...", id="project_name_input")
            with Horizontal(id="create_project_buttons"):
                yield Button("Create", variant="primary", id="create_project_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        project_name_input = self.query_one("#project_name_input", Input)
        if project_name_input.value.strip():
            self.dismiss({"project_name": project_name_input.value.strip()})
        else:
            self.app.notify("Project name cannot be empty", severity="error")

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


class TaskColumn(Container):
    """A column representing a task state (Later, Now, Done)."""

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

        # Update the column header
        header = self.query_one(".column-header", Static)
        header.update(f"[bold]{self.title}[/bold]")

        # Update the task list - need to query by class since ID changes
        list_view = self.query_one(".task-list", ListView)
        list_view.clear()

        for task in tasks:
            list_view.append(TaskListItem(task))


class DetailPane(Container):
    """Detail pane for viewing and editing task details."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_task: Optional[TaskModel] = None

    def compose(self) -> ComposeResult:
        with Vertical(id="detail_content"):
            yield Static("Task Details", id="detail_header")
            yield Static("No task selected", id="detail_task_label")
            yield Static("Priority: -", id="detail_priority")
            yield Static("State: -", id="detail_state")
            yield Input(placeholder="URL...", id="detail_url")
            yield Static("Notes:", id="detail_notes_label")
            yield TextArea(id="detail_notes")
            yield Static("Created: -", id="detail_created")
            yield Static("Completed: -", id="detail_completed")

    def load_task(self, task: Optional[TaskModel], conn: sqlite3.Connection) -> None:
        """Load a task into the detail pane."""
        self.current_task = task

        if task is None:
            self.query_one("#detail_task_label", Static).update("No task selected")
            self.query_one("#detail_priority", Static).update("Priority: -")
            self.query_one("#detail_state", Static).update("State: -")
            self.query_one("#detail_url", Input).value = ""
            self.query_one("#detail_notes", TextArea).text = ""
            self.query_one("#detail_created", Static).update("Created: -")
            self.query_one("#detail_completed", Static).update("Completed: -")
            return

        priority_indicators = ["🔴", "🟡", "🟢", "🟢", "🟢"]
        priority_indicator = priority_indicators[min(task.priority, 4)]

        self.query_one("#detail_task_label", Static).update(f"[bold]Task #{task.id}:[/bold] {task.task}")
        self.query_one("#detail_priority", Static).update(f"Priority: {priority_indicator} ({task.priority})")
        self.query_one("#detail_state", Static).update(f"State: {task.state}")
        self.query_one("#detail_url", Input).value = task.url or ""
        self.query_one("#detail_notes", TextArea).text = task.notes or ""
        self.query_one("#detail_created", Static).update(f"Created: {task.dt_created}")

        if task.dt_completed and task.dt_completed != "0":
            self.query_one("#detail_completed", Static).update(f"Completed: {task.dt_completed}")
        else:
            self.query_one("#detail_completed", Static).update("Completed: -")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input field changes."""
        if event.input.id == "detail_url" and self.current_task:
            self.save_url()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle notes text area changes."""
        if event.text_area.id == "detail_notes" and self.current_task:
            self.save_notes()

    def save_url(self) -> None:
        """Save URL changes to the database."""
        if not self.current_task:
            return

        try:
            url_value = self.query_one("#detail_url", Input).value
            self.current_task.update_details(
                self.app.conn,
                self.current_task.task,
                url=url_value if url_value.strip() else None
            )
        except Exception as e:
            self.app.notify(f"Error saving URL: {e}", severity="error")

    def save_notes(self) -> None:
        """Save notes changes to the database."""
        if not self.current_task:
            return

        try:
            notes_value = self.query_one("#detail_notes", TextArea).text
            self.current_task.update_details(
                self.app.conn,
                self.current_task.task,
                notes=notes_value if notes_value.strip() else None
            )
        except Exception as e:
            self.app.notify(f"Error saving notes: {e}", severity="error")


class KanbanBoard(App):
    """Kanban board TUI application."""

    CSS = """
    ProjectSwitcherModal, CreateProjectModal {
        align: center middle;
    }

    #project_modal {
        grid-size: 1;
        grid-gutter: 1 2;
        grid-rows: auto 1fr;
        padding: 0 1;
        width: 60w;
        height: 20;
        border: thick $primary 80%;
        background: $surface;
    }

    #create_project_modal {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: auto 3 auto;
        padding: 0 1;
        width: 80w;
        height: 12;
        border: thick $primary 80%;
        background: $surface;
    }

    #project_title, #create_project_title {
        column-span: 1;
        text-align: center;
        width: 100%;
    }

    #create_project_title {
        column-span: 2;
    }

    #project_name_input {
        column-span: 2;
        width: 100%;
        height: 3;
    }

    #create_project_buttons {
        column-span: 2;
        width: 100%;
        content-align: center middle;
    }

    #project_list {
        height: 1fr;
        border: solid $primary;
    }

    #main_container {
        width: 100%;
        height: 100%;
    }

    #task_column_container {
        width: 30%;
        height: 100%;
    }

    #detail_pane {
        width: 70%;
        height: 100%;
        border-left: solid $primary;
    }

    #detail_content {
        padding: 1 2;
        height: 100%;
    }

    #detail_header {
        text-align: center;
        background: $primary;
        color: $text;
        padding: 0 1;
        margin-bottom: 1;
    }

    #detail_task_label {
        margin-bottom: 1;
    }

    #detail_priority, #detail_state {
        margin-bottom: 1;
    }

    #detail_url {
        margin-bottom: 1;
        height: 3;
    }

    #detail_notes_label {
        margin-bottom: 1;
    }

    #detail_notes {
        height: 1fr;
        border: solid $primary;
        margin-bottom: 1;
    }

    #detail_created, #detail_completed {
        color: $text-muted;
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
        width: 100%;
        height: 100%;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("a", "add_task", "Add Task"),
        Binding("b", "cycle_section", "Cycle Section"),
        Binding("p", "switch_project", "Switch Project"),
        Binding(">", "slide_right", "Slide Right"),
        Binding("r", "refresh", "Refresh"),
        Binding("x", "delete_task", "Delete"),
        Binding("+", "increase_priority", "↑ Priority"),
        Binding("-", "decrease_priority", "↓ Priority"),
        Binding("u", "undo", "Undo"),
    ]

    def __init__(self):
        super().__init__()
        self.conn: Optional[sqlite3.Connection] = None
        self.current_section = "Now"  # "Later", "Now", or "Done"
        self.sections = ["Later", "Now", "Done"]
        self.last_action: Optional[tuple] = None
        self.current_project_id: Optional[int] = None
        self.current_project_title: str = "General"
        self.task_column: Optional[TaskColumn] = None
        self.detail_pane: Optional[DetailPane] = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="main_container"):
            with Container(id="task_column_container"):
                self.task_column = TaskColumn(self.current_section, self.current_section)
                yield self.task_column

            self.detail_pane = DetailPane(id="detail_pane")
            yield self.detail_pane

        yield Footer()

    def update_title(self) -> None:
        """Update the app title with the current section and project name."""
        self.title = f"Tasks - {self.current_section} - {self.current_project_title}"

    def on_mount(self) -> None:
        """Initialize database connection and load tasks."""
        try:
            dbfile = Path(get_taskdb_loc())
            self.conn = sqlite3.connect(dbfile)
            self.conn.row_factory = sqlite3.Row

            # Ensure database schema exists
            if not dbfile.is_file():
                db.create_schema(self.conn)

            # Run migrations
            db.migrate_schema(self.conn)

            # Load the active project
            self.load_active_project()

            # Update the title
            self.update_title()

            self.refresh_tasks()

            # Focus the task list initially
            if self.task_column:
                self.set_focus(self.task_column.query_one(".task-list"))

        except Exception as e:
            self.notify(f"Database error: {e}", severity="error")

    def load_active_project(self) -> None:
        """Load the currently active project."""
        active_project = db.get_active_project(self.conn)
        if active_project:
            self.current_project_id = active_project['id']
            self.current_project_title = active_project['title']
        else:
            # Fallback to default project
            self.current_project_id = 1
            self.current_project_title = "General"

    def refresh_tasks(self) -> None:
        """Refresh tasks in the current section."""
        try:
            # Get tasks by state for current project
            tasks = db.get_tasks_by_state(self.conn, self.current_section, self.current_project_id)

            # Special handling for Done section to show completed tasks
            if self.current_section == "Done":
                cur = self.conn.cursor()
                if self.current_project_id:
                    cur.execute("""
                        SELECT * FROM tasks
                        WHERE dt_completed > 0
                            AND (state != 'Archive' OR state IS NULL)
                            AND project_id = ?
                        ORDER BY dt_completed DESC
                    """, [self.current_project_id])
                else:
                    cur.execute("""
                        SELECT * FROM tasks
                        WHERE dt_completed > 0 AND (state != 'Archive' OR state IS NULL)
                        ORDER BY dt_completed DESC
                    """)
                done_rows = cur.fetchall()
                tasks = [TaskModel(**dict(row)) for row in done_rows]

            if self.task_column:
                self.task_column.title = self.current_section
                self.task_column.state = self.current_section
                self.task_column.refresh_tasks(tasks)

            # Update title
            self.update_title()

        except Exception as e:
            self.notify(f"Error refreshing tasks: {e}", severity="error")

    def action_refresh(self) -> None:
        """Refresh the current section."""
        self.refresh_tasks()
        self.notify("Tasks refreshed")

    def action_cycle_section(self) -> None:
        """Cycle through sections (Later -> Now -> Done -> Later)."""
        current_index = self.sections.index(self.current_section)
        next_index = (current_index + 1) % len(self.sections)
        self.current_section = self.sections[next_index]
        self.refresh_tasks()
        self.notify(f"Switched to {self.current_section}")

        # Clear detail pane when switching sections
        if self.detail_pane:
            self.detail_pane.load_task(None, self.conn)

        # Refocus the task list
        if self.task_column:
            task_list = self.task_column.query_one(".task-list")
            self.set_focus(task_list)

    def action_add_task(self) -> None:
        """Add a new task using the detail pane."""
        # For now, use a simple approach - in the future this could use the detail pane
        # But we need to create the task first to have something to edit
        try:
            args = {
                "task_entry": "New Task",
                "project_id": self.current_project_id
            }
            task_id = TaskModel.create(self.conn, args)
            if task_id:
                db.set_task_state(self.conn, task_id, self.current_section)
                self.notify(f"Created Task #{task_id}")
                self.refresh_tasks()

                # Load the new task in the detail pane
                task = db.get_task(self.conn, task_id)
                if task and self.detail_pane:
                    self.detail_pane.load_task(task, self.conn)
            else:
                self.notify("Failed to create task", severity="error")
        except Exception as e:
            self.notify(f"Error creating task: {e}", severity="error")

    def get_current_task(self) -> Optional[TaskModel]:
        """Get the currently selected task."""
        focused = self.focused
        if not focused or not hasattr(focused, "highlighted_child"):
            return None

        highlighted = focused.highlighted_child
        if highlighted and hasattr(highlighted, "task_model"):
            return highlighted.task_model
        return None

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Handle task selection to update detail pane."""
        if event.item and hasattr(event.item, "task_model"):
            task = event.item.task_model
            if self.detail_pane:
                self.detail_pane.load_task(task, self.conn)

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
                # Task is in Done section, archive it
                db.set_task_state(self.conn, task.id, "Archive")
                self.notify(f"Archived task #{task.id}")

            self.refresh_tasks()

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
            self.refresh_tasks()

            # Clear detail pane
            if self.detail_pane:
                self.detail_pane.load_task(None, self.conn)

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
                db.increase_priority(self.conn, task.id)
                self.notify(f"Increased priority of task #{task.id}")
                self.refresh_tasks()
                # Reload task in detail pane
                updated_task = db.get_task(self.conn, task.id)
                if updated_task and self.detail_pane:
                    self.detail_pane.load_task(updated_task, self.conn)
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
                db.decrease_priority(self.conn, task.id)
                self.notify(f"Decreased priority of task #{task.id}")
                self.refresh_tasks()
                # Reload task in detail pane
                updated_task = db.get_task(self.conn, task.id)
                if updated_task and self.detail_pane:
                    self.detail_pane.load_task(updated_task, self.conn)
            else:
                self.notify("Task already at lowest priority")
        except Exception as e:
            self.notify(f"Error updating priority: {e}", severity="error")

    def action_undo(self) -> None:
        """Undo the last action."""
        if not self.last_action:
            self.notify("No action to undo")
            return

        action_type, data = self.last_action

        try:
            if action_type == "delete":
                task_to_restore: TaskModel = data
                cur = self.conn.cursor()
                cur.execute(
                    """
                    INSERT INTO tasks (id, task, url, notes, priority, dt_created, dt_completed, state, project_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task_to_restore.id,
                        task_to_restore.task,
                        task_to_restore.url,
                        task_to_restore.notes,
                        task_to_restore.priority,
                        task_to_restore.dt_created,
                        task_to_restore.dt_completed,
                        task_to_restore.state,
                        task_to_restore.project_id,
                    ),
                )
                self.conn.commit()
                self.notify(f"Restored task #{task_to_restore.id}")
                self.refresh_tasks()
                self.last_action = None  # Clear undo state
            else:
                self.notify("Undo for this action is not implemented")
        except Exception as e:
            self.notify(f"Error undoing action: {e}", severity="error")

    def action_switch_project(self) -> None:
        """Show project switcher modal."""
        try:
            projects = db.get_projects(self.conn)
            if not projects:
                self.notify("No projects found", severity="error")
                return

            def handle_project_action(result):
                if result:
                    if result["action"] == "switch":
                        self.switch_to_project(result["project_id"])
                    elif result["action"] == "create_new":
                        self.show_create_project_modal()

            self.push_screen(
                ProjectSwitcherModal(projects, self.current_project_id),
                handle_project_action
            )
        except Exception as e:
            self.notify(f"Error loading projects: {e}", severity="error")

    def switch_to_project(self, project_id: int) -> None:
        """Switch to the specified project."""
        try:
            if db.set_active_project(self.conn, project_id):
                # Reload active project
                self.load_active_project()
                self.update_title()
                self.refresh_tasks()
                self.notify(f"Switched to project: {self.current_project_title}")

                # Clear detail pane
                if self.detail_pane:
                    self.detail_pane.load_task(None, self.conn)
            else:
                self.notify("Failed to switch project", severity="error")
        except Exception as e:
            self.notify(f"Error switching project: {e}", severity="error")

    def show_create_project_modal(self) -> None:
        """Show modal to create a new project."""
        def handle_create_project(result):
            if result and result.get("project_name"):
                try:
                    project_id = db.create_project(self.conn, result["project_name"])
                    if project_id:
                        self.switch_to_project(project_id)
                        self.notify(f"Created project: {result['project_name']}")
                    else:
                        self.notify("Failed to create project", severity="error")
                except Exception as e:
                    self.notify(f"Error creating project: {e}", severity="error")

        self.push_screen(CreateProjectModal(), handle_create_project)

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
