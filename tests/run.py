#!/usr/bin/env python3
"""
Run API tests for README success criteria.
Usage: python run.py  or  BASE_URL=http://localhost:8080 python run.py
"""
import base64
import json
import os
import sys
from pathlib import Path

try:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlencode
except ImportError:
    from urllib2 import Request, urlopen, HTTPError, URLError
    from urllib import urlencode

SCRIPT_DIR = Path(__file__).resolve().parent
FIXTURES = SCRIPT_DIR / "fixtures"
SAMPLE_PNG = FIXTURES / "sample.png"

# Minimal 1x1 PNG (smallest valid PNG)
SAMPLE_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")

fail_count = 0


def ensure_fixture():
    FIXTURES.mkdir(parents=True, exist_ok=True)
    if not SAMPLE_PNG.exists():
        SAMPLE_PNG.write_bytes(base64.b64decode(SAMPLE_PNG_B64))


def check(name: str, resp, expect_status: int = 200):
    """Expect exact status (default 200)."""
    global fail_count
    if resp.status == expect_status:
        print(f"PASS {name}")
    else:
        print(f"FAIL {name}")
        fail_count += 1


def check_bonus(name: str, resp):
    """Bonus endpoints: pass on 200 or 404."""
    global fail_count
    if resp.status in (200, 404):
        print(f"PASS {name}")
    else:
        resp.read()  # consume body
        print(f"FAIL {name}")
        fail_count += 1


def check_non_root(name: str, resp):
    """Must be 200 and JSON has root: false."""
    global fail_count
    body = resp.read().decode()
    if resp.status != 200:
        print(f"FAIL {name}")
        fail_count += 1
        return
    try:
        data = json.loads(body)
        if data.get("root") is False:
            print(f"PASS {name}")
        else:
            print(f"FAIL {name}")
            fail_count += 1
    except json.JSONDecodeError:
        print(f"FAIL {name}")
        fail_count += 1


def request(method: str, path: str, data=None, json_body=None, files=None):
    """Perform request and return response (or raise)."""
    url = f"{BASE_URL}{path}"
    headers = {}
    body = None
    if json_body is not None:
        body = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if data is not None:
        body = data.encode("utf-8") if isinstance(data, str) else data
    if files:
        # multipart/form-data for file upload
        boundary = "----FormBoundary7MA4YWxkTrZu0gW"
        parts = []
        for key, (filename, content, content_type) in files.items():
            ct = content_type or "application/octet-stream"
            header = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'
                f"Content-Type: {ct}\r\n\r\n"
            )
            parts.append(header.encode())
            parts.append(content)
            parts.append(b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    req = Request(url, data=body, headers=headers, method=method)
    return urlopen(req)


def main():
    global fail_count
    ensure_fixture()
    print(f"Testing {BASE_URL}")
    print("---")

    # 1. GET /health
    try:
        r = request("GET", "/health")
        check("GET /health", r)
    except (HTTPError, URLError) as e:
        print(f"FAIL GET /health")
        fail_count += 1

    # 2. POST /image-info
    try:
        with open(SAMPLE_PNG, "rb") as f:
            content = f.read()
        r = request("POST", "/image-info", files={"file": ("sample.png", content, "image/png")})
        check("POST /image-info", r)
    except HTTPError as e:
        print(f"FAIL POST /image-info")
        fail_count += 1
    except Exception:
        print(f"FAIL POST /image-info")
        fail_count += 1

    # 3. POST /hash (value=hello)
    try:
        r = request("POST", "/hash", json_body={"value": "hello"})
        check("POST /hash (value=hello)", r)
    except HTTPError as e:
        print(f"FAIL POST /hash (value=hello)")
        fail_count += 1

    # 4. GET /run-as-root (non-root)
    try:
        r = request("GET", "/run-as-root")
        check_non_root("GET /run-as-root (non-root)", r)
    except HTTPError as e:
        print(f"FAIL GET /run-as-root (non-root)")
        fail_count += 1

    # GET /cache/{key}
    try:
        r = request("GET", "/cache/test-key")
        check_bonus("GET /cache/{key}", r)
    except HTTPError as e:
        body_bytes = e.read()
        r = type("R", (), {"status": e.code, "read": lambda self, b=body_bytes: b})()
        check_bonus("GET /cache/{key}", r)
    except Exception:
        print(f"FAIL GET /cache/{{key}}")
        fail_count += 1

    # POST /cache/{key}
    try:
        r = request("POST", f"/cache/bonus-key?{urlencode({'value': 'bonus-value'})}")
        check_bonus("POST /cache/{key}", r)
    except HTTPError as e:
        body_bytes = e.read()
        r = type("R", (), {"status": e.code, "read": lambda self, b=body_bytes: b})()
        check_bonus("POST /cache/{key}", r)
    except Exception:
        print(f"FAIL POST /cache/{{key}}")
        fail_count += 1

    # GET /db/now
    try:
        r = request("GET", "/db/now")
        check_bonus("GET /db/now", r)
    except HTTPError as e:
        body_bytes = e.read()
        r = type("R", (), {"status": e.code, "read": lambda self, b=body_bytes: b})()
        check_bonus("GET /db/now", r)
    except Exception:
        print(f"FAIL GET /db/now")
        fail_count += 1

    # POST /hash (value=empty)
    try:
        r = request("POST", "/hash", json_body={"value": ""})
        check("POST /hash (value=empty)", r)
    except HTTPError as e:
        print(f"FAIL POST /hash (value=empty)")
        fail_count += 1

    print("---")
    if fail_count == 0:
        print("All success-criteria checks passed.")
        return 0
    print("Some checks failed.")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
