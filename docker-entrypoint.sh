#!/usr/bin/env sh
# ---------------------------------------------------------------------------
# 컨테이너 시작 시:
#   1) MySQL 이 접속 가능해질 때까지 대기
#   2) Alembic 마이그레이션으로 스키마 생성/최신화
#   3) uvicorn 으로 FastAPI(+SimpleCNN) 기동
# ---------------------------------------------------------------------------
set -e

DB_HOST="${DB_HOST:-mysql}"
DB_PORT="${DB_PORT:-3306}"

echo "[entrypoint] Waiting for database at ${DB_HOST}:${DB_PORT} ..."
python - <<'PY'
import os, socket, sys, time

host = os.environ.get("DB_HOST", "mysql")
port = int(os.environ.get("DB_PORT", "3306"))
deadline = time.time() + 120
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            print("[entrypoint] Database is reachable.")
            sys.exit(0)
    except OSError:
        time.sleep(2)
print("[entrypoint] Database not reachable within 120s.", file=sys.stderr)
sys.exit(1)
PY

echo "[entrypoint] Running Alembic migrations ..."
alembic upgrade head

echo "[entrypoint] Starting API server (SimpleCNN loads on import) ..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
