# Tyre Business App

A Streamlit web app for managing tyre stock, sales, payments, outstanding balances, and profit reports.

The app can run in two ways:

- Local testing: uses `tyre_business.db` SQLite automatically.
- Online deployment: uses PostgreSQL when `DATABASE_URL` is set in Streamlit secrets or environment variables.

No database password or app password is stored in the code.

## Files

- `app.py`: the Streamlit app.
- `requirements.txt`: Python packages needed by the app.
- `.gitignore`: keeps local databases, virtual environments, cache files, and local secrets out of Git.
- `tyre_business.db`: local SQLite database only. It is created automatically when running locally and is not needed online.

## Run Locally On Windows

First install Python from <https://www.python.org/downloads/windows/> if it is not already installed.
During installation, tick **Add python.exe to PATH**.

Then open PowerShell in this folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks the activate command, run this once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then run the activate command again:

```powershell
.\.venv\Scripts\Activate.ps1
```

When Streamlit starts, it will show a local web address such as:

```text
http://localhost:8501
```

Open that address in your browser.

## Prepare GitHub

1. Create a GitHub account if you do not already have one.
2. Create a new GitHub repository.
3. Upload these project files to the repository:
   - `app.py`
   - `requirements.txt`
   - `README.md`
   - `.gitignore`
4. Do not upload `tyre_business.db`, backup `.db` files, `.venv`, `__pycache__`, or `.streamlit/secrets.toml`.

## Create A Cloud PostgreSQL Database

Use either Supabase or Neon. Both provide a PostgreSQL database URL.

### Option 1: Supabase

1. Go to <https://supabase.com/>.
2. Create a new project.
3. Open the project database settings.
4. Find the PostgreSQL connection string.
5. Copy the connection string that looks similar to:

```text
postgresql://postgres:YOUR_PASSWORD@HOST:5432/postgres
```

### Option 2: Neon

1. Go to <https://neon.tech/>.
2. Create a new project.
3. Open the connection details.
4. Copy the PostgreSQL connection string.
5. It usually looks similar to:

```text
postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require
```

Keep this URL private. It is the password to the online database.

## Deploy On Streamlit Community Cloud

1. Go to <https://share.streamlit.io/> or <https://streamlit.io/cloud>.
2. Sign in with GitHub.
3. Click **New app**.
4. Choose the GitHub repository for this app.
5. Set the main file path to:

```text
app.py
```

6. Open **Advanced settings**.
7. Add these secrets:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require"
APP_PASSWORD = "choose-a-private-password-here"
```

8. Deploy the app.
9. Share the app link with your brother.

## Streamlit Secrets

For online deployment, put the database URL and app password in Streamlit Cloud secrets:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require"
APP_PASSWORD = "choose-a-private-password-here"
```

This app also supports this format:

```toml
[database]
url = "postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require"
```

For local testing with secrets, create `.streamlit/secrets.toml` on your own computer and add the same value there.
That file is ignored by Git so the password does not get uploaded.

## App Password

The app uses `APP_PASSWORD` from Streamlit secrets to protect all pages.

When `APP_PASSWORD` is set, users must enter the correct password before they can see:

- Dashboard
- Add Stock
- View Stock
- Search Tyres
- Record Sale
- Outstanding Balances
- Sales Report

After login, the app remembers the user in the browser session, so they do not need to type the password again when changing pages.

To log out, click **Logout** in the sidebar.

For local testing, you can create `.streamlit/secrets.toml`:

```toml
APP_PASSWORD = "your-local-test-password"
```

If `APP_PASSWORD` is not set, the app still runs locally but shows a warning that password protection is missing.

## How The Database Choice Works

- If `DATABASE_URL` exists, the app uses PostgreSQL.
- If Streamlit secrets contain `DATABASE_URL`, the app uses PostgreSQL.
- If Streamlit secrets contain `[database] url = "..."`, the app uses PostgreSQL.
- If no cloud database is configured, the app uses local SQLite and creates `tyre_business.db`.

## Important Notes

- `tyre_business.db` is not required for online deployment.
- Streamlit Community Cloud storage is not a safe permanent place for SQLite data, so online use should use Supabase or Neon PostgreSQL.
- Never paste database passwords or app passwords directly into `app.py`.
- If you change the app later, push the updated files to GitHub and Streamlit Cloud will redeploy.
