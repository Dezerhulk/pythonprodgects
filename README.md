

This project provides a FastAPI-based task queue API with persistent storage and task status tracking.

## Features

- SQLite/PostgreSQL persistence via `DATABASE_URL`
- Task statuses: `pending`, `processing`, `done`, `error`
- JWT authentication
- Rate limiting
- Error handling and logging

## Run locally

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Create a `.env` file or set environment variables:

```env
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///./tasks.db
RATE_LIMIT=5
ACCESS_TOKEN_EXPIRE_SECONDS=3600
LOG_FILE=app.log
```

3. Start the API:

```bash
uvicorn task_api:app --reload
```

## Endpoints

- `POST /token` - get JWT token
- `POST /tasks` - create a task
- `GET /tasks/{task_id}` - get task status/result

## Notes

- The default database is SQLite.
- For PostgreSQL, set `DATABASE_URL` like `postgresql+psycopg2://user:password@host:port/dbname`.
