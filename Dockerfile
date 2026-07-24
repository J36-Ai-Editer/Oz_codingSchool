# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# AI Health API 이미지
# - FastAPI 앱(app/)과 SimpleCNN 추론 코드(worker/)를 한 이미지에 담는다.
# - worker/model.py 는 import 시점에 SimpleCNN state_dict 를 로딩하므로
#   torch/torchvision/pillow 와 worker/models/*.pth 가 이미지에 포함돼야 한다.
# ---------------------------------------------------------------------------
FROM python:3.13-slim-bookworm

# uv 바이너리 복사 (의존성 설치·잠금 파일 준수용)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# 헬스체크(curl) 및 빌드에 필요한 최소 시스템 패키지
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1) 의존성만 먼저 설치해 레이어 캐시를 활용한다 (소스 변경 시 재설치 방지)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# 2) 애플리케이션 + 워커(모델 포함) 소스 복사
COPY . .

# 엔트리포인트: DB 대기 → 마이그레이션 → uvicorn
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
