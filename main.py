"""
Platform Engineer Interview — sample Python web app.
Containerize this app with a production-style Dockerfile.
"""
import os
from io import BytesIO

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import database_available, redis_available

app = FastAPI(
    title="Platform Interview App",
    description="Sample app for Dockerfile exercise.",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    """Liveness/readiness: returns 200 when the app is running."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Root check (success criteria: process should not run as root)
# ---------------------------------------------------------------------------

@app.get("/run-as-root")
def run_as_root():
    """
    Return whether the process is running as root (uid 0).
    For success criteria, this should return {"root": false, "uid": <non-zero>}.
    """
    print(f"os.getuid(): {os.getuid()}")
    uid = os.getuid()
    euid = os.geteuid()
    return {"root": uid == 0, "uid": uid, "euid": euid}


# ---------------------------------------------------------------------------
# Image info (Pillow)
# ---------------------------------------------------------------------------

@app.post("/image-info")
async def image_info(file: UploadFile = File(...)):
    """
    Accept an image upload and return dimensions and format using Pillow.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload must be an image")
    try:
        from PIL import Image
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Pillow not available: {e}") from e
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        img = Image.open(BytesIO(contents))
        img.load()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}") from e
    return {
        "format": img.format,
        "mode": img.mode,
        "width": img.size[0],
        "height": img.size[1],
    }


# ---------------------------------------------------------------------------
# Hash (cryptography)
# ---------------------------------------------------------------------------

class HashRequest(BaseModel):
    value: str


class HashResponse(BaseModel):
    sha256_hex: str


@app.post("/hash", response_model=HashResponse)
def hash_value(req: HashRequest):
    """
    Hash the given string with SHA-256 using the cryptography library.
    """
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.backends import default_backend
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"cryptography not available: {e}") from e
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(req.value.encode("utf-8"))
    return HashResponse(sha256_hex=digest.finalize().hex())


# ---------------------------------------------------------------------------
# Optional: Redis cache (for docker-compose exercise)
# ---------------------------------------------------------------------------

@app.get("/cache/{key}")
def cache_get(key: str):
    """Return a cached value if Redis is configured and the key exists."""
    if not redis_available():
        return JSONResponse(
            status_code=503,
            content={"detail": "Redis not configured (set REDIS_URL)"},
        )
    try:
        import redis
        from app.config import REDIS_URL
        r = redis.from_url(REDIS_URL)
        value = r.get(key)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    if value is None:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"key": key, "value": value.decode("utf-8")}


@app.post("/cache/{key}")
def cache_set(key: str, value: str):
    """Set a cached value if Redis is configured."""
    if not redis_available():
        return JSONResponse(
            status_code=503,
            content={"detail": "Redis not configured (set REDIS_URL)"},
        )
    try:
        import redis
        from app.config import REDIS_URL
        r = redis.from_url(REDIS_URL)
        r.set(key, value)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return {"key": key, "status": "ok"}


# ---------------------------------------------------------------------------
# Optional: Database read (for docker-compose exercise)
# ---------------------------------------------------------------------------

@app.get("/db/now")
async def db_now():
    """Return current database timestamp if Postgres is configured."""
    if not database_available():
        return JSONResponse(
            status_code=503,
            content={"detail": "Database not configured (set DATABASE_URL)"},
        )
    try:
        import asyncpg
        from app.config import DATABASE_URL
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            row = await conn.fetchrow("SELECT NOW() AS now")
            return {"now": str(row["now"])}
        finally:
            await conn.close()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
