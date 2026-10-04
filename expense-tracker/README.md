# Expense Tracker Application

A full-featured modular Python Flask Expense Tracker web application with user authentication, category management, analytics dashboard, REST API, responsive UI, and interactive charts.

## Folder Structure

```
expense-tracker/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── instance/
│   └── expenses.db
│
├── app/
│   ├── routes/
│   ├── models/
│   ├── database/
│   ├── services/
│   ├── utils/
│   ├── templates/
│   └── static/
│
└── tests/
```

## Running the Application

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Initialize and seed database:
   ```bash
   python -m app.database.seed
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open browser at `http://127.0.0.1:5000`
