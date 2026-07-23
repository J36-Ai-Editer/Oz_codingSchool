# Docker 환경 설정 가이드 (Windows / macOS)

이 저장소를 **처음 받는 팀원**이 Docker 로 서버를 띄우기까지의 전체 과정을 OS별로 정리한 문서다.
서비스 구성과 과제 조건은 [8일차 Docker Compose 문서](./8일차_docker_compose.md)를 참고한다.

## 0. 한눈에 보기

```bash
# 1) Docker Desktop 설치 (OS별 1장·2장 참고)
# 2) 저장소 클론
git clone https://github.com/J36-Ai-Editer/Oz_codingSchool.git
cd Oz_codingSchool

# 3) 실행 — .env 준비 불필요 (없으면 .env.example 로 자동 생성)
docker compose up -d --build
```

접속: API `http://localhost:8000` · Swagger `http://localhost:8000/docs` · Adminer `http://localhost:8080`
로그인: `admin@example.com` / `Passw0rd!!` (시드 계정)

---

## 1. Windows 설정

### 1.1 요구사항

| 항목 | 조건 |
|---|---|
| OS | Windows 10 22H2 이상 또는 Windows 11 (64bit) |
| CPU | 가상화 지원 + BIOS/UEFI 에서 가상화 활성화 |
| 백엔드 | WSL 2 (Docker Desktop 기본값) |
| 메모리 | 8GB 이상 권장 (torch 추론 포함) |

작업 관리자 → 성능 → CPU 에서 **가상화: 사용** 인지 먼저 확인한다. `사용 안 함` 이면 BIOS 에서
Intel VT-x / AMD-V 를 켜야 한다.

### 1.2 WSL 2 설치

관리자 권한 PowerShell 에서:

```powershell
wsl --install          # 미설치 시 Ubuntu 와 WSL2 를 함께 설치
wsl --update           # 이미 설치돼 있다면 최신화
wsl --status           # 기본 버전이 2 인지 확인
```

설치 후 재부팅한다.

### 1.3 Docker Desktop 설치

```powershell
winget install Docker.DockerDesktop
```

또는 https://www.docker.com/products/docker-desktop 에서 설치 파일을 받는다.
설치 마법사에서 **"Use WSL 2 instead of Hyper-V"** 를 체크한 상태로 진행한다.

### 1.4 WSL 통합 켜기 (중요)

Docker Desktop → **Settings → Resources → WSL Integration** → 사용 중인 배포판(Ubuntu 등) 토글 ON → **Apply & restart**

- 이 설정을 켜야 WSL 터미널에서 `docker` 명령을 쓸 수 있다.
- 켜지 않으면 WSL 안에서 `The command 'docker' could not be found` 가 뜬다.
  이때는 Windows 쪽 CLI 를 직접 호출하면 된다: `docker.exe compose up -d --build`

### 1.5 설치 확인

```powershell
docker version
docker compose version
docker run --rm hello-world
```

### 1.6 Git 줄바꿈 설정 (Windows 전용 주의)

컨테이너 엔트리포인트는 리눅스 셸 스크립트라 **CRLF 로 저장되면 실행되지 않는다**
(`exec /app/docker-entrypoint.sh: no such file or directory`).

이 저장소는 `.gitattributes` 에 `*.sh text eol=lf` 를 지정해 두어 자동으로 LF 로 체크아웃되지만,
전역 설정도 아래처럼 맞춰 두는 것이 안전하다.

```powershell
git config --global core.autocrlf input
```

이미 문제가 생겼다면 해당 파일만 다시 받으면 된다.

```powershell
git rm --cached docker-entrypoint.sh
git checkout -- docker-entrypoint.sh
```

### 1.7 소스 위치와 코드 자동 반영

- `D:\` 같은 **Windows 드라이브**에 두면 파일 변경 이벤트(inotify)가 컨테이너로 전달되지 않는다.
  그래서 compose 에 `WATCHFILES_FORCE_POLLING=true` 를 설정해 폴링 방식으로 감지하도록 해 두었다.
- 더 빠른 반응 속도와 I/O 성능을 원하면 **WSL 파일시스템 안**(`\\wsl$\Ubuntu\home\<user>\...`)에
  클론하는 것을 권장한다. 이 경우 폴링 없이도 리로드가 동작한다.

---

## 2. macOS 설정

### 2.1 요구사항

| 항목 | 조건 |
|---|---|
| OS | macOS 13 (Ventura) 이상 |
| CPU | Apple Silicon(M1~) 또는 Intel |
| 메모리 | 8GB 이상 권장 (Docker 에 4GB 이상 할당) |

### 2.2 Docker Desktop 설치

```bash
# Homebrew 사용 시
brew install --cask docker-desktop     # 구버전 Homebrew 에서는 `brew install --cask docker`
```

또는 https://www.docker.com/products/docker-desktop 에서 칩에 맞는 dmg
(**Apple Chip** / **Intel Chip**)를 받아 설치한다.

Apple Silicon 사용자는 x86 이미지 실행을 위해 Rosetta 를 함께 설치한다.

```bash
softwareupdate --install-rosetta --agree-to-license
```

설치 후 **Applications → Docker** 를 실행해 메뉴 바에 고래 아이콘이 뜨는지 확인한다
(데몬이 떠 있어야 CLI 가 동작한다).

### 2.3 리소스 설정

Docker Desktop → **Settings → Resources**

- **Memory**: 4GB 이상 (폐렴 예측 시 torch 가 메모리를 사용한다)
- **File sharing**: **VirtioFS** 선택 (기본값, 바인드 마운트 성능이 가장 좋다)

### 2.4 설치 확인

```bash
docker version
docker compose version
docker run --rm hello-world
```

### 2.5 Apple Silicon(M1~) 주의사항 — 반드시 확인

이 프로젝트의 MySQL 드라이버 `asyncmy` 는 **linux/arm64 용 미리 빌드된 휠을 제공하지 않는다.**
따라서 Apple Silicon 에서 네이티브 arm64 로 이미지를 빌드하면 소스 컴파일이 필요해
`uv sync` 단계에서 빌드가 실패할 수 있다.

**해결: amd64 이미지로 빌드/실행한다(Rosetta 에뮬레이션).**

```bash
# 이번 셸에서만 적용
export DOCKER_DEFAULT_PLATFORM=linux/amd64
docker compose up -d --build

# 매번 적용하려면 셸 프로필에 추가
echo 'export DOCKER_DEFAULT_PLATFORM=linux/amd64' >> ~/.zshrc
source ~/.zshrc
```

- Docker Desktop → Settings → General 의 **"Use Rosetta for x86/amd64 emulation"** 을 켜면 속도가 개선된다.
- 참고: `mysql:8.0`, `adminer:5`, `python:3.13-slim` 은 arm64 이미지를 제공하므로 문제가 없고,
  `torch`/`torchvision` 도 arm64 CPU 휠이 있다. 걸리는 것은 `asyncmy` 하나다.
- 네이티브 arm64 로 돌리고 싶다면 Dockerfile 에 빌드 도구(`build-essential`)를 추가해
  `asyncmy` 를 컴파일하는 방법도 있으나, 이미지가 커지고 빌드 시간이 늘어난다(현재 저장소에는 미적용).

### 2.6 포트 확인

`8000`, `8080`, `3307` 을 사용한다. 이미 사용 중인 포트가 있으면 아래로 확인 후 정리한다.

```bash
lsof -i :8000
```

---

## 3. 공통 — 실행 · 확인 · 초기화

명령은 모두 **프로젝트 루트**에서 실행한다.
(WSL 에서 통합을 켜지 않았다면 `docker` 대신 `docker.exe` 를 쓴다)

### 3.1 실행

```bash
docker compose up -d --build     # 빌드 + 백그라운드 실행
docker compose ps                # 상태 확인 (fastapi, mysql 이 healthy 여야 정상)
docker compose logs -f fastapi   # 로그 실시간 확인
docker compose down              # 중지 (데이터 유지)
```

기동 시 자동으로 처리되는 순서:

1. `.env` 가 없으면 `.env.example` 을 복사해 생성
2. MySQL 이 준비될 때까지 대기
3. `alembic upgrade head` 로 스키마 생성/최신화
4. 시드 데이터 생성(관리자 1명, 환자 2명 — 이미 있으면 건너뜀)
5. `uvicorn --reload` 로 API 기동

### 3.2 초기화

| 목적 | 명령 |
|---|---|
| 데이터(DB·업로드 이미지)만 초기화 | `docker compose down -v --remove-orphans` |
| 컨테이너·볼륨·빌드 이미지까지 초기화 | `docker compose down -v --rmi local --remove-orphans` |
| 로컬 설정까지 초기화 | 위 명령 후 `rm -f .env && rm -rf media` |
| 빌드 캐시 정리 | `docker builder prune -f` |
| 도커 전체 정리(다른 프로젝트 영향) | `docker system prune -a --volumes` ⚠️ |

> ⚠️ `.env` 를 지울 때는 **반드시 `-v` 로 DB 볼륨도 함께 지운다.** 새로 만들어진 `.env` 의 계정과
> 기존 볼륨에 초기화돼 있던 MySQL 계정이 달라 인증에 실패하기 때문이다.

### 3.3 최신 코드로 다시 세팅

```bash
git fetch origin
git checkout main
git reset --hard origin/main     # 로컬 변경을 버리고 원격 상태로 맞춤
docker compose up -d --build
```

---

## 4. 트러블슈팅

| 증상 | OS | 원인 / 해결 |
|---|---|---|
| `command 'docker' could not be found` | Windows(WSL) | WSL Integration 미설정 → 설정 켜거나 `docker.exe` 사용 |
| `exec /app/docker-entrypoint.sh: no such file or directory` | Windows | 셸 스크립트가 CRLF → `core.autocrlf input` 후 파일 재체크아웃 |
| `ports are not available ... 3306` | 공통 | 로컬 MySQL 이 3306 점유. 기본 노출 포트는 3307 이며, 겹치면 `.env` 의 `DB_PORT` 변경 |
| `8000 포트 충돌` | 공통 | 로컬 uvicorn 종료 또는 compose `ports` 를 `8001:8000` 으로 변경 |
| `Access denied for user` | 공통 | `.env` 와 기존 DB 볼륨의 계정 불일치 → `docker compose down -v` 후 재기동 |
| 빌드 중 `asyncmy` 컴파일 실패 | macOS(Apple Silicon) | `export DOCKER_DEFAULT_PLATFORM=linux/amd64` 후 재빌드 |
| 코드 수정이 반영되지 않음 | 공통 | `docker compose logs fastapi` 에 `WatchFiles detected changes` 가 찍히는지 확인 (Windows 는 폴링 설정 필요 — 이미 적용됨) |
| 컨테이너가 계속 재시작됨 | 공통 | `docker compose logs fastapi` 로 원인 확인. 메모리 부족이면 Docker 할당 메모리 상향 |
| `docker daemon is not running` | macOS | Docker Desktop 앱이 실행 중인지(메뉴바 아이콘) 확인 |

## 5. 명령어 치트시트

```bash
docker compose up -d --build      # 빌드 + 실행
docker compose ps                 # 상태
docker compose logs -f fastapi    # 로그
docker compose exec fastapi bash  # 컨테이너 접속
docker compose exec fastapi uv run --group dev pytest -q   # 컨테이너 안에서 테스트(15개 통과)
docker compose restart fastapi    # 재시작
docker compose down               # 중지
docker compose down -v            # 중지 + 데이터 삭제
```
