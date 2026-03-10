# Platform Engineer Interview — Containerize This App

This repository contains a small Python web application. Your task is to **containerize it** and demonstrate platform engineering best practices.

## Your Task

1. **Provide a production-style Dockerfile** that:
   - Builds and runs this application correctly.
   - Uses a minimal base image and keeps the final image small.
   - Does not run the process as root (use a non-root user).
   - Correctly handles all application dependencies. Some dependencies require system libraries; you are expected to resolve any build or runtime errors (e.g. by installing the right system packages in the image).

2. **Optionally**, add a **docker-compose** setup that runs the app together with Postgres and/or Redis, and wire the app to use them via environment variables (e.g. `DATABASE_URL`, `REDIS_URL`). The app already has optional endpoints that use these when configured.

## Success Criteria

- The container starts and serves the application.
- `GET /health` returns HTTP 200 with `{"status":"ok"}`.
- `POST /image-info` works with an image file upload (returns dimensions/format).
- `POST /hash` with a JSON body `{"value":"hello"}` returns a SHA-256 hash.
- The process inside the container does **not** run as root (use `GET /run-as-root` to verify; tests expect `"root": false`).
- The final image does **not** include unnecessary build tools or development packages.

## Running the App Locally (without Docker)

From the project root:

```bash
cd app
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Run tests by executing:
python tests/run.py

## API Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness/readiness check |
| `/run-as-root` | GET | Whether process runs as root; expect `{"root": false, "uid": ...}` |
| `/image-info` | POST | Upload an image; returns format, dimensions |
| `/hash` | POST | Body `{"value":"string"}`; returns SHA-256 hex |
| `/cache/{key}` | GET/POST | Optional: get/set Redis value (if `REDIS_URL` set) |
| `/db/now` | GET | Optional: current DB time (if `DATABASE_URL` set) |

