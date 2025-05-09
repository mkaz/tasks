# Changelog

## v2.2.1 - 2025-05-09

- Add tests
- Add link emoji 🔗 to tasks with URL specified


## v2.2.0 - 2025-05-08

- Remove database table to track schema
    - Create new `migrate` command
    - Build schema based on database structure

- Change A,B,C modes to simpler Now / Later


## v2.1.3 - 2025-05-07

- Added URL field to tasks #1
- Add new command `open` that accepts id and opens URL
- Add new database table to track schema version and migrate
