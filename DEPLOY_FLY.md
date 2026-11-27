# Fly.io deployment: Flask + PostgreSQL

This repository is a Flask monolith: Flask renders the HTML and owns the
cookie-based login session. Its browser JavaScript calls relative URLs such as
`/api/dashboard`; it is not a separately deployable static frontend.

The no-redesign deployment is therefore:

```text
browser -> Vercel custom domain -> Vercel rewrite -> Fly Flask Machine -> PostgreSQL
```

The rewrite keeps the browser on the Vercel origin, so Flask's existing session
cookie and relative API calls continue to work. Do not use a cross-origin
`fetch()` to Fly for this session-based application: third-party cookies are
unreliable in modern browsers.

## Before deploy

`backups/expenses-20261102-pre-fly.db` is a legacy SQLite backup. This version
does not read SQLite files; migrate that data into PostgreSQL separately if you
need to preserve it. Keep a copy outside this repository before proceeding.

The application no longer needs a Fly Volume: all persistent data lives in
PostgreSQL. The app connects with `DATABASE_URL` and creates its tables on
startup.

## Provision and deploy in Singapore

Install and authenticate the Fly CLI, then run these commands from the project
root. Choose a globally unique app name in place of `YOUR_FLY_APP_NAME`.

```bash
fly launch --no-deploy --name YOUR_FLY_APP_NAME --region sin
```

Confirm `fly.toml` still contains `primary_region = 'sin'` and change its `app`
value to the name selected above. Create and attach a Fly Postgres cluster (or
point `DATABASE_URL` at another managed PostgreSQL instance):

```bash
fly postgres create --name YOUR_DB_APP_NAME --region sin
fly postgres attach --app YOUR_FLY_APP_NAME YOUR_DB_APP_NAME
fly secrets set SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')" --app YOUR_FLY_APP_NAME
fly deploy --app YOUR_FLY_APP_NAME
```

`fly postgres attach` sets the `DATABASE_URL` secret automatically. For an
external provider, set it yourself:

```bash
fly secrets set DATABASE_URL="postgresql://user:password@host:5432/expense_tracker" --app YOUR_FLY_APP_NAME
```

## Verify the database

The first request to the app creates the `users`, `transactions`, and `budgets`
tables. Check connectivity and table creation:

```bash
fly ssh console --app YOUR_FLY_APP_NAME -C 'python -c "import database; database.init_db(seed_sample_data=False); print(database.get_db_connection().close())"'
fly checks list --app YOUR_FLY_APP_NAME
```

A successful command prints `None` and exits with status 0. Avoid running
`init_db()` with `seed_sample_data=True` against a restored production database,
because it inserts the demo user when the `users` table is empty.

## Point Vercel at Fly

After the Fly health check is healthy, copy
`vercel.fly-proxy.json.example` over `vercel.json`, replace
`YOUR_FLY_APP_NAME`, and deploy Vercel. This removes the old Vercel Python
function and forwards all pages, static assets, auth routes, and API requests
to Fly while retaining the Vercel URL in the browser.

```bash
cp vercel.fly-proxy.json.example vercel.json
```

Do this only after substituting the actual Fly hostname. A Vercel rewrite is a
proxy, not a redirect, so the address bar remains your Vercel domain.

## Post-deploy checks

1. Visit `https://YOUR_FLY_APP_NAME.fly.dev/health`; it must return HTTP 200.
2. Use the Vercel URL to log in and add a test transaction.
3. Run `fly machine restart MACHINE_ID --app YOUR_FLY_APP_NAME`.
4. Reload the Vercel URL and confirm the test transaction remains.
5. Run `fly deploy --app YOUR_FLY_APP_NAME`, reload, and confirm it remains.

PostgreSQL backups are managed by the database provider. Export logical backups
periodically (for example with `pg_dump`) and store them outside Fly.
