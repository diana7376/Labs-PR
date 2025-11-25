import os
import asyncio
import random
import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI()

# --- Configuration ---
ROLE = os.getenv("ROLE", "follower")  # 'leader' or 'follower'
# Comma-separated list of follower URLs (e.g., "http://follower-1:80,...")
FOLLOWERS = os.getenv("FOLLOWERS", "").split(",") if os.getenv("FOLLOWERS") else []
WRITE_QUORUM = int(os.getenv("WRITE_QUORUM", "1"))
MIN_DELAY_MS = int(os.getenv("MIN_DELAY", "0"))
MAX_DELAY_MS = int(os.getenv("MAX_DELAY", "1000"))

# In-memory Key-Value Store
store: Dict[str, Any] = {}
lock = asyncio.Lock()  # To ensure local thread-safety


class WriteRequest(BaseModel):
    key: str
    value: Any


@app.get("/")
async def health():
    return {"role": ROLE, "status": "alive", "data_count": len(store)}


@app.get("/data")
async def get_data():
    """Endpoint to verify data consistency"""
    return store


@app.post("/replicate")
async def replicate(data: WriteRequest):
    """
    Follower Endpoint: Receives data from leader and commits it.
    """
    if ROLE == "leader":
        raise HTTPException(status_code=400, detail="Leader cannot receive replication")

    async with lock:
        store[data.key] = data.value
    return {"status": "replicated"}


async def replicate_to_follower(client: httpx.AsyncClient, url: str, data: dict):
    """
    Helper to send data to a single follower with simulated network lag.
    """
    if not url: return False

    # 1. Simulate Network Lag (Concurrent wait)
    delay = random.uniform(MIN_DELAY_MS, MAX_DELAY_MS) / 1000.0
    await asyncio.sleep(delay)

    # 2. Send Request
    try:
        resp = await client.post(f"{url}/replicate", json=data)
        return resp.status_code == 200
    except Exception as e:
        print(f"Failed to replicate to {url}: {e}")
        return False


@app.post("/write")
async def write(data: WriteRequest):
    """
    Leader Endpoint: Handles writes, replicates, and enforces Quorum.
    """
    if ROLE != "leader":
        raise HTTPException(status_code=400, detail="Only leader accepts writes")

    # 1. Local Write
    async with lock:
        store[data.key] = data.value

    # 2. Semi-Synchronous Replication
    # We create tasks for all followers to run concurrently
    async with httpx.AsyncClient() as client:
        tasks = [
            replicate_to_follower(client, follower_url, data.dict())
            for follower_url in FOLLOWERS if follower_url
        ]

        if not tasks:
            return {"status": "written_local_only"}

        # We need to wait until we get 'WRITE_QUORUM' acknowledgments.
        # asyncio.as_completed yields futures as they finish.
        acks = 0
        success = False

        # We process results as they come in
        for future in asyncio.as_completed(tasks):
            result = await future
            if result:
                acks += 1

            if acks >= WRITE_QUORUM:
                success = True
                break  # Quorum met!

        # Note: The remaining tasks continue in the background (eventually consistency)
        # but we don't wait for them to return the response to the user.

    if success:
        return {"status": "success", "quorum_met": True}
    else:
        # In a real system, you might roll back here.
        raise HTTPException(status_code=500, detail="Write quorum not met")