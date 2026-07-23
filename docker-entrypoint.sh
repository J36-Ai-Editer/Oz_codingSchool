#!/usr/bin/env sh
# ---------------------------------------------------------------------------
# 컨테이너 시작 시:
#   1) MySQL 이 접속 가능해질 때까지 대기
#   2) Alembic 마이그레이션으로 스키마 생성/최신화
#   3) 테스트 시드 데이터 생성 (멱등 - 이미 있으면 건너뜀)
#   4) uvicorn 으로 FastAPI(+SimpleCNN) 기동
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

echo "[entrypoint] Seeding test data (idempotent) ..."
python -m app.seed || echo "[entrypoint] seed 건너뜀/실패 (서버는 계속 기동)"

echo "[entrypoint] Starting API server (SimpleCNN loads on import) ..."
# 호스팅(Koyeb 등)은 PORT 를 주입한다. 로컬 개발에선 UVICORN_RELOAD=1 로 자동 리로드.
SERVE_PORT="${PORT:-8000}"
if [ -n "${UVICORN_RELOAD:-}" ]; then
    # 감시 대상을 소스 디렉터리로 한정한다.
    # (/app 전체를 감시하면 .venv 의 수만 개 파일까지 폴링해 CPU 를 낭비한다)
    exec uvicorn app.main:app --host 0.0.0.0 --port "${SERVE_PORT}" \
        --reload --reload-dir /app/app --reload-dir /app/worker
else
    exec uvicorn app.main:app --host 0.0.0.0 --port "${SERVE_PORT}"
fi
