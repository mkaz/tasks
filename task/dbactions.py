from sqlite3 import Connection


def create_schema(conn: Connection):
    """Create schema. Will not overwrite if exists"""
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            task TEXT NOT NULL,
            dt_completed DATETIME DEFAULT 0,
            dt_created DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def insert_task(conn: Connection, task: str) -> int:
    """Insert task into database"""
    sql = "INSERT INTO tasks (task) VALUES (?)"
    cur = conn.cursor()
    cur.execute(sql, [task])
    conn.commit()

    return cur.lastrowid
