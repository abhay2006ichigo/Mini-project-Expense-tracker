# Backend Module (Person 3)

## Overview
This directory contains the Flask application routes, business logic services, and validation/formatting utilities.

## Responsibilities
- **routes/**: Blueprint definitions for authentication (`auth_routes.py`), expense management (`expense_routes.py`), analytics (`dashboard_routes.py`), and JSON APIs (`api_routes.py`).
- **services/**: Business logic layer decoupling SQL operations from endpoints (`auth_service.py`, `expense_service.py`, `analytics_service.py`).
- **utils/**: Form validators (`validators.py`) and data formatters (`helpers.py`).
