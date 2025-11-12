from dataclasses import dataclass
from typing import Optional
from sqlite3 import Connection
import re


@dataclass
class Task:
    id: int
    title: str
    priority: int
    state: str
    dt_created: str
    dt_completed: str
    url: Optional[str] = None
    notes: Optional[str] = None

    @staticmethod
    def create(conn: Connection, args: dict) -> Optional[int]:
        """Creates a new task in the database and returns its ID."""
        entry_text = args["task_entry"]
        title_text, url = parse_entry_text(entry_text)

        cur = conn.cursor()

        columns = ["title", "url"]
        values = [title_text, url]

        priority = args.get("priority")
        if priority is not None:
            columns.append("priority")
            values.append(priority)

        state = args.get("state")
        if state:
            columns.append("state")
            values.append(state)

        placeholders = ", ".join(["?"] * len(values))
        sql = f"INSERT INTO tasks ({', '.join(columns)}) VALUES ({placeholders})"
        try:
            cur.execute(sql, values)
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
        self, conn: Connection, title_text: str, url: Optional[str] = None, notes: Optional[str] = None
    ) -> None:
        """Updates the title and optionally its URL and notes in the database and on the instance.
        If 'url' or 'notes' is None, those fields are not updated in the database.
        """
        cur = conn.cursor()

        fields_to_set = {"title": title_text}
        values_list = [title_text]

        if url is not None:
            fields_to_set["url"] = url
            values_list.append(url)

        if notes is not None:
            fields_to_set["notes"] = notes
            values_list.append(notes)

        set_clause = ", ".join(f"{key} = ?" for key in fields_to_set)
        values_list.append(self.id)

        sql = f"UPDATE tasks SET {set_clause} WHERE id = ?"

        try:
            cur.execute(sql, values_list)
            conn.commit()

            self.title = title_text
            if url is not None:
                self.url = url
            if notes is not None:
                self.notes = notes
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
    """Parse the entry text into a title and optional URL."""
    # use regex to find the first URL in entry_text and extract the URL and the rest of the text
    url_pattern = r"https?://.*?[^\s]+"
    match = re.search(url_pattern, entry_text)
    if match:
        url = match.group(0)
        title_text = entry_text.replace(url, "").strip()
    else:
        url = None
        title_text = entry_text.strip()
    return title_text, url
