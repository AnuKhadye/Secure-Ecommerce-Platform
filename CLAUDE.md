# CLAUDE.md: Secure E-Commerce Platform

Flask web app (Customer / Seller / Admin roles) built as a security-focused coursework project and used as a portfolio piece. The README and the owner's resume make security claims about it. **Every claim must be true in the code.** Read `FIXES.md` first: it is the list of open work.

## Stack
- Python 3, Flask 3.1, Flask-WTF (CSRF), Werkzeug (password hashing), SQLite, Jinja2, python-dotenv
- Bandit for static analysis (dev tool)

## Layout
- `app.py`: routes, session and cookie config, `role_required` decorator, checkout
- `forms.py`: Flask-WTF forms (register, login, set username)
- `db/database.py`: all SQL and the user/product/cart/review queries
- `templates/`, `static/`: Jinja2 templates and assets
- `.env.example`: copy to `.env` and set `SECRET_KEY`
- `FIXES.md`: checklist of agreed fixes (tick items as they are completed)

## Run
- Set `SECRET_KEY` (the app refuses to start without it). Generate one with: `python -c "import secrets; print(secrets.token_hex(32))"`
- Local development: set `FLASK_ENV=development` (this turns on debug and turns off the Secure cookie flag), then `python app.py`
- The SQLite database is created automatically on first import. It is git-ignored; never commit `*.db`, `.env` or `*.pyc`.
- There is no test suite yet. Until one exists, verify changes by running the app and exercising the changed route manually, and run `bandit -r . -x ./venv` after security-relevant changes.

## Rules
1. **Claims must match code.** If you change behaviour, update the README (and `FIXES.md`) in the same commit. If a README claim is false, fix the code or delete the claim; never leave it.
2. **SQL is parameterised only.** No f-strings, `%` or `+` in `execute()`. The one known exception to confirm is `PRAGMA table_info({table})` in `db/database.py` (see FIXES.md EC-8).
3. **All user input is validated server-side:** type, range and length, before it reaches the database.
4. **State-changing routes are POST with CSRF protection.** Keep `CSRFProtect` on.
5. **Authorisation is enforced in the route,** with `role_required` and ownership checks (for example a seller can only edit their own products). Never rely on the UI hiding a button.
6. **Secrets come from the environment.** No hardcoded keys. Do not print secret values in output or commits.
7. **Do not invent evidence.** Do not fabricate a threat model, Bandit output, test results or metrics. If the original material is missing, say so and ask the owner. Threat-model entries must be derived from the actual code and reviewed with the owner.
8. **Smallest change that fixes the issue.** Do not refactor unrelated code. Do not add dependencies unless a FIXES.md item calls for it, and add them to `requirements.txt` (UTF-8) or `requirements-dev.txt` for dev tools.

## Workflow for each fix
1. Read the relevant file(s) and the FIXES.md item.
2. Make the change.
3. Run the app and check the changed behaviour by hand (and re-run Bandit if security-related).
4. Update README wording if it described this behaviour.
5. Tick the item in `FIXES.md`, then commit with a message that names the item ID (for example `EC-1: use PBKDF2 for password hashing`).

## Owner preferences
- British spelling. Concise explanations. Ask before deleting files or rewriting history.

## Session log
- Read `SESSION_LOG.md` (git-ignored) at the start of a session for recent progress, decisions and next steps.
- Before ending a session, add a dated entry at the top: what was done, decisions, still open, next step.
