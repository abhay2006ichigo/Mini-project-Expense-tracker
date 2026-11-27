# Database Module (Person 4)

## Overview
This directory handles data persistence, PostgreSQL schema definition, data models, and database seeding.

## Responsibilities
- **models/**: Python data classes representing `User`, `Expense`, and `Category`.
- **db.py**: PostgreSQL database connection helper (`get_db`, `close_db`, `init_db`).
- **schema.sql**: DDL scripts defining `users`, `transactions`, and `budgets` tables.
- **seed.py**: Script populating default categories and sample test user data.
