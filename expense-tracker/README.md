# Personal Expense Tracker & Budget Management Web Application

A modern, minimalist financial management SaaS web application built with Python Flask, SQLite3, HTML5, CSS3, and Vanilla JavaScript. Features interactive SVG charts, dynamic spending velocity breakdowns, a real-time budget manager, instant expense logging, and search/filtering tools—with zero heavy front-end frameworks or external charting dependencies.

---

## Features

- **Dashboard ("Spending Overview")**:
  - Dynamic monthly spend summary, daily average, top expense category, and remaining budget.
  - Native SVG Stacked Spend Velocity Breakdown chart supporting `7D`, `30D`, `6M`, and `YTD` timeframes.
  - Native SVG Donut Category Share chart with responsive legends and center total display.
  - Quick Log panel for instant spend logging with amount stepper, quick presets (`₹50`, `₹100`, `₹200`, `₹500`), category picker, and optional notes.
  - Recent transactions list grouped by day with daily totals.

- **Transactions History**:
  - Full reverse-chronological transaction log grouped by date with daily totals.
  - Real-time search by notes and categories.
  - Category dropdown filter (`All`, `Food`, `Transport`, `Shopping`, `Bills`, `Entertainment`, `Health`, `Education`, `Travel`, `Other`).
  - Add, edit, and delete transactions with confirmation dialogs.
  - Immediate recalculation of all financial statistics.

- **Budget Management**:
  - Radial SVG progress indicator displaying percentage of budget consumed.
  - Custom monthly spending limit configuration with instant preset buttons (`₹15,000`, `₹25,000`, `₹40,000`, `₹60,000`).
  - "Where It Goes" category-wise spend progress bars.

- **Multi-User Isolation & Session Accounts**:
  - Starts a brand new personal expense list for every new user upon signup or guest start.
  - User-to-user data isolation: all transactions, budgets, and dashboard statistics are strictly scoped to the logged-in user in SQLite.
  - Sign up (`/register`), Log in (`/login`), and instant 1-click **Guest Mode** (`/guest`) for immediate private expense tracking.
  - Built-in Demo account (`demo` / `demo123`) pre-populated with realistic sample data for quick previewing.

- **Design System & Aesthetics**:
  - Clean light grey/off-white background with crisp white cards.
  - 12-14px border radii, subtle borders, and smooth micro-animations.
  - Indian Rupee (`₹`) numbering system throughout.
  - Fixed compact desktop sidebar with user profile avatar and mobile-friendly responsive navigation.

---

## Technology Stack

- **Backend**: Python 3, Flask, SQLite3, Flask sessions
- **Frontend**: HTML5, Vanilla CSS3 (Custom Design System), Vanilla JavaScript (ES6+)
- **Charts**: Custom Native SVG Charts (No Chart.js, D3, or external libraries)
- **Database**: SQLite3 (`expenses.db`) with parameterized SQL queries

---

## Project Structure

```
expense-tracker/
│
├── app.py                      # Flask application entry point and API routes
├── database.py                 # SQLite database connection, schema, and queries
├── expenses.db                 # SQLite database file (created on initialization)
├── requirements.txt            # Project dependencies
├── README.md                   # Setup and usage guide
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Shared layout, fixed sidebar, and modals
│   ├── dashboard.html          # Spending overview dashboard
│   ├── transactions.html       # Transactions history and filtering
│   └── budget.html             # Budget management and category tracking
│
├── static/
│   ├── css/
│   │   └── style.css           # Vanilla CSS design system matching reference UI
│   ├── js/
│   │   ├── dashboard.js        # Stacked bar & donut charts, stats, quick log
│   │   ├── transactions.js     # Search, filter, edit/delete actions
│   │   └── budget.js           # Circular progress gauge and limit controls
│   └── images/
│
└── tests/                      # Automated test suite
    ├── test_database.py        # Database operations & analytics tests
    ├── test_expenses.py        # API endpoints and template view tests
    └── test_auth.py            # Session and configuration tests
```

---

## Installation & Setup Instructions

### 1. Prerequisites
Ensure you have **Python 3.8+** installed:
```bash
python3 --version
```

### 2. Create and Activate a Virtual Environment

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database
The database (`expenses.db`) automatically initializes with schema and sample seed records upon first running the app. You can also manually run:
```bash
python3 -c "import database; database.init_db()"
```

### 5. Run the Application
```bash
python app.py
```

The application will start locally at:
```
http://127.0.0.1:5000
```
Open this URL in your web browser to view the application.

---

## Running the Automated Tests

Run the test suite using Python's built-in `unittest` runner:
```bash
python3 -m unittest discover tests
```

Or using `pytest`:
```bash
pytest -v
```

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Dashboard View |
| `/transactions` | `GET` | Transactions View |
| `/budget` | `GET` | Budget Management View |
| `/api/dashboard?period=30D` | `GET` | Dashboard KPIs, breakdown time-series, donut data, and recent transactions |
| `/api/transactions` | `GET` | Filtered transaction list with date grouping |
| `/api/budget` | `GET` | Monthly budget progress and category breakdown |
| `/api/add-transaction` | `POST` | Create a new transaction |
| `/api/update-transaction/<id>` | `POST/PUT`| Update an existing transaction |
| `/api/delete-transaction/<id>` | `POST/DELETE` | Delete a transaction |
| `/api/update-budget` | `POST` | Update monthly spending limit |
