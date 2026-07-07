# Tyre Business App

A multi-business Streamlit platform for tyre stock, sales, payments, outstanding balances, reports, low-stock alerts, business settings, and platform-owner administration.

The app can run in two ways:

- Local testing: uses `tyre_business.db` SQLite automatically when no cloud database is configured.
- Online deployment: uses PostgreSQL when `DATABASE_URL` is set in Streamlit secrets or environment variables.

No database password, platform owner password, or business user password is stored in the code. Business user passwords are stored as secure hashes.

## Files

- `app.py`: the Streamlit app.
- `requirements.txt`: Python packages needed by the app.
- `.gitignore`: keeps local databases, virtual environments, cache files, and local secrets out of Git.
- `tyre_business.db`: local SQLite database only. It is created automatically when running locally and is not needed online.

## Run Locally On Windows

Install Python from <https://www.python.org/downloads/windows/> if needed. During installation, tick **Add python.exe to PATH**.

Then open PowerShell in this folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open the local address Streamlit shows, usually:

```text
http://localhost:8501
```

## Local Secrets

For local platform-owner access, create `.streamlit/secrets.toml`:

```toml
PLATFORM_OWNER_EMAIL = "owner@example.com"
PLATFORM_OWNER_PASSWORD = "choose-a-private-owner-password"
SUPPORT_EMAIL = "your-support-email@example.com"
SUPPORT_WHATSAPP = "your-support-whatsapp-number"
```

For local PostgreSQL testing, also add:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require"
```

Do not upload `.streamlit/secrets.toml`.

## GitHub

Upload these files:

- `app.py`
- `requirements.txt`
- `README.md`
- `.gitignore`

Do not upload `.venv`, `__pycache__`, `.streamlit/secrets.toml`, `tyre_business.db`, backup `.db` files, or cache folders.

## Cloud PostgreSQL

Use Supabase or Neon. Copy the PostgreSQL connection string, for example:

```text
postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require
```

Keep the URL private.

## Streamlit Community Cloud

1. Go to <https://streamlit.io/cloud>.
2. Sign in with GitHub.
3. Create or update the app.
4. Main file path:

```text
app.py
```

5. Add Streamlit secrets:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require"
PLATFORM_OWNER_EMAIL = "owner@example.com"
PLATFORM_OWNER_PASSWORD = "choose-a-private-owner-password"
SUPPORT_EMAIL = "your-support-email@example.com"
SUPPORT_WHATSAPP = "your-support-whatsapp-number"
```

6. Deploy or reboot the app.

## Accounts

- Normal tyre businesses create their own account from the app.
- Each business sees only its own stock, customers, sales, payments, reports, settings, and low-stock records.
- The platform owner logs in with `PLATFORM_OWNER_EMAIL` and `PLATFORM_OWNER_PASSWORD` from Streamlit secrets.
- The platform owner can view platform totals, list businesses, suspend businesses, and reactivate businesses.

## Support Contact

- The Help page and business sidebar read support details from `SUPPORT_EMAIL` and `SUPPORT_WHATSAPP`.
- You can set them in Streamlit secrets or environment variables.
- If both are missing, the app shows `Support contact not configured yet.`

## Database Choice

- If `DATABASE_URL` exists, the app uses PostgreSQL.
- If Streamlit secrets contain `DATABASE_URL`, the app uses PostgreSQL.
- If no cloud database is configured, the app uses local SQLite and creates `tyre_business.db`.

## Important Notes

- `tyre_business.db` is not required for online deployment.
- Streamlit Community Cloud storage is not a safe permanent place for SQLite data, so online use should use Supabase or Neon PostgreSQL.
- Never paste database URLs, passwords, or owner credentials directly into `app.py`.
- If you change the app later, push updated files to GitHub and Streamlit Cloud will redeploy.
