# 무료 배포 가이드 (Koyeb + TiDB Serverless)

이 앱을 **무료로** 실제 웹에 올리는 방법입니다.
- 웹 앱: **Koyeb** 무료 인스턴스 (카드 불필요, 512MB RAM)
- DB: **TiDB Serverless** (MySQL 호환, 무료 5GB, 카드 불필요)
- 이미지 저장: 컨테이너 로컬(임시) — 재배포 시 초기화됨(데모용)

> ⚠️ **메모리 주의**: 무료 인스턴스는 512MB입니다. 이 앱은 torch 를 **예측 요청 시에만** 로딩하도록
> 최적화돼 있어 평상시엔 가볍지만, AI 예측을 동시에 여러 번 호출하면 메모리 초과(OOM)로 재시작될
> 수 있습니다. 안정적으로 쓰려면 Koyeb 유료(작은 인스턴스) 또는 RAM 1GB 인 Cloud Run 을 고려하세요.

---

## 1. TiDB Serverless (무료 MySQL) 만들기

1. https://tidbcloud.com 가입 → **Create Cluster** → **Serverless** (무료) 선택
2. 클러스터 생성 후 **Connect** 클릭 → 접속 정보 확인:
   - Host (예: `gateway01.xxx.prod.aws.tidbcloud.com`)
   - Port: **4000**
   - User (예: `xxxxxxx.root`)
   - Password (직접 설정)
3. SQL 콘솔 또는 클라이언트에서 데이터베이스 생성:
   ```sql
   CREATE DATABASE ai_health;
   ```
   > TiDB 는 TLS 연결이 필수입니다 → 배포 시 `DB_SSL=true` 로 설정합니다(아래).

## 2. Koyeb 에 앱 배포

1. https://www.koyeb.com 가입 (GitHub 계정으로 로그인 가능)
2. **Create Service** → **GitHub** → 이 저장소 선택 → 브랜치 `main`
3. **Builder**: Dockerfile (자동 감지됨)
4. **Instance**: `Free` 선택
5. **Ports**: `8000` (Koyeb 가 `PORT` 를 주입하면 앱이 자동으로 그 포트를 사용)
6. **Environment variables** 에 아래 값 입력:

   | 변수 | 값 | 설명 |
   |---|---|---|
   | `DB_HOST` | TiDB Host | 예: `gateway01....tidbcloud.com` |
   | `DB_PORT` | `4000` | TiDB 포트 |
   | `DB_USER` | TiDB User | 예: `xxxx.root` |
   | `DB_PASSWORD` | TiDB Password | (secret 으로) |
   | `DB_NAME` | `ai_health` | 위에서 만든 DB |
   | `DB_SSL` | `true` | TiDB TLS 필수 |
   | `JWT_SECRET_KEY` | 긴 랜덤 문자열 | (secret) 로그인 토큰 서명 |
   | `REFRESH_COOKIE_SECURE` | `true` | HTTPS 환경 |
   | `SEED_ADMIN_EMAIL` | 원하는 관리자 이메일 | 공개 사이트용 |
   | `SEED_ADMIN_PASSWORD` | **강한 비밀번호** | 공개 사이트용 (기본값 쓰지 말 것) |

7. **Deploy** → 빌드가 끝나면 컨테이너가 시작되며 entrypoint 가 자동으로:
   - DB 연결 대기 → `alembic upgrade head`(스키마 생성) → 시드(admin+환자2명) → 서버 기동

## 3. 접속 & 로그인

- 배포 완료 후 Koyeb 이 제공하는 URL (예: `https://your-app-xxx.koyeb.app`) 접속
- 로그인: `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` 로 지정한 값
  (미지정 시 기본 `admin@example.com` / `Passw0rd!!` — 공개 배포에선 반드시 변경)

## 4. 제약 및 참고

- **이미지 임시 저장**: 업로드한 X-ray 는 컨테이너 디스크에 저장되어 **재배포/재시작 시 사라집니다**.
  영속화하려면 Cloudflare R2 / Supabase Storage 같은 무료 오브젝트 스토리지 연동이 필요합니다(추가 개발).
- **콜드/슬립**: Koyeb 무료 인스턴스는 잠들지 않지만, 리소스 초과 시 재시작될 수 있습니다.
- **로컬 개발은 그대로**: `docker compose up -d` 는 기존처럼 로컬 MySQL + 자동 리로드로 동작합니다
  (`UVICORN_RELOAD=1` 이 compose 에 설정됨). 배포 환경에선 리로드가 꺼집니다.

## 5. 대안: Cloud Run (더 안정적, 카드 필요)

512MB 가 부족하면 Google Cloud Run 에 같은 이미지로 배포하고 메모리를 **1GB** 로 설정하세요.
월 무료 할당량 내에서 torch 예측이 안정적으로 동작합니다. DB 는 동일하게 TiDB Serverless 사용.
