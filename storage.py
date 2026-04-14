



import asyncio
import logging
import time
from typing import Dict, List

from fastapi import HTTPException, Request

from config import RATE_LIMIT

queue: asyncio.Queue[str] = asyncio.Queue()
rate_limit_store: Dict[str, List[float]] = {}

logger = logging.getLogger("task_app.storage")


def rate_limiter(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    timestamps = rate_limit_store.setdefault(ip, [])
    rate_limit_store[ip] = [t for t in timestamps if now - t < 1]

    if len(rate_limit_store[ip]) >= RATE_LIMIT:
        logger.warning("Rate limit exceeded for %s", ip)
        raise HTTPException(status_code=429, detail="Too many requests")

    rate_limit_store[ip].append(now)
