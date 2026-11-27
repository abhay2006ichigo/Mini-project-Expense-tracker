# 💰 Expense Tracker

A full-stack personal expense tracking web application built using **Python, Flask, PostgreSQL, HTML, CSS, and JavaScript**.

The project allows users to securely manage their expenses, categorize transactions, and visualize their spending through a dashboard.

---

## 🛠️ Tech Stack

### Frontend
- HTML5
- CSS3
- JavaScript
- Chart.js

### Backend
- Python
- Flask
- Flask Sessions
- Werkzeug

### Database
- PostgreSQL
- psycopg 3

### Development
- Git
- GitHub
- VS Code

---

# 👥 Team Structure

The project is divided into four major responsibilities.

| Person | Role | Folder |
|---|---|---|
| Person 1 | Frontend/UI | `app/frontend/` |
| Person 2 | JavaScript/API Integration | `app/frontend-js/` |
| Person 3 | Backend/Flask | `app/backend/` |
| Person 4 | Database | `app/database/` |

---

# 📁 Project Structure

```text
expense-tracker/
│
├── README.md
├── requirements.txt
├── .gitignore
├── app.py
├── config.py
├── database.py
│
├── app/
│   │
│   ├── frontend/
│   │   ├── README.md
│   │   ├── templates/
│   │   └── static/css/
│   │
│   ├── frontend-js/
│   │   ├── README.md
│   │   └── static/js/
│   │
│   ├── backend/
│   │   ├── README.md
│   │   ├── routes/
│   │   ├── services/
│   │   └── utils/
│   │
│   └── database/
│       ├── README.md
│       ├── models/
│       ├── db.py
│       ├── schema.sql
│       └── seed.py
│
└── tests/
```

---

# 🚀 Features

## Authentication

- User registration
- User login
- User logout
- Password hashing
- Session management

## Expense Management

- Add expense
- Edit expense
- Delete expense
- View expenses
- Categorize expenses
- Filter expenses
- Search expenses

## Dashboard

- Total expenses
- Monthly expenses
- Category-wise spending
- Recent transactions
- Monthly spending chart
- Category distribution chart

---

# 🔄 Application Flow

```text
User
 │
 ▼
HTML/CSS/JavaScript
 │
 │ HTTP Request
 ▼
Flask Backend
 │
 │ Database Query
 ▼
PostgreSQL Database
 │
 │ Data
 ▼
Flask Backend
 │
 │ HTML / JSON
 ▼
Frontend
```

---

# 🔌 API Contract

The frontend and backend communicate through defined API endpoints.

### Authentication

```text
POST /api/register
POST /api/login
POST /api/logout
```

### Expenses

```text
GET    /api/expenses
POST   /api/expenses
GET    /api/expenses/<id>
PUT    /api/expenses/<id>
DELETE /api/expenses/<id>
```

### Dashboard

```text
GET /api/dashboard
GET /api/dashboard/monthly
GET /api/dashboard/categories
```

The backend team must document any changes to these endpoints before merging.

---

# 🗄️ Database

Main tables:

```text
users
transactions
budgets
```

Relationship:

```text
USER
  │
  ├── 1:N ──► TRANSACTIONS
  │
  └── 1:N ──► BUDGETS
```

Tables are created automatically on startup. Set `DATABASE_URL` before running the app or the test suite.


---

# 🌿 Git Workflow

Never directly work on `main`.

Create a feature branch:

```bash
git checkout -b feature/your-feature
```

Example:

```bash
git checkout -b frontend/dashboard
```

After completing the feature:

```bash
git add .
git commit -m "Add dashboard UI"
git push origin feature/frontend-dashboard
```

Then create a Pull Request on GitHub.

---

# 📌 Team Rules

1. Do not modify another person's module without discussing it first.
2. Do not commit database credentials or connection strings.
3. Do not commit passwords, API keys, or secrets.
4. Pull the latest `main` before starting new work.
5. Use meaningful commit messages.
6. Test your changes before creating a Pull Request.
7. Keep API contracts consistent.
8. Do not rename shared files without informing the team.

---

# ⚙️ Installation

Clone the repository:

```bash
git clone <REPOSITORY_URL>
cd expense-tracker
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it.

### macOS/Linux

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a PostgreSQL database and set its connection URL:

```bash
createdb expense_tracker
export DATABASE_URL="postgresql://postgres:password@localhost:5432/expense_tracker"
```

Run the tests (requires a separate, disposable database):

```bash
export TEST_DATABASE_URL="postgresql://postgres:password@localhost:5432/expense_tracker_test"
pytest
```

Run the application:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5001
```

---

# 🚀 Deployment

The app ships with production configuration for the most common Python hosts.

### Environment variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Flask session signing key. Set this in production. | Development key |
| `PORT` | Port the server listens on. | `5001` locally, `8000` in Docker |
| `HOST` | Bind address when running `python app.py`. | `0.0.0.0` |
| `FLASK_DEBUG` | Set to `1` to enable the debugger locally. Keep `0` in production. | `0` |
| `DATABASE_URL` | PostgreSQL connection URL used by the app. | `postgresql://postgres@localhost:5432/expense_tracker` |
| `TEST_DATABASE_URL` | PostgreSQL connection URL used only by the test suite. Tests skip without it. | — |

Copy `.env.example` to `.env` and adjust the values for local or server use.

### Docker (any host)

```bash
docker build -t expense-tracker .
docker run -p 8000:8000 \
  -e SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')" \
  -e DATABASE_URL="postgresql://user:password@host:5432/expense_tracker" \
  expense-tracker
```

The container connects to PostgreSQL using `DATABASE_URL`; data is persisted by the database server. The `/health` endpoint is used as the container health check.

### Render / Railway / Heroku

These platforms read the included `Procfile`:

```text
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 60
```

Set `SECRET_KEY` and `DATABASE_URL` in the dashboard, pointing to a managed PostgreSQL instance.

### Vercel

Vercel detects the Flask `app` in `app.py` automatically; `vercel.json` configures the function. Set `SECRET_KEY` in the project environment variables.

> **Note:** Vercel Functions have an ephemeral filesystem, but all data lives in PostgreSQL. Set `DATABASE_URL` to a hosted PostgreSQL instance so every function instance shares the same durable data.

### Health check

```text
GET /health
```

Returns `{"status": "ok"}` when the app and database are reachable.

---

# 🧪 Testing

Run:

```bash
pytest
```

All contributors should test their module before opening a Pull Request.

---

# 🎯 Development Goal

Build a clean, modular, secure and responsive expense tracker that demonstrates:

- Frontend development
- REST API development
- Flask architecture
- Database design
- Authentication
- CRUD operations
- Data visualization
- Git/GitHub collaboration

---

## 📜 License

This project is developed for educational purposes.
