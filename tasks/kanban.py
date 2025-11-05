#!/usr/bin/env python3
"""
Kanban TUI for tasks using Textual
"""

import sqlite3
from pathlib import Path
from typing import List, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Header, Footer, Static, ListItem, ListView, Input, Button, TextArea, Select
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
        url_indicator = " 🔗" if task.url else ""

        # Show checkbox for Done tasks, priority indicator for others
        if task.state == "Done":
            indicator = "✅"
        else:
            priority_indicators = ["🔴", "🟡", "🟢", "🟢", "🟢"]
            indicator = priority_indicators[min(task.priority, 4)]

        label = f"{task.id:>3} {indicator} {task.task}{url_indicator}"
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

    def on_key(self, event) -> None:
        """Handle Enter key to open detail pane for editing."""
        if event.key == "enter":
            # Trigger edit mode in detail pane
            if self.app.detail_pane and self.app.detail_pane.current_task:
                self.app.detail_pane.enter_edit_mode()
                # Focus the first editable field
                self.app.set_focus(self.app.detail_pane.query_one("#detail_task_input"))
                event.prevent_default()
                event.stop()


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
        self.edit_mode: bool = False

    def compose(self) -> ComposeResult:
        with Vertical(id="detail_content"):
            yield Static("Task Details [READ MODE]", id="detail_header")
            yield Static("Task #-", id="detail_task_id")
            yield Input(placeholder="Task description...", id="detail_task_input", disabled=True)
            yield Select(
                [("🔴 Highest (0)", 0), ("🟡 High (1)", 1), ("🟢 Normal (2)", 2), ("🟢 Low (3)", 3), ("🟢 Lowest (4)", 4)],
                id="detail_priority_select",
                allow_blank=False,
                disabled=True
            )
            yield Static("State: -", id="detail_state")
            yield Input(placeholder="URL...", id="detail_url", disabled=True)
            yield Static("Notes:", id="detail_notes_label")
            yield TextArea(id="detail_notes", disabled=True)
            yield Static("Created: -", id="detail_created")
            yield Static("Completed: -", id="detail_completed")
            yield Static("[Highlight task and press Enter to edit]", id="detail_hint")

    def load_task(self, task: Optional[TaskModel], conn: sqlite3.Connection) -> None:
        """Load a task into the detail pane."""
        self.current_task = task
        self.edit_mode = False  # Always start in read mode
        self.update_mode_display()

        if task is None:
            self.query_one("#detail_task_id", Static).update("Task #-")
            self.query_one("#detail_task_input", Input).value = ""
            self.query_one("#detail_priority_select", Select).value = 2
            self.query_one("#detail_state", Static).update("State: -")
            self.query_one("#detail_url", Input).value = ""
            self.query_one("#detail_notes", TextArea).text = ""
            self.query_one("#detail_created", Static).update("Created: -")
            self.query_one("#detail_completed", Static).update("Completed: -")
            return

        self.query_one("#detail_task_id", Static).update(f"[bold]Task #{task.id}[/bold]")
        self.query_one("#detail_task_input", Input).value = task.task
        self.query_one("#detail_priority_select", Select).value = task.priority
        self.query_one("#detail_state", Static).update(f"State: {task.state}")
        self.query_one("#detail_url", Input).value = task.url or ""
        self.query_one("#detail_notes", TextArea).text = task.notes or ""
        self.query_one("#detail_created", Static).update(f"Created: {task.dt_created}")

        if task.dt_completed and task.dt_completed != "0":
            self.query_one("#detail_completed", Static).update(f"Completed: {task.dt_completed}")
        else:
            self.query_one("#detail_completed", Static).update("Completed: -")

    def enter_edit_mode(self) -> None:
        """Enter edit mode."""
        if not self.current_task:
            return
        self.edit_mode = True
        self.update_mode_display()

    def exit_edit_mode(self) -> None:
        """Exit edit mode and save changes."""
        if not self.current_task:
            return

        # Save all changes
        self.save_all()

        self.edit_mode = False
        self.update_mode_display()

    def update_mode_display(self) -> None:
        """Update the display based on current mode."""
        if self.edit_mode:
            # Enable editing
            self.query_one("#detail_header", Static).update("Task Details [EDIT MODE]")
            self.query_one("#detail_task_input", Input).disabled = False
            self.query_one("#detail_priority_select", Select).disabled = False
            self.query_one("#detail_url", Input).disabled = False
            self.query_one("#detail_notes", TextArea).disabled = False
            self.query_one("#detail_hint", Static).update("[Press 'Esc' to save and exit]")
        else:
            # Disable editing (read-only)
            self.query_one("#detail_header", Static).update("Task Details [READ MODE]")
            self.query_one("#detail_task_input", Input).disabled = True
            self.query_one("#detail_priority_select", Select).disabled = True
            self.query_one("#detail_url", Input).disabled = True
            self.query_one("#detail_notes", TextArea).disabled = True
            self.query_one("#detail_hint", Static).update("[Highlight task and press Enter to edit]")

    def save_all(self) -> None:
        """Save all changes to the database."""
        if not self.current_task:
            return

        try:
            task_value = self.query_one("#detail_task_input", Input).value
            priority_value = self.query_one("#detail_priority_select", Select).value
            url_value = self.query_one("#detail_url", Input).value
            notes_value = self.query_one("#detail_notes", TextArea).text

            # Update task details
            self.current_task.update_details(
                self.app.conn,
                task_value if task_value.strip() else "Untitled Task",
                url=url_value if url_value.strip() else None,
                notes=notes_value if notes_value.strip() else None
            )

            # Update priority separately
            if priority_value is not None:
                cur = self.app.conn.cursor()
                cur.execute("UPDATE tasks SET priority = ? WHERE id = ?", [priority_value, self.current_task.id])
                self.app.conn.commit()
                self.current_task.priority = priority_value

            # Refresh the task list to show updated text
            self.app.refresh_tasks()
            self.app.notify("Changes saved")
        except Exception as e:
            self.app.notify(f"Error saving: {e}", severity="error")


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

    #detail_task_id {
        margin-bottom: 1;
    }

    #detail_task_input {
        margin-bottom: 1;
        height: 3;
    }

    #detail_priority_select {
        margin-bottom: 1;
    }

    #detail_state {
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

    #detail_hint {
        margin-top: 1;
        color: $text-muted;
        text-align: center;
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
        Binding("ctrl+n", "add_task", "New Task"),
        Binding("left", "cycle_section", "◀", show=False),
        Binding("right", "cycle_section", "▶", show=False),
        Binding("p", "switch_project", "Projects"),
        Binding("x", "delete_task", "Delete"),
        Binding("d", "mark_done", "Done"),
        Binding("ctrl+enter", "open_url", "Open URL"),
    ]

    def __init__(self):
        super().__init__()
        self.conn: Optional[sqlite3.Connection] = None
        self.current_section = "Backlog"  # "Backlog" or "Done"
        self.sections = ["Backlog", "Done"]
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

    def action_cycle_section(self) -> None:
        """Toggle between Backlog and Done sections."""
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
        """Add a new task to Backlog."""
        try:
            args = {
                "task_entry": "New Task",
                "project_id": self.current_project_id
            }
            task_id = TaskModel.create(self.conn, args)
            if task_id:
                # Always create new tasks in Backlog
                db.set_task_state(self.conn, task_id, "Backlog")
                self.notify(f"Created Task #{task_id} in Backlog")

                # Switch to Backlog if not already there
                if self.current_section != "Backlog":
                    self.current_section = "Backlog"

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

    def on_key(self, event) -> None:
        """Handle Escape key to exit edit mode in detail pane."""
        if event.key == "escape" and self.detail_pane and self.detail_pane.edit_mode:
            self.detail_pane.exit_edit_mode()
            # Refocus task list
            if self.task_column:
                self.set_focus(self.task_column.query_one(".task-list"))
            event.prevent_default()
            event.stop()

    def action_mark_done(self) -> None:
        """Mark the selected task as done."""
        task = self.get_current_task()
        if not task:
            return

        try:
            task.mark_done(self.conn)
            db.set_task_state(self.conn, task.id, "Done")
            self.notify(f"Marked task #{task.id} as done")
            self.refresh_tasks()

            # Clear detail pane
            if self.detail_pane:
                self.detail_pane.load_task(None, self.conn)

        except Exception as e:
            self.notify(f"Error marking task done: {e}", severity="error")

    def action_open_url(self) -> None:
        """Open the URL of the selected task in the default browser."""
        task = self.get_current_task()
        if not task:
            return

        if not task.url:
            self.notify("Task has no URL", severity="warning")
            return

        try:
            import webbrowser
            webbrowser.open(task.url)
            self.notify(f"Opening URL: {task.url}")
        except Exception as e:
            self.notify(f"Error opening URL: {e}", severity="error")

    def action_delete_task(self) -> None:
        """Delete the selected task."""
        task = self.get_current_task()
        if not task:
            return

        try:
            task.delete(self.conn)
            self.notify(f"Deleted task #{task.id}")
            self.refresh_tasks()

            # Clear detail pane
            if self.detail_pane:
                self.detail_pane.load_task(None, self.conn)

        except Exception as e:
            self.notify(f"Error deleting task: {e}", severity="error")


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
