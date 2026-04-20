# PythonProject

This repository contains a FastAPI task queue API with persistent storage, JWT authentication, and file logging.

## Features

- SQLite/PostgreSQL persistence via `DATABASE_URL`
- Task statuses: `pending`, `processing`, `done`, `error`
- JWT authentication with username/password
- Rate limiting
- Background worker with error handling
- Configurable settings via `.env`
- Requeues pending and processing tasks from the database on startup

## Run locally

1. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and adjust values:

```bash
copy .env.example .env
```

4. Start the API:

```bash
python main.py
```

Or directly with uvicorn:

```bash
uvicorn task_api:app --reload
```

## Run tests

```bash
pytest -q
```

## Docker

Build and run the container directly:

```bash
docker build -t task-api .
docker run --rm -p 8000:8000 --env-file .env task-api
```

Or use Docker Compose for local development and live reload of the project volume:

```bash
docker compose up --build
```

The `docker-compose.yml` file mounts the project folder into `/app`, passes `.env` into the container, and exposes port `8000`.

## Environment variables

Use `.env` or environment variables to configure the service.

```env
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///./tasks.db
# For PostgreSQL, use a URL like:
# DATABASE_URL=postgresql://user:password@localhost:5432/task_db
RATE_LIMIT=5
ACCESS_TOKEN_EXPIRE_SECONDS=3600
LOG_FILE=app.log
USER_CREDENTIALS=alice:alice123,bob:bobPassword
# For multiple users, add comma-separated username:password entries:
# USER_CREDENTIALS=alice:alice123,bob:bobPassword,charlie:charliePass
```

## API Endpoints

- `POST /token` - obtain JWT token using `username` and `password`
- `POST /tasks` - create a task
- `GET /tasks/{task_id}` - check task status and result

## Example requests

1. Request a token:

```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "alice123"}'
```

2. Create a task:

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"data": "hello"}'
```

3. Check task status:

```bash
curl http://localhost:8000/tasks/<TASK_ID> \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## Notes

- If `DATABASE_URL` is not provided, the app uses SQLite at `./tasks.db` by default.
- `USER_CREDENTIALS` defines one or more `username:password` pairs.
- Log output is written to the file configured by `LOG_FILE`.
- The service uses a runtime `asyncio.Queue` to dispatch tasks to the worker, while task state and results are persisted in the database.
- The app requeues any pending or processing tasks on startup.
