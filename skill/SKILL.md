---
name: tasks
description: Manage a persistent todo list with the Tasks command-line app. Use when the user asks to capture, list, prioritize, inspect, edit, or complete tasks, or asks the coding harness to maintain their task list.
license: MIT
compatibility: Requires the `tasks` command-line app and access to its SQLite database.
---

# Tasks CLI

Use the installed `tasks` command to manage the user's todo list. Treat the database as user data: inspect the selected database before changing it, and never manipulate its SQLite file directly.

## Before running commands

1. Check that the CLI is available with `command -v tasks`.
2. Run `tasks --info` to report the selected database and version before the first mutation in a session.
3. If the user specifies a database, put the global option before the subcommand: `tasks --db PATH COMMAND`.
4. If the selected database is ambiguous or unexpected, ask which database to use before writing.

The app may select a local `tasks.db` based on the current directory. Do not create or switch databases implicitly.

## Common operations

```bash
# List active tasks
tasks show

# List only tasks in the Now state
tasks show --now

# Inspect one task before changing it
tasks show TASK_ID

# Add a task
tasks add "TASK TITLE"

# Add a high-priority task in the Now state
tasks add --state Now --priority 1 "TASK TITLE"

# Complete a task
tasks do TASK_ID

# Show the weekly report
tasks show --week
```

Priorities run from `0` (highest) through `4` (lowest). Supported states are `Now`, `Backlog`, `Later`, `Done`, and `Archive`.

A URL can be included in an added task. The app stores the first URL separately from the title:

```bash
tasks add "Review proposal https://example.com/proposal"
```

## Safe workflow

- List or inspect tasks freely.
- Before completing a task, resolve its exact numeric ID and inspect it if the user's reference is not unambiguous.
- Add or complete tasks only when the user requests the mutation. Report the task ID and result afterward.
- `tasks edit TASK_ID` is interactive. Run it only when the user can interact with the terminal; otherwise explain that the current CLI has no non-interactive edit command.
- The CLI has no delete command. Do not bypass it with direct SQL.
- Do not infer that a task is complete merely because its state is `Done`; use `tasks do TASK_ID` when the user asks to complete it.
- Quote titles and database paths in shell commands.
