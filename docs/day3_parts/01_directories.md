## 2. 디렉터리별 역할과 작성해야 할 파일

FastAPI 프로젝트의 규모가 커지면 모든 코드를 `main.py` 한 파일에 작성하기 어렵다. API 엔드포인트, 입력값 검증, 비즈니스 규칙, 데이터베이스 쿼리와 ORM 모델을 역할에 따라 분리하면 각 코드의 책임이 명확해지고 수정 범위도 줄어든다.

이 템플릿은 다음과 같은 계층 방향을 기준으로 구성되어 있다.

```text
클라이언트 요청
    ↓
app/apis            HTTP 요청과 응답 처리
    ↓
app/schemas         요청 데이터 검증 및 응답 형태 정의
    ↓
app/services        비즈니스 규칙과 작업 순서 처리
    ↓
app/repositories    데이터베이스 조회·저장 처리
    ↓
app/models          SQLAlchemy ORM 테이블 정의
    ↓
app/core/db         데이터베이스 엔진·세션·공통 Base
```

응답은 반대 방향으로 전달된다. 하위 계층이 상위 계층을 직접 참조하지 않도록 의존 방향을 일정하게 유지하면 결합도를 낮출 수 있다.

| 디렉터리 | 핵심 역할 | 대표적으로 작성할 내용 |
| --- | --- | --- |
| `app/core/` | 프로젝트 공통 기반 설정 | 환경변수, DB 엔진·세션, 공통 ORM Mixin, 보안·로깅 설정 |
| `app/models/` | DB 테이블 구조 표현 | SQLAlchemy ORM 모델, 컬럼, 제약 조건, 관계 |
| `app/repositories/` | 데이터 접근 | 조회, 생성, 수정, 삭제, 검색 쿼리 |
| `app/schemas/` | API 데이터 형식 | Request·Response 모델, 입력값 검증 |
| `app/services/` | 비즈니스 로직 | 중복 검사, 권한 확인, 트랜잭션과 작업 순서 |
| `app/apis/` | HTTP 인터페이스 | URL, HTTP Method, 의존성 주입, 상태 코드 |

### 2.1 `app/core/`

#### 역할

`app/core/`는 특정 기능 하나에 속하지 않고 애플리케이션 전체에서 공통으로 사용하는 기반 코드를 관리한다. 환경변수, 데이터베이스 연결, 인증, 로깅처럼 여러 기능에서 반복적으로 필요한 설정을 한곳에 모으는 계층이다.

현재 템플릿에는 다음 파일이 준비되어 있다.

```text
app/core/
├── __init__.py
├── config.py
└── db/
    ├── __init__.py
    ├── databases.py
    └── models.py
```

#### 현재 파일의 기능

- `config.py`
  - `.env`에서 데이터베이스 환경변수를 읽는다.
  - `pydantic-settings`의 `BaseSettings`를 사용한다.
  - 애플리케이션 전체에서 사용할 `settings` 객체를 생성한다.
- `db/databases.py`
  - MySQL 비동기 연결 URL을 조합한다.
  - SQLAlchemy `AsyncEngine`을 생성한다.
  - `AsyncSessionLocal` 세션 팩토리를 만든다.
  - 모든 ORM 모델의 부모가 되는 `Base`를 선언한다.
  - FastAPI `Depends`에서 사용할 `async_get_db()`를 제공한다.
- `db/models.py`
  - 여러 ORM 모델에서 재사용할 공통 Mixin을 정의한다.
  - UUID 기본키, 생성·수정 시각, 논리 삭제 필드를 제공한다.

#### 추후 작성할 수 있는 파일

프로젝트 요구사항에 따라 다음 파일을 추가할 수 있다.

```text
app/core/
├── security.py       # 비밀번호 해싱, JWT 생성·검증
├── exceptions.py     # 공통 예외 클래스
├── logging.py        # 로깅 설정
├── constants.py      # 프로젝트 공통 상수
└── dependencies.py   # 공통 FastAPI 의존성
```

#### 작성 시 주의사항

- `.env`의 비밀번호나 인증 키를 코드에 직접 작성하지 않는다.
- `core`가 `apis`나 특정 기능의 `services`를 import하지 않도록 한다.
- 모든 설정을 `core`에 넣기보다 여러 기능에서 공통으로 사용하는 내용만 둔다.
- 개발·테스트·운영 환경에서 달라지는 값은 환경변수로 관리한다.

데이터베이스 연결 코드의 세부 동작과 환경변수 설정 방법은 별도의 데이터베이스 연결 파트에서 설명한다.

---

### 2.2 `app/models/`

#### 역할

`app/models/`는 SQLAlchemy ORM을 사용하여 데이터베이스 테이블 구조를 Python 클래스로 표현하는 디렉터리다. 각 모델 클래스는 테이블 이름, 컬럼, 자료형, 기본키, 외래키, 인덱스, 고유 제약 조건과 테이블 간 관계를 정의한다.

현재 템플릿에는 빈 `__init__.py`만 있으며, 실제 모델은 ERD를 확인한 뒤 기능 또는 테이블별 Python 파일로 작성해야 한다.

```text
app/models/
├── __init__.py
├── user.py
├── patient.py
└── medical_record.py
```

파일명은 팀 규칙에 따라 정할 수 있지만 `user.py`, `patient.py`처럼 하나의 도메인 또는 테이블을 알 수 있게 작성하는 것이 좋다.

#### 모델 파일에 작성할 내용

- `Base` 및 공통 Mixin 상속
- `__tablename__`
- 기본키와 일반 컬럼
- `nullable`, `unique`, `index` 등 제약 조건
- `ForeignKey`
- `relationship()`을 사용한 모델 간 관계
- 필요한 경우 Enum과 테이블 수준 제약 조건

간단한 형태는 다음과 같다.

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.databases import Base
from app.core.db.models import TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
```

위 코드는 디렉터리의 역할을 보여주기 위한 예시이며, 실제 컬럼과 관계는 과제에서 제공하는 ERD를 기준으로 작성해야 한다.

#### `app/models/__init__.py`의 중요성

이 템플릿의 `alembic/env.py`에는 다음과 같은 import가 있다.

```python
from app import models
```

Alembic의 자동 마이그레이션이 모든 테이블을 발견하려면 `app/models/__init__.py`에서 작성한 모델 모듈을 import해야 한다.

```python
from app.models.user import User
from app.models.patient import Patient

__all__ = ["User", "Patient"]
```

모델 파일만 만들고 `__init__.py`에서 불러오지 않으면 모델이 `Base.metadata`에 등록되지 않아 Alembic이 테이블 생성을 감지하지 못할 수 있다.

#### Model과 Schema의 차이

| 구분 | ORM Model | Pydantic Schema |
| --- | --- | --- |
| 위치 | `app/models/` | `app/schemas/` |
| 목적 | 데이터베이스 테이블 표현 | API 요청·응답 데이터 표현 |
| 주요 라이브러리 | SQLAlchemy | Pydantic |
| 비밀번호 필드 | DB 저장을 위해 포함 가능 | Response에서는 제외해야 함 |

#### 작성 시 주의사항

- 모델은 반드시 템플릿의 동일한 `Base`를 상속한다.
- Python 속성명과 실제 DB 컬럼명을 일관되게 관리한다.
- 외래키 컬럼과 `relationship()`의 양방향 관계를 확인한다.
- 이메일처럼 중복될 수 없는 값에는 DB 수준의 `unique` 제약도 적용한다.
- 모델 변경 후에는 Alembic 마이그레이션 파일을 생성하고 내용을 검토한다.

구체적인 모델 작성과 Alembic 명령은 SQLAlchemy·Alembic 파트에서 설명한다.

---

### 2.3 `app/repositories/`

#### 역할

`app/repositories/`는 Service가 필요로 하는 데이터를 데이터베이스에서 읽거나 저장하는 계층이다. SQLAlchemy의 `select`, `insert`, `update`, `delete` 문과 `AsyncSession`을 사용한 데이터 접근 코드를 모은다.

```text
app/repositories/
├── __init__.py
├── user_repository.py
├── patient_repository.py
└── medical_record_repository.py
```

#### Repository 파일에 작성할 내용

- 기본키를 이용한 단일 데이터 조회
- 조건을 이용한 조회
- 목록 조회와 페이지네이션
- ORM 객체 생성 및 추가
- 입력된 필드만 수정
- 실제 삭제 또는 논리 삭제
- 중복 확인을 위한 조회

예시는 다음과 같다.

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> User | None:
    statement = select(User).where(User.email == email)
    result = await db.execute(statement)
    return result.scalar_one_or_none()
```

#### Service와 Repository의 구분

Repository는 데이터를 어떻게 가져올지 담당하고, Service는 가져온 데이터를 이용해 어떤 업무 규칙을 적용할지 담당한다.

예를 들어 이메일 중복 가입을 방지할 때 다음과 같이 역할을 나눈다.

- Repository: 해당 이메일의 사용자가 존재하는지 조회
- Service: 사용자가 존재하면 가입을 거절하고, 없으면 생성 절차 진행

#### 트랜잭션 규칙

`commit()`을 Repository와 Service 중 어디에서 수행할지는 팀 규칙으로 통일해야 한다. 여러 Repository 작업을 하나의 트랜잭션으로 묶기 위해 다음 방식이 이해하기 쉽다.

- Repository: 객체 추가, 조회, 수정과 `flush()` 담당
- Service: 전체 작업 성공 시 `commit()`, 실패 시 `rollback()` 담당

프로젝트 전체에서 이 규칙이 섞이지 않도록 합의해야 한다.

#### 작성 시 주의사항

- Repository에서 `HTTPException`을 직접 발생시키지 않는다.
- Request·Response Schema보다 ORM 모델과 세션을 중심으로 작성한다.
- 비즈니스 판단과 권한 확인을 Repository에 넣지 않는다.
- `AsyncSession`을 사용할 때 DB 호출에 `await`를 빠뜨리지 않는다.
- 전체 행을 불필요하게 조회하지 않고 필요한 조건과 페이지네이션을 적용한다.

---

### 2.4 `app/schemas/`

#### 역할

`app/schemas/`는 API가 외부에서 받을 데이터와 외부로 반환할 데이터의 구조를 Pydantic 모델로 정의한다. 잘못된 값이 Service에 전달되기 전에 형식, 길이, 범위 등을 검증하고 응답에서 노출할 필드를 제한한다.

```text
app/schemas/
├── __init__.py
├── user.py
├── patient.py
└── medical_record.py
```

#### Schema 파일에 작성할 내용

하나의 기능에서도 용도에 따라 Schema를 분리한다.

- 생성 요청: `UserCreate`
- 수정 요청: `UserUpdate`
- 목록 또는 상세 응답: `UserResponse`
- 공통 필드: `UserBase`

```python
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=8, max_length=20)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    email: EmailStr
    name: str
```

`from_attributes=True`를 사용하면 SQLAlchemy ORM 객체의 속성을 읽어 Response Schema로 변환할 수 있다.

#### 작성 시 주의사항

- 생성·수정·응답 Schema를 하나로 합치지 않는다.
- 응답 Schema에는 비밀번호 해시나 내부 관리용 필드를 포함하지 않는다.
- 수정 요청의 선택 필드와 명시적으로 입력된 `null`을 어떻게 처리할지 정한다.
- 문자열 길이와 숫자 범위처럼 API에서 검증할 수 있는 조건을 명시한다.
- 데이터베이스의 `unique` 제약처럼 DB 조회가 필요한 검증은 Service에서 처리한다.

---

### 2.5 `app/services/`

#### 역할

`app/services/`는 애플리케이션의 핵심 비즈니스 규칙과 하나의 작업을 완료하기 위한 처리 순서를 담당한다. API와 Repository 사이에서 필요한 데이터를 조회하고, 업무 조건을 검사하고, 여러 데이터 변경을 하나의 트랜잭션으로 조합한다.

```text
app/services/
├── __init__.py
├── user_service.py
├── patient_service.py
└── medical_record_service.py
```

#### Service 파일에 작성할 내용

- 회원가입 시 이메일 중복 검사
- 비밀번호 해싱
- 로그인 인증
- 현재 사용자의 권한 확인
- 환자 등록 가능 여부 확인
- 여러 Repository 호출 조합
- 트랜잭션 `commit()`과 `rollback()`
- 도메인 예외 발생

간단한 회원 생성 흐름은 다음과 같이 표현할 수 있다.

```python
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import user_repository
from app.schemas.user import UserCreate


async def create_user(db: AsyncSession, data: UserCreate):
    existing_user = await user_repository.get_user_by_email(db, data.email)
    if existing_user is not None:
        raise DuplicateEmailError()

    password_hash = hash_password(data.password)
    user = await user_repository.create_user(db, data, password_hash)

    await db.commit()
    await db.refresh(user)
    return user
```

#### API와 Service의 구분

- API: 요청 수신, 의존성 주입, 상태 코드와 HTTP 응답 처리
- Service: 이메일 중복, 권한, 생성 조건 등 업무 규칙 처리

같은 Service는 HTTP API뿐 아니라 배치 작업이나 테스트에서도 재사용할 수 있어야 한다.

#### 작성 시 주의사항

- Service가 `Request`, `Response` 같은 HTTP 객체에 의존하지 않게 한다.
- 데이터 접근 쿼리를 Service에 직접 반복해서 작성하지 않는다.
- 실패 시 데이터가 일부만 저장되지 않도록 트랜잭션 범위를 관리한다.
- 외부 서비스 호출과 DB 변경이 함께 있을 때 실패 처리 방법을 정한다.
- 단순한 전달 함수만 과도하게 만들지 말고 실제 업무 규칙을 중심으로 작성한다.

---

### 2.6 `app/apis/`

#### 역할

`app/apis/`는 클라이언트와 애플리케이션을 연결하는 HTTP 인터페이스 계층이다. `APIRouter`를 사용하여 URL, HTTP Method, 요청 Schema, 응답 Schema, 상태 코드와 의존성을 정의한다.

현재 `app/main.py`의 catch-all 라우트는 `api/v1`로 시작하는 경로를 프런트엔드 경로 처리에서 제외한다. 따라서 프로젝트 API는 `/api/v1` prefix를 사용하는 구조가 자연스럽다.

```text
app/apis/
├── __init__.py
├── users.py
├── patients.py
└── medical_records.py
```

#### API 파일에 작성할 내용

- `APIRouter` 객체
- URL과 HTTP Method
- Path·Query·Body Parameter
- `Depends`를 통한 DB 세션과 인증 사용자 주입
- Request·Response Schema
- Service 호출
- HTTP 상태 코드
- 도메인 예외를 HTTP 오류로 변환하는 처리

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.schemas.user import UserCreate, UserResponse
from app.services import user_service


router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(async_get_db),
) -> UserResponse:
    return await user_service.create_user(db, data)
```

작성한 Router는 최종적으로 `app/main.py`에서 등록해야 한다.

```python
from app.apis.users import router as users_router

app.include_router(users_router)
```

#### 작성 시 주의사항

- API 함수 안에 SQLAlchemy 쿼리와 복잡한 비즈니스 로직을 모두 작성하지 않는다.
- 기능별 Router의 prefix와 tag 이름을 팀 규칙으로 통일한다.
- 적절한 HTTP Method와 상태 코드를 사용한다.
- 응답에는 반드시 Response Schema를 적용해 노출 필드를 통제한다.
- `/{path:path}`와 같은 catch-all 라우트보다 API Router가 먼저 등록되도록 구성한다.
- 인증이 필요한 API에는 현재 사용자 의존성을 명시한다.

---

### 2.7 계층별 책임 경계

하나의 회원가입 요청을 예로 들면 각 계층은 다음과 같이 역할을 나눈다.

| 처리 단계 | 담당 계층 |
| --- | --- |
| `POST /api/v1/users` 요청 수신 | `apis` |
| 이메일 형식, 이름 길이, 비밀번호 길이 검증 | `schemas` |
| 이메일 중복 가입 금지 규칙 적용 | `services` |
| 이메일로 기존 사용자 조회 | `repositories` |
| `users` 테이블과 컬럼 구조 제공 | `models` |
| DB 세션과 연결 제공 | `core/db` |
| 비밀번호를 제외한 응답 형태 결정 | `schemas` |
| `201 Created` 응답 반환 | `apis` |

이처럼 각 계층의 책임을 분리하면 데이터베이스가 변경되어도 API 코드의 수정 범위를 줄일 수 있고, 비즈니스 규칙을 독립적으로 테스트하기 쉬워진다.

### 2.8 패키지 작성 공통 규칙

- 각 디렉터리의 `__init__.py`는 해당 폴더를 Python 패키지로 인식하게 한다.
- 기능 또는 도메인 이름은 모든 계층에서 통일한다.

```text
app/models/user.py
app/repositories/user_repository.py
app/schemas/user.py
app/services/user_service.py
app/apis/users.py
```

- 의존 방향은 가급적 다음 순서를 유지한다.

```text
apis → services → repositories → models → core
```

- 순환 import가 발생하면 공통 타입이나 설정의 위치가 적절한지 다시 확인한다.
- 하나의 계층이 다른 계층의 책임을 대신하지 않도록 코드 리뷰에서 확인한다.
- 폴더만 만들고 끝내지 않고 실제 파일이 담당할 책임을 팀 규칙으로 정한다.

### 2.9 현재 템플릿 분석 결과

현재 `app/core/`에는 환경변수, 비동기 MySQL 연결, 공통 ORM Mixin이 구현되어 있다. 반면 `app/models/`, `app/repositories/`, `app/schemas/`, `app/services/`, `app/apis/`에는 `__init__.py`만 있고 기능 코드는 아직 작성되지 않았다.

따라서 이후 과제에서는 ERD와 API 요구사항을 기준으로 각 계층에 기능별 파일을 추가해야 한다. 이때 모델부터 API까지 한 기능의 이름을 일관되게 사용하고, `main.py`에는 애플리케이션 조립과 Router 등록만 남기는 방향이 적절하다.

### 2.10 참고 프로젝트 구조와 현재 템플릿 비교

학습 자료인 「Structuring a FastAPI Project: Best Practices」에서는 다음 구조를 예시로 제시한다.

```text
app/
├── main.py
├── dependencies.py
├── routers/
├── internal/
├── core/
├── models/
├── schemas/
├── services/
└── db/
```

FastAPI 프로젝트에 반드시 하나의 정답 구조가 있는 것은 아니다. 프로젝트 규모, 팀 규칙, 데이터베이스 접근 방식에 따라 디렉터리 이름과 계층 수가 달라질 수 있다. 첨부된 학습 자료와 현재 과제 템플릿의 개념은 다음과 같이 대응한다.

| 학습 자료의 구조 | 현재 템플릿 | 차이 및 해석 |
| --- | --- | --- |
| `app/routers/` | `app/apis/` | 이름은 다르지만 `APIRouter`와 엔드포인트를 관리하는 동일한 역할이다. |
| `app/db/` | `app/core/db/` | 현재 템플릿은 DB 연결을 프로젝트 공통 기반인 `core` 안에 배치했다. |
| `app/dependencies.py` | `app/core/db/databases.py` 등 | 현재 템플릿은 DB 세션 의존성 `async_get_db()`를 DB 설정 파일에 함께 둔다. 공통 의존성이 많아지면 별도 파일로 분리할 수 있다. |
| `app/internal/` | 별도 디렉터리 없음 | 관리자 전용 API가 필요하면 `app/apis/admin.py` 또는 별도의 `internal` 패키지를 추가할 수 있다. |
| Repository 계층 없음 | `app/repositories/` 존재 | 현재 템플릿은 Service에서 SQLAlchemy 쿼리를 분리해 데이터 접근 책임을 더 명확하게 나눈다. |
| 동기 `Session` | 비동기 `AsyncSession` | 현재 템플릿은 `asyncmy`, `create_async_engine`, `async_sessionmaker`를 사용하므로 DB 호출에 `await`가 필요하다. |

첨부 자료의 예시는 Service에서 ORM 모델을 직접 생성하고 `commit()`까지 수행한다. 소규모 프로젝트에서는 이 구조도 사용할 수 있지만, 현재 템플릿에는 Repository 디렉터리가 별도로 준비되어 있으므로 다음과 같이 한 단계 더 분리하는 것이 구조의 목적에 잘 맞는다.

```text
학습 자료: Router → Schema → Service → Model·Database
현재 템플릿: API → Schema → Service → Repository → Model·Database
```

또한 학습 자료에서는 `python-dotenv`와 `os.getenv()`를 사용하지만 현재 템플릿은 `pydantic-settings`의 `BaseSettings`를 사용한다. 두 방법 모두 환경변수를 읽는다는 목적은 같지만, `BaseSettings`는 설정값의 타입 선언과 검증을 함께 수행할 수 있다.

이 비교를 통해 디렉터리 이름 자체보다 각 계층이 어떤 책임을 맡고, 의존 방향이 일관되게 유지되는지가 더 중요하다는 것을 확인할 수 있다.

### 참고자료

- 「Structuring a FastAPI Project: Best Practices」, 제공된 학습 자료
- [FastAPI 공식 문서 - Bigger Applications: Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [SQLAlchemy 공식 문서 - Declarative Mapping](https://docs.sqlalchemy.org/en/20/orm/declarative_mapping.html)
- [SQLAlchemy 공식 문서 - Asynchronous I/O](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Pydantic 공식 문서 - Models](https://docs.pydantic.dev/latest/concepts/models/)
