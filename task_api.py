import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from auth import authenticate_user, create_token, verify_token
from config import LOG_FILE
from database import SessionLocal, Task as DbTask, get_db, init_db
from models import TaskCreate, TaskStatus, LoginRequest, TaskState
from storage import rate_limiter, queue
from worker import worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("task_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized")

    with SessionLocal() as db:
        pending_tasks = db.query(DbTask).filter(
            DbTask.status.in_([TaskState.pending.value, TaskState.processing.value])
        ).all()

        for stored_task in pending_tasks:
            stored_task.status = TaskState.pending.value
            await queue.put(stored_task.id)

        if pending_tasks:
            db.commit()
            logger.info("Requeued %d tasks from the database", len(pending_tasks))

    asyncio.create_task(worker())
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/token")
async def login(login_request: LoginRequest):
    if not authenticate_user(login_request.username, login_request.password):
        logger.warning("Unauthorized login attempt for user %s", login_request.username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_token(login_request.username)
    logger.info("Token created for user %s", login_request.username)
    return {"access_token": token}


@app.post("/tasks", dependencies=[Depends(rate_limiter)])
async def create_task(task: TaskCreate, user: str = Depends(verify_token), db=Depends(get_db)):
    task_id = str(uuid.uuid4())
    db_task = DbTask(id=task_id, status=TaskState.pending.value, data=task.data, result=None, user=user)

    try:
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        await queue.put(task_id)
        logger.info("Task %s created by user %s", task_id, user)
        return {"task_id": task_id}
    except SQLAlchemyError as err:
        db.rollback()
        logger.exception("Database error while creating task %s", task_id)
        raise HTTPException(status_code=500, detail="Failed to create task") from err


@app.get("/tasks/{task_id}", response_model=TaskStatus, dependencies=[Depends(rate_limiter)])
async def get_task(task_id: str, user: str = Depends(verify_token), db=Depends(get_db)):
    try:
        task = db.get(DbTask, task_id)
    except SQLAlchemyError as err:
        logger.exception("Database error while reading task %s", task_id)
        raise HTTPException(status_code=500, detail="Failed to retrieve task") from err

    if not task:
        logger.warning("Task %s not found for user %s", task_id, user)
        raise HTTPException(status_code=404, detail="Task not found")

    if task.user != user:
        logger.warning("Forbidden access to task %s by user %s", task_id, user)
        raise HTTPException(status_code=403, detail="Forbidden")

    return TaskStatus(id=task.id, status=task.status, result=task.result)


# uvicorn task_api:app --reload
