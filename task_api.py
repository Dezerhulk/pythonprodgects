import asyncio
import time
import uuid
from typing import Dict, Optional, List

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import jwt

# ===================== CONFIG =====================
SECRET_KEY = "supersecret"
ALGORITHM = "HS256"
RATE_LIMIT = 5  # requests per second

app = FastAPI()
security = HTTPBearer()

# ===================== MODELS =====================
class TaskCreate(BaseModel):
    data: str = Field(..., min_length=1, max_length=1000)

class TaskStatus(BaseModel):
    id: str
    status: str
    result: Optional[str] = None

# ===================== STORAGE =====================
tasks: Dict[str, dict] = {}
queue: asyncio.Queue[str] = asyncio.Queue()
rate_limit_store: Dict[str, List[float]] = {}

# ===================== AUTH =====================
def create_token(username: str) -> str:
    payload = {"sub": username, "exp": time.time() + 3600}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ===================== RATE LIMIT =====================
def rate_limiter(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    timestamps = rate_limit_store.setdefault(ip, [])

    rate_limit_store[ip] = [t for t in timestamps if now - t < 1]

    if len(rate_limit_store[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many requests")

    rate_limit_store[ip].append(now)

# ===================== WORKER =====================
async def worker() -> None:
    while True:
        task_id = await queue.get()
        tasks[task_id]["status"] = "processing"

        await asyncio.sleep(2)
        result = tasks[task_id]["data"].upper()

        tasks[task_id]["status"] = "done"
        tasks[task_id]["result"] = result

        queue.task_done()


@app.on_event("startup")
async def startup_event() -> None:
    asyncio.create_task(worker())

# ===================== ROUTES =====================
@app.post("/token")
async def login(username: str):
    return {"access_token": create_token(username)}


@app.post("/tasks", dependencies=[Depends(rate_limiter)])
async def create_task(task: TaskCreate, user: str = Depends(verify_token)):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": "pending",
        "data": task.data,
        "result": None,
        "user": user,
    }

    await queue.put(task_id)
    return {"task_id": task_id}


@app.get("/tasks/{task_id}", response_model=TaskStatus, dependencies=[Depends(rate_limiter)])
async def get_task(task_id: str, user: str = Depends(verify_token)):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task["user"] != user:
        raise HTTPException(status_code=403, detail="Forbidden")

    return TaskStatus(id=task_id, status=task["status"], result=task["result"])

# ===================== RUN =====================
# uvicorn task_api:app --reload
