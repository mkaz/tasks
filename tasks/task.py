from datetime import datetime
from enum import Enum
from typing import Optional
import re

from pydantic import BaseModel, Field, field_validator


class TaskState(str, Enum):
    NOW = "Now"
    BACKLOG = "Backlog"
    LATER = "Later"
    DONE = "Done"
    ARCHIVE = "Archive"

    def __str__(self) -> str:
        return self.value


class Task(BaseModel):
    id: int = Field(..., ge=1)
    title: str = Field(..., min_length=1)
    priority: int = Field(2, ge=0, le=4)
    state: TaskState = Field(default=TaskState.BACKLOG)
    dt_created: datetime
    dt_completed: Optional[datetime] = None
    url: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("title cannot be empty")
        return title

    @field_validator("url", "notes", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return value.strip() or None

    @field_validator("dt_completed", mode="before")
    @classmethod
    def normalize_dt_completed(cls, value):
        if value in (None, "", 0, "0"):
            return None
        return value


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
