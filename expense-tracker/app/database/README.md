# Database Module (Person 4)

## Overview
This directory handles data persistence, SQLite schema definition, data models, and database seeding.

## Responsibilities
- **models/**: Python data classes representing `User`, `Expense`, and `Category`.
- **db.py**: SQLite database connection helper (`get_db`, `close_db`, `init_db`).
- **schema.sql**: DDL scripts defining `users`, `categories`, and `expenses` tables.
- **seed.py**: Script populating default categories and sample test user data.
