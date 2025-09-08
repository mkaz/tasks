from dataclasses import dataclass
from typing import Optional
from sqlite3 import Connection
import re


@dataclass
class Task:
    id: int
    task: str
    priority: int
    state: str
    dt_created: str
    dt_completed: str
    url: Optional[str] = None
    board_id: int = 1

    @staticmethod
    def create(conn: Connection, args: dict) -> Optional[int]:
        """Creates a new task in the database and returns its ID."""
        entry_text = args["task_entry"]
        task_text, url = parse_entry_text(entry_text)
        board_id = args.get("board_id", 1)  # Default to board 1 if not specified

        cur = conn.cursor()
        sql = "INSERT INTO tasks (task, url, board_id) VALUES (?, ?, ?)"
        try:
            cur.execute(sql, (task_text, url, board_id))
            conn.commit()
            return cur.lastrowid
        except Exception:
            conn.rollback()
            return None

    def mark_done(self, conn: Connection) -> None:
        """Marks the task as done in the database."""
        cur = conn.cursor()
        sql = """
            UPDATE tasks
               SET dt_completed = CURRENT_TIMESTAMP
             WHERE id = ?
        """
        try:
            cur.execute(sql, [self.id])
            conn.commit()
        except Exception:
            conn.rollback()

    def update_details(
        self, conn: Connection, task_text: str, url: Optional[str] = None
    ) -> None:
        """Updates the task's text and optionally its URL in the database and on the instance.
        If 'url' is None, the URL field is not updated in the database.
        """
        cur = conn.cursor()

        fields_to_set = {"task": task_text}
        values_list = [task_text]

        if url is not None:
            fields_to_set["url"] = url
            values_list.append(url)

        set_clause = ", ".join(f"{key} = ?" for key in fields_to_set)
        values_list.append(self.id)

        sql = f"UPDATE tasks SET {set_clause} WHERE id = ?"

        try:
            cur.execute(sql, values_list)
            conn.commit()

            self.task = task_text
            if url is not None:
                self.url = url
        except Exception:
            conn.rollback()

    def delete(self, conn: Connection) -> None:
        """Deletes the task from the database."""
        cur = conn.cursor()
        sql = "DELETE FROM tasks WHERE id = ?"
        try:
            cur.execute(sql, [self.id])
            conn.commit()
        except Exception:
            conn.rollback()


def parse_entry_text(entry_text: str) -> tuple[str, Optional[str]]:
    """Parse the entry text into a task text and URL."""
    # use regex to find the first URL in entry_text and extract the URL and the rest of the text
    url_pattern = r"https?://.*?[^\s]+"
    match = re.search(url_pattern, entry_text)
    if match:
        url = match.group(0)
        task_text = entry_text.replace(url, "")
    else:
        url = None
        task_text = entry_text
    return task_text, url
