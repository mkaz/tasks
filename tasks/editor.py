from typing import Any, Dict, Optional

from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.validation import ValidationError, Validator

from tasks.task import Task

PRIORITY_RANGE = range(0, 5)
STATE_CHOICES = ["Backlog", "Now", "Later", "Done", "Archive"]


class PriorityValidator(Validator):
    def validate(self, document) -> None:
        text = document.text.strip()
        if not text:
            return
        if not text.isdigit():
            raise ValidationError(message="Priority must be a number between 0 and 4.")
        value = int(text)
        if value not in PRIORITY_RANGE:
            raise ValidationError(message="Priority must be between 0 and 4.")


class StateValidator(Validator):
    def validate(self, document) -> None:
        text = document.text.strip()
        if text and text not in STATE_CHOICES:
            raise ValidationError(
                message=f"State must be one of: {', '.join(STATE_CHOICES)}"
            )


def _prompt_value(
    label: str, current: Optional[str], validator: Optional[Validator] = None
) -> str:
    result = prompt(f"{label}: ", default=current or "", validator=validator).strip()
    return result


def _prompt_notes(current: Optional[str]) -> str:
    kb = KeyBindings()

    @kb.add("c-d")
    def _(event):
        event.app.current_buffer.validate_and_handle()

    message = "Notes (Ctrl-D to finish)\n"
    result = prompt(
        message,
        default=current or "",
        multiline=True,
        key_bindings=kb,
    ).strip()
    return result


def _confirm_save() -> bool:
    answer = prompt("Save changes? [Y/n]: ").strip().lower()
    if "n" in answer:
        return False
    return True


def edit_task(conn, task: Task) -> None:
    """Interactively edit a task, prompting field-by-field."""
    print("+" + "-" * 23 + "+")
    print(f"| Editing Task ID: {task.id:3d}  |")
    print("+" + "-" * 23 + "+")

    updated: Dict[str, Optional[Any]] = {}

    ## try catch so nice ctrl-c
    try:
        new_title = _prompt_value("Title", task.title)
        if new_title != task.title:
            updated["title"] = new_title

        new_url = _prompt_value("URL", task.url or "")
        if new_url != (task.url or ""):
            updated["url"] = new_url or None

        new_priority_raw = _prompt_value(
            "Priority (0-4)", str(task.priority), validator=PriorityValidator()
        )
        new_priority = int(new_priority_raw) if new_priority_raw else task.priority
        if new_priority != task.priority:
            updated["priority"] = new_priority

        new_state = _prompt_value("State", task.state, validator=StateValidator())
        if new_state != task.state:
            updated["state"] = new_state

        new_notes = _prompt_notes(task.notes)
        if new_notes != (task.notes or ""):
            updated["notes"] = new_notes or None

        if not updated:
            print("No changes made.")
            return

        print("\nProposed changes:")
        for key, value in updated.items():
            print(f"- {key}: {value}")

        if not _confirm_save():
            print("Edit cancelled.")
            return

        assignments = ", ".join(f"{field} = ?" for field in updated.keys())
        values = list(updated.values())
        values.append(task.id)

        cur = conn.cursor()
        cur.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", values)
        conn.commit()
        print("Task updated.")
    except KeyboardInterrupt:
        print("Edit cancelled.")
