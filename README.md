# 💰 Expense Tracker

A full-stack personal expense tracking web application built using **Python, Flask, SQLite, HTML, CSS, and JavaScript**.

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
- SQLite
- SQLAlchemy / SQLite3

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
│
├── instance/
│   └── expenses.db
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
SQLite Database
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
expenses
categories
```

Relationship:

```text
USER
 │
 │ 1:N
 ▼
EXPENSE
 │
 │ N:1
 ▼
CATEGORY
```

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
2. Do not commit the SQLite database unless explicitly required.
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

Run the application:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

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
