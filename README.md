# AI Health Web Assignment

## Docker 로 실행하기 (권장)

Docker Desktop 만 설치돼 있으면 아래 두 줄로 API·MySQL·Adminer 가 함께 뜬다.
`.env` 는 없으면 `.env.example` 을 복사해 자동 생성되므로 별도 준비가 필요 없다.

```bash
docker compose up -d --build
docker compose ps          # fastapi, mysql 이 healthy 면 정상
```

- API `http://localhost:8000` · Swagger `http://localhost:8000/docs` · Adminer `http://localhost:8080`
- 시드 관리자 계정: `admin@example.com` / `Passw0rd!!`
- 중지: `docker compose down` (데이터까지 초기화하려면 `docker compose down -v`)

| 문서 | 내용 |
|---|---|
| [Docker 환경 설정 가이드](./docs/docker_환경설정_가이드.md) | Windows / macOS 별 설치·설정·초기화·트러블슈팅 |
| [8일차 Docker Compose 문서](./docs/8일차_docker_compose.md) | 서비스 구성, `/app` 마운트, 자동 리로드, 실행 화면 |

## User API

4일차 과제의 User API는 SQLAlchemy 비동기 세션, Pydantic 검증, Argon2 비밀번호 해싱, JWT 인증을 사용합니다.

| Method | Endpoint | 기능 |
| --- | --- | --- |
| `POST` | `/api/v1/users/signup` | 회원가입 |
| `POST` | `/api/v1/users/login` | 로그인 |
| `POST` | `/api/v1/users/refresh` | Access Token 재발급 |
| `POST` | `/api/v1/users/logout` | 로그아웃 |
| `GET` | `/api/v1/users/me` | 내 정보 조회 |
| `PATCH` | `/api/v1/users/me` | 내 정보 수정 |
| `PATCH` | `/api/v1/users/me/password` | 비밀번호 변경 |
| `DELETE` | `/api/v1/users/me` | 회원 탈퇴 |
| `GET` | `/api/v1/admin/users` | 관리자 사용자 목록 조회 |
| `PATCH` | `/api/v1/admin/users/role` | 관리자 사용자 권한 수정 |

### 환경 설정

`.env.example`을 `.env`로 복사한 뒤 DB 접속 정보와 `JWT_SECRET_KEY`를 환경에 맞게 수정합니다. 실제 비밀키는 저장소에 커밋하지 않습니다.

### 실행 및 Swagger 확인

```bash
uv sync --group dev
uv run fastapi dev app/main.py
```

서버 실행 후 [http://localhost:8000/docs](http://localhost:8000/docs)에서 10개 User API를 확인할 수 있습니다.

### 자동 테스트

테스트는 실제 MySQL 데이터에 영향을 주지 않도록 격리된 SQLite DB에서 실행됩니다.

```bash
uv run pytest -q
```

## Alembic Migration Guide

이 프로젝트는 데이터베이스 마이그레이션을 위해 Alembic을 사용합니다.

### 1. 마이그레이션 파일 생성 (자동 생성)
모델(`app/models/`)이 변경된 경우 다음 명령어를 실행하여 마이그레이션 파일을 생성합니다.
```bash
uv run alembic revision --autogenerate -m "변경 내용 설명"
```

### 2. 데이터베이스에 반영
생성된 마이그레이션을 데이터베이스에 적용하려면 다음 명령어를 실행합니다.
```bash
uv run alembic upgrade head
```

### 3. 이전 상태로 되돌리기 (Rollback)
마지막 마이그레이션을 취소하려면 다음 명령어를 실행합니다.
```bash
uv run alembic downgrade -1
```
