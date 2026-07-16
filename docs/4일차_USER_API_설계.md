# 4일차 User API 설계

## 1. 문서 목적

이 문서는 AI 헬스케어 웹 서비스의 User API를 구현하기 전에 사용자 요구사항, HTTP 인터페이스, 데이터 검증, 인증·권한, 예외 처리 기준을 합의하기 위한 API 명세서다.

설계 근거는 다음과 같다.

- `static/apis.js`에 명시된 `REQ-USER-001`부터 `REQ-USER-009`
- 로그인 토큰 발급에 관한 `NFR-USER-001`
- 회원가입·마이페이지·관리자 회원 관리 화면에서 실제로 사용하는 입력값
- `app/models/user.py`의 SQLAlchemy `User` 모델
- `app/models/enums.py`의 성별·부서·권한 열거형

모든 Endpoint의 공통 Prefix는 `/api/v1`이다. 비밀번호 원문과 `hashed_password`는 어떤 응답에도 포함하지 않는다.

## 2. 요구사항 요약

| ID | 사용자 요구사항 | 인증·권한 | 핵심 규칙 |
| --- | --- | --- | --- |
| REQ-USER-001 | 사내 구성원이 이메일, 비밀번호, 이름, 부서, 성별, 전화번호로 회원가입한다. | 불필요 | 이메일·전화번호 중복 금지, 비밀번호 해싱, 최초 권한 `PENDING` |
| REQ-USER-002 | 가입된 이메일과 비밀번호로 로그인한다. | 불필요 | 활성 계정과 올바른 비밀번호 확인 |
| REQ-USER-003 | 로그인된 사용자가 로그아웃한다. | 필요 | Refresh Token을 더 이상 사용할 수 없게 처리 |
| REQ-USER-004 | 관리자가 전체 사용자 목록을 조회한다. | 관리자 | 이름·이메일 검색, 부서 필터 지원 |
| REQ-USER-005 | 관리자가 다른 사용자의 권한을 수정한다. | 관리자 | `PENDING`, `STAFF`, `ADMIN` 중 하나로 변경 |
| REQ-USER-006 | 로그인된 사용자가 자신의 정보를 조회한다. | 필요 | 비밀번호 관련 필드 제외 |
| REQ-USER-007 | 로그인된 사용자가 자신의 부서와 전화번호를 수정한다. | 필요 | 전달된 필드만 수정, 전화번호 중복 금지 |
| REQ-USER-008 | 로그인된 사용자가 자신의 비밀번호를 변경한다. | 필요 | 현재 비밀번호 확인 후 새 비밀번호 해싱 |
| REQ-USER-009 | 로그인된 사용자가 회원 탈퇴한다. | 필요 | 계정을 비활성화하고 토큰 무효화 |
| NFR-USER-001 | 로그인 성공 시 Access Token과 Refresh Token을 발급한다. | 로그인 성공 사용자 | Access Token은 JSON, Refresh Token은 HttpOnly Cookie |

### 2.1 사용자 유형

| 역할 | 설명 | 허용 기능 |
| --- | --- | --- |
| `PENDING` | 가입 후 관리자 승인 대기 사용자 | 로그인 정책은 구현 전 확정 필요, 업무 API 접근 제한 |
| `STAFF` | 승인된 일반 사내 구성원 | 자신의 정보 조회·수정·비밀번호 변경·탈퇴 |
| `ADMIN` | 관리자 | 일반 사용자 기능과 사용자 목록 조회·권한 수정 |

## 3. 요구사항–API 매핑

| 요구사항 ID | API | Method | Endpoint |
| --- | --- | --- | --- |
| REQ-USER-001 | 회원가입 | `POST` | `/api/v1/users/signup` |
| REQ-USER-002, NFR-USER-001 | 로그인 | `POST` | `/api/v1/users/login` |
| NFR-USER-001 | Access Token 재발급 | `POST` | `/api/v1/users/refresh` |
| REQ-USER-003 | 로그아웃 | `POST` | `/api/v1/users/logout` |
| REQ-USER-004 | 전체 사용자 목록 조회 | `GET` | `/api/v1/admin/users` |
| REQ-USER-005 | 사용자 권한 수정 | `PATCH` | `/api/v1/admin/users/role` |
| REQ-USER-006 | 내 정보 조회 | `GET` | `/api/v1/users/me` |
| REQ-USER-007 | 내 정보 수정 | `PATCH` | `/api/v1/users/me` |
| REQ-USER-008 | 내 비밀번호 변경 | `PATCH` | `/api/v1/users/me/password` |
| REQ-USER-009 | 회원 탈퇴 | `DELETE` | `/api/v1/users/me` |

## 4. 공통 API 규칙

### 4.1 요청과 응답

- 일반 Request Body와 Response Body는 `application/json`을 사용한다.
- 로그인은 OAuth2 도구 및 기존 프런트엔드와 호환되도록 `application/x-www-form-urlencoded`를 사용한다.
- 로그인 요청의 `username` 필드에는 이메일을 입력한다.
- 인증이 필요한 요청은 `Authorization: Bearer <access_token>` 헤더를 사용한다.
- Refresh Token은 JavaScript에서 읽을 수 없는 `HttpOnly` Cookie로 전달한다.
- 날짜·시간은 ISO 8601 문자열로 표현한다.
- `PATCH` 요청은 전달된 필드만 변경한다.

### 4.2 성공 상태 코드

| 상황 | 상태 코드 |
| --- | --- |
| 생성 성공 | `201 Created` |
| 조회·로그인·수정·토큰 갱신 성공 | `200 OK` |
| 응답 본문이 필요 없는 로그아웃·탈퇴 성공 | `204 No Content` |

### 4.3 공통 오류 형식

```json
{
  "detail": "오류 메시지"
}
```

Pydantic 입력 검증 실패는 FastAPI의 `422 Unprocessable Entity` 형식을 사용한다.

### 4.4 공통 상태 코드

| 상태 코드 | 의미 | 대표 상황 |
| --- | --- | --- |
| `400 Bad Request` | 비즈니스 규칙 위반 | 현재 비밀번호 불일치, 빈 수정 요청 |
| `401 Unauthorized` | 인증 실패 | 잘못된 로그인 정보, 없거나 만료된 토큰 |
| `403 Forbidden` | 권한 부족 | 일반 사용자의 관리자 API 호출 |
| `404 Not Found` | 대상 없음 | 관리자가 수정할 사용자가 존재하지 않음 |
| `409 Conflict` | 고유값 충돌 | 이메일 또는 전화번호 중복 |
| `422 Unprocessable Entity` | 입력 형식·범위 오류 | 이메일 형식, 비밀번호 규칙, Enum 오류 |

## 5. 전체 Endpoint 목록

| 번호 | 기능 | Method | Endpoint | 인증 | 권한 | 성공 코드 |
| ---: | --- | --- | --- | --- | --- | ---: |
| 1 | 회원가입 | `POST` | `/api/v1/users/signup` | 불필요 | 모두 | `201` |
| 2 | 로그인 | `POST` | `/api/v1/users/login` | 불필요 | 모두 | `200` |
| 3 | 토큰 재발급 | `POST` | `/api/v1/users/refresh` | Refresh Cookie | 가입 사용자 | `200` |
| 4 | 로그아웃 | `POST` | `/api/v1/users/logout` | 필요 | 로그인 사용자 | `204` |
| 5 | 내 정보 조회 | `GET` | `/api/v1/users/me` | 필요 | 로그인 사용자 | `200` |
| 6 | 내 정보 수정 | `PATCH` | `/api/v1/users/me` | 필요 | 로그인 사용자 | `200` |
| 7 | 내 비밀번호 변경 | `PATCH` | `/api/v1/users/me/password` | 필요 | 로그인 사용자 | `200` |
| 8 | 회원 탈퇴 | `DELETE` | `/api/v1/users/me` | 필요 | 로그인 사용자 | `204` |
| 9 | 사용자 목록 조회 | `GET` | `/api/v1/admin/users` | 필요 | `ADMIN` | `200` |
| 10 | 사용자 권한 수정 | `PATCH` | `/api/v1/admin/users/role` | 필요 | `ADMIN` | `200` |

## 6. API별 상세 명세

### 6.1 회원가입

| 항목 | 내용 |
| --- | --- |
| 요구사항 | REQ-USER-001 |
| Method·Endpoint | `POST /api/v1/users/signup` |
| 인증·권한 | 불필요 |
| Request Body | `email`, `password`, `name`, `department`, `gender`, `phone_number` 모두 필수 |
| Response Body | 생성된 공개 사용자 정보 |
| 성공 | `201 Created` |
| 예외 | `409` 이메일·전화번호 중복, `422` 입력 검증 실패 |
| 비즈니스 규칙 | 비밀번호를 Argon2로 해싱하고 역할은 `PENDING`, 상태는 활성으로 생성 |

요청 예시:

```json
{
  "email": "sejun@example.com",
  "password": "Password1!",
  "name": "정세준",
  "department": "DEV",
  "gender": "M",
  "phone_number": "01012345678"
}
```

응답 예시:

```json
{
  "id": 1,
  "email": "sejun@example.com",
  "name": "정세준",
  "department": "DEV",
  "gender": "M",
  "phone_number": "01012345678",
  "role": "PENDING",
  "is_active": true,
  "created_at": "2026-07-16T10:00:00"
}
```

### 6.2 로그인

| 항목 | 내용 |
| --- | --- |
| 요구사항 | REQ-USER-002, NFR-USER-001 |
| Method·Endpoint | `POST /api/v1/users/login` |
| Content-Type | `application/x-www-form-urlencoded` |
| 인증·권한 | 불필요 |
| Form Body | `username`: 이메일, `password`: 비밀번호 |
| Response Body | Access Token과 토큰 타입 |
| Cookie | Refresh Token을 `HttpOnly`, `Secure`, `SameSite` 정책과 함께 설정 |
| 성공 | `200 OK` |
| 예외 | `401` 이메일·비밀번호 불일치 또는 비활성 계정, `422` 필수값 누락 |

요청 예시:

```text
username=sejun%40example.com&password=Password1%21
```

응답 예시:

```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

보안을 위해 계정 존재 여부를 구분하지 않고 로그인 실패 메시지는 동일하게 반환한다.

```json
{
  "detail": "이메일 또는 비밀번호가 올바르지 않습니다."
}
```

### 6.3 Access Token 재발급

| 항목 | 내용 |
| --- | --- |
| 요구사항 | NFR-USER-001 |
| Method·Endpoint | `POST /api/v1/users/refresh` |
| 인증 | HttpOnly Cookie의 유효한 Refresh Token 필요 |
| Request Body | 없음 |
| Response Body | 새 Access Token과 토큰 타입 |
| 성공 | `200 OK` |
| 예외 | `401` Cookie 누락·만료·위조 또는 비활성 계정 |

응답 예시:

```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

### 6.4 로그아웃

| 항목 | 내용 |
| --- | --- |
| 요구사항 | REQ-USER-003 |
| Method·Endpoint | `POST /api/v1/users/logout` |
| 인증·권한 | Bearer Token을 가진 로그인 사용자 |
| Request Body | 없음 |
| 성공 | `204 No Content` |
| 예외 | `401` 인증 실패 |
| 비즈니스 규칙 | Refresh Cookie 삭제 및 서버 측 Refresh Token 무효화 정책 적용 |

성공 시 Response Body는 없다.

### 6.5 내 정보 조회

| 항목 | 내용 |
| --- | --- |
| 요구사항 | REQ-USER-006 |
| Method·Endpoint | `GET /api/v1/users/me` |
| 인증·권한 | 로그인 사용자 |
| Request Body | 없음 |
| Response Body | 현재 인증 사용자의 공개 정보 |
| 성공 | `200 OK` |
| 예외 | `401` 인증 실패 |

응답 예시:

```json
{
  "id": 1,
  "email": "sejun@example.com",
  "name": "정세준",
  "department": "DEV",
  "gender": "M",
  "phone_number": "01012345678",
  "role": "STAFF",
  "is_active": true,
  "created_at": "2026-07-16T10:00:00"
}
```

### 6.6 내 정보 수정

| 항목 | 내용 |
| --- | --- |
| 요구사항 | REQ-USER-007 |
| Method·Endpoint | `PATCH /api/v1/users/me` |
| 인증·권한 | 로그인 사용자 |
| Request Body | `department`, `phone_number` 선택 입력 |
| Response Body | 수정된 공개 사용자 정보 |
| 성공 | `200 OK` |
| 예외 | `400` 수정 필드 없음, `409` 전화번호 중복, `422` 형식·Enum 오류 |
| 비즈니스 규칙 | 전달된 필드만 수정하며 이메일·이름·성별·권한은 이 API에서 수정 불가 |

요청 예시:

```json
{
  "department": "RESEARCH",
  "phone_number": "01098765432"
}
```

### 6.7 내 비밀번호 변경

| 항목 | 내용 |
| --- | --- |
| 요구사항 | REQ-USER-008 |
| Method·Endpoint | `PATCH /api/v1/users/me/password` |
| 인증·권한 | 로그인 사용자 |
| Request Body | `current_password`, `new_password` 필수 |
| Response Body | 처리 결과 메시지 |
| 성공 | `200 OK` |
| 예외 | `400` 현재 비밀번호 불일치·기존과 동일, `422` 새 비밀번호 규칙 위반 |
| 비즈니스 규칙 | 현재 비밀번호 확인 후 새 비밀번호를 Argon2로 해싱하여 저장 |

요청 예시:

```json
{
  "current_password": "Password1!",
  "new_password": "NewPassword2@"
}
```

응답 예시:

```json
{
  "message": "비밀번호가 변경되었습니다."
}
```

### 6.8 회원 탈퇴

| 항목 | 내용 |
| --- | --- |
| 요구사항 | REQ-USER-009 |
| Method·Endpoint | `DELETE /api/v1/users/me` |
| 인증·권한 | 로그인 사용자 |
| Request Body | 없음 |
| 성공 | `204 No Content` |
| 예외 | `401` 인증 실패 |
| 비즈니스 규칙 | 관계 데이터 보존을 위해 우선 `is_active=false`로 비활성화하고 토큰 무효화 |

성공 시 Response Body는 없다.

### 6.9 전체 사용자 목록 조회

| 항목 | 내용 |
| --- | --- |
| 요구사항 | REQ-USER-004 |
| Method·Endpoint | `GET /api/v1/admin/users` |
| 인증·권한 | `ADMIN` |
| Query Parameter | `query`: 이름·이메일 부분 검색, `department`: 부서 필터 |
| Response Body | 공개 사용자 정보 배열 |
| 성공 | `200 OK` |
| 예외 | `401` 인증 실패, `403` 관리자 권한 없음, `422` 잘못된 부서 값 |

요청 예시:

```text
GET /api/v1/admin/users?query=sejun&department=DEV
```

응답 예시:

```json
[
  {
    "id": 1,
    "email": "sejun@example.com",
    "name": "정세준",
    "department": "DEV",
    "gender": "M",
    "phone_number": "01012345678",
    "role": "STAFF",
    "is_active": true,
    "created_at": "2026-07-16T10:00:00"
  }
]
```

검색 결과가 없으면 오류가 아닌 빈 배열 `[]`을 반환한다. 데이터가 많아질 경우 `page`와 `size` 기반 페이지네이션을 추가할 수 있으나 현재 요구사항에는 포함하지 않는다.

### 6.10 사용자 권한 수정

| 항목 | 내용 |
| --- | --- |
| 요구사항 | REQ-USER-005 |
| Method·Endpoint | `PATCH /api/v1/admin/users/role` |
| 인증·권한 | `ADMIN` |
| Request Body | `user_id`, `new_role` 필수 |
| Response Body | 수정된 공개 사용자 정보 |
| 성공 | `200 OK` |
| 예외 | `400` 자기 자신의 권한 변경, `401` 인증 실패, `403` 권한 부족, `404` 사용자 없음, `422` Role 오류 |
| 비즈니스 규칙 | 대상 역할을 `PENDING`, `STAFF`, `ADMIN` 중 하나로 변경 |

요청 예시:

```json
{
  "user_id": 2,
  "new_role": "STAFF"
}
```

응답 예시:

```json
{
  "id": 2,
  "email": "gaeun@example.com",
  "name": "유가은",
  "department": "MEDICAL",
  "gender": "F",
  "phone_number": "01022223333",
  "role": "STAFF",
  "is_active": true,
  "created_at": "2026-07-16T10:10:00"
}
```

## 7. Pydantic Schema 설계

### 7.1 Schema 목록

| Schema | 용도 | 주요 필드 |
| --- | --- | --- |
| `UserSignupRequest` | 회원가입 요청 | `email`, `password`, `name`, `department`, `gender`, `phone_number` |
| `UserResponse` | 사용자 공개 응답 | `id`, `email`, `name`, `department`, `gender`, `phone_number`, `role`, `is_active`, `created_at` |
| `TokenResponse` | 로그인·갱신 응답 | `access_token`, `token_type` |
| `UserUpdateRequest` | 내 정보 수정 | `department`, `phone_number` |
| `PasswordUpdateRequest` | 비밀번호 변경 | `current_password`, `new_password` |
| `UserListQuery` | 관리자 목록 검색 | `query`, `department` |
| `UserRoleUpdateRequest` | 관리자 권한 변경 | `user_id`, `new_role` |
| `MessageResponse` | 단순 메시지 응답 | `message` |

### 7.2 필드 검증 규칙

| 필드 | Python 타입 | 필수 여부 | 검증 규칙 |
| --- | --- | --- | --- |
| `email` | `EmailStr` | 회원가입 시 필수 | 앞뒤 공백 제거, 소문자 정규화, DB 최대 255자, 중복 불가 |
| `password` | `str` | 필수 | 8~20자, 영문 대문자·소문자·숫자·특수문자 각각 1개 이상 |
| `name` | `str` | 필수 | 앞뒤 공백 제거, 2~20자 |
| `phone_number` | `str` | 가입 시 필수, 수정 시 선택 | 숫자만 저장, `01`로 시작하는 10~11자리, 중복 불가 |
| `gender` | `Gender` | 필수 | `M`, `F` 중 하나 |
| `department` | `Department` | 가입 시 필수, 수정 시 선택 | `MEDICAL`, `DEV`, `RESEARCH` 중 하나 |
| `role` | `Role` | 권한 수정 시 필수 | `PENDING`, `STAFF`, `ADMIN` 중 하나 |
| `user_id` | `int` | 필수 | 1 이상 |
| `query` | `str | None` | 선택 | 앞뒤 공백 제거, 이름·이메일 부분 검색 |

`UserUpdateRequest`는 모든 필드가 선택이지만 두 필드 모두 누락된 경우 `model_validator`로 거부한다. 비밀번호 규칙은 재사용 가능한 `AfterValidator` 또는 공통 검증 함수로 한 곳에서 관리한다.

## 8. User 모델 매핑

| API 필드 | User 모델 컬럼 | 변환 또는 주의사항 |
| --- | --- | --- |
| `id` | `id: Integer` | DB 자동 증가, Request에서 받지 않음 |
| `email` | `email: String(255)` | 소문자 정규화 후 저장, UNIQUE |
| `password` | 직접 매핑 금지 | 해싱 후 `hashed_password`에 저장 |
| `hashed_password` | `hashed_password: String(255)` | API Response에서 절대 노출 금지 |
| `name` | `name: String(20)` | 최대 20자 |
| `phone_number` | `phone_number: String(20)` | 숫자만 정규화 후 저장, UNIQUE |
| `gender` | `gender: Enum(Gender)` | `M`, `F` |
| `department` | `department: Enum(Department)` | `MEDICAL`, `DEV`, `RESEARCH` |
| `role` | `role: Enum(Role)` | 기본값 `PENDING` |
| `is_active` | `is_active: Boolean` | 기본값 `true`, 탈퇴 시 `false` |
| `created_at` | `TimestampMixin.created_at` | 읽기 전용 |
| `updated_at` | `TimestampMixin.updated_at` | 읽기 전용, 필요할 경우 응답에 추가 가능 |

현재 모델은 요구 필드를 모두 포함하므로 과제 1 기준으로 컬럼 추가는 필요하지 않다. 다만 Refresh Token을 서버에서 관리하려면 별도 토큰 테이블 또는 Redis 등의 저장 정책이 필요하다.

## 9. 인증·권한·보안 정책

- 비밀번호는 Argon2로 단방향 해싱하며 평문을 저장하거나 로그에 남기지 않는다.
- Access Token은 짧은 만료 시간을 가진 JWT로 발급하고 JSON Body로 반환한다.
- Refresh Token은 Access Token보다 긴 만료 시간을 적용하고 `HttpOnly` Cookie로 전달한다.
- 운영 환경에서는 Refresh Cookie에 `Secure=true`를 적용한다.
- Cookie의 `SameSite` 값과 CSRF 방어 방식은 배포 구조에 맞춰 결정한다.
- 인증 실패 응답으로 이메일 가입 여부를 노출하지 않는다.
- `get_current_user` 의존성에서 토큰, 사용자 존재 여부, `is_active`를 확인한다.
- `get_current_admin` 의존성에서 현재 사용자의 `role == ADMIN`을 확인한다.
- 일반 응답과 관리자 응답 모두 `hashed_password`를 제외한다.
- 이메일과 전화번호의 중복 검사는 애플리케이션과 DB UNIQUE 제약 조건 양쪽에서 처리한다.
- 마지막 관리자 한 명의 권한을 낮추는 상황은 서비스 운영 안전을 위해 차단하는 방안을 과제 2에서 검토한다.

## 10. 예외 응답 정책

| 상황 | 상태 코드 | 예시 메시지 |
| --- | ---: | --- |
| 이메일 중복 | `409` | `이미 사용 중인 이메일입니다.` |
| 전화번호 중복 | `409` | `이미 사용 중인 전화번호입니다.` |
| 로그인 실패 | `401` | `이메일 또는 비밀번호가 올바르지 않습니다.` |
| Access/Refresh Token 오류 | `401` | `인증 정보가 유효하지 않습니다.` |
| 비활성 계정 | `401` | `사용할 수 없는 계정입니다.` |
| 관리자 권한 없음 | `403` | `관리자 권한이 필요합니다.` |
| 대상 사용자 없음 | `404` | `사용자를 찾을 수 없습니다.` |
| 현재 비밀번호 불일치 | `400` | `현재 비밀번호가 올바르지 않습니다.` |
| 수정할 필드 없음 | `400` | `수정할 항목을 하나 이상 입력해주세요.` |
| 자기 자신의 권한 변경 | `400` | `자신의 권한은 변경할 수 없습니다.` |
| Schema 검증 실패 | `422` | FastAPI 기본 검증 오류 배열 |

DB UNIQUE 제약 조건에서 경쟁 상태로 `IntegrityError`가 발생하면 트랜잭션을 rollback하고 `409 Conflict`로 변환한다. 예상하지 못한 내부 오류나 DB 접속 정보는 클라이언트에 노출하지 않는다.

## 11. 계층별 구현 흐름

```text
Client
  → API Router: 요청 수신, 인증 의존성 주입, 상태 코드와 응답 모델 선언
  → Pydantic Schema: 타입·형식·길이·Enum 검증
  → Service: 중복·권한·비밀번호 등 비즈니스 규칙 판단
  → Repository: SQLAlchemy 조회·생성·수정
  → SQLAlchemy User Model
  → MySQL Database
```

| 계층 | 예상 파일 | 책임 |
| --- | --- | --- |
| Router | `app/apis/users.py`, `app/apis/admin_users.py` | HTTP 요청·응답 및 인증 의존성 연결 |
| Schema | `app/schemas/user.py` | 요청·응답 모델과 값 검증 |
| Service | `app/services/user_service.py`, `auth_service.py` | 비즈니스 규칙, 해싱, 토큰, 트랜잭션 경계 |
| Repository | `app/repositories/user_repository.py` | 사용자 조회·저장·수정 쿼리 |
| Model | `app/models/user.py` | DB 테이블 매핑 |
| Core | `app/core/security.py`, `app/core/dependencies.py` | JWT·Argon2·현재 사용자/관리자 의존성 |

Repository는 HTTP 상태 코드를 알지 않으며 조회 결과 또는 `None`을 반환한다. Service가 예외를 판단하고, 쓰기 작업은 성공 시 `commit`, 실패 시 `rollback`한다.

## 12. 팀원별 API 분담안

공통 Schema, 인증 의존성, Repository 인터페이스는 작업 시작 전에 합의하고 통합 브랜치에 먼저 반영한다. 각 팀원은 자신의 API 코드와 해당 테스트를 함께 작성한다.

| 팀원 | 담당 API | Method·Endpoint | 공통 파일 수정 가능성 | 필수 테스트 |
| --- | --- | --- | --- | --- |
| 정세준 | 회원가입, 로그인, 토큰 재발급 | `POST /users/signup`, `POST /users/login`, `POST /users/refresh` | 인증·보안, User Schema·Repository | 가입 성공·중복, 로그인 성공·실패, Refresh 성공·실패 |
| 유가은 | 로그아웃, 내 정보 조회 | `POST /users/logout`, `GET /users/me` | 인증 의존성, 응답 Schema | 인증 유무, 공개 필드, Cookie 삭제 |
| 임경수 | 내 정보 수정, 비밀번호 변경 | `PATCH /users/me`, `PATCH /users/me/password` | User Service·Schema | 부분 수정, 중복 전화번호, 현재 비밀번호·새 비밀번호 검증 |
| 권민재 | 회원 탈퇴, 관리자 목록·권한 수정 | `DELETE /users/me`, `GET /admin/users`, `PATCH /admin/users/role` | 관리자 의존성·Repository | 비활성화, 검색·필터, 403·404, 권한 변경 |

통합 시 충돌 가능성이 높은 파일은 담당자를 지정한다.

| 공통 파일 | 1차 담당 | 협업 규칙 |
| --- | --- | --- |
| `app/schemas/user.py` | 정세준 | 필요한 Schema를 먼저 선언하고 변경 사항 공유 |
| `app/repositories/user_repository.py` | 임경수 | 공통 조회 함수 시그니처를 먼저 합의 |
| `app/core/security.py` | 정세준 | 토큰·해싱 함수 직접 중복 구현 금지 |
| `app/core/dependencies.py` | 유가은 | 현재 사용자·관리자 의존성 공통 사용 |
| `app/main.py` | 통합 담당자 | 개인 브랜치에서 반복 수정하지 않고 최종 통합 시 Router 등록 |

## 13. 구현 및 테스트 체크리스트

- [ ] 10개 Endpoint가 Swagger UI에 표시된다.
- [ ] 회원가입 시 이메일·전화번호 중복이 차단된다.
- [ ] 비밀번호가 Argon2 해시로만 저장된다.
- [ ] 로그인 성공 시 Access Token과 HttpOnly Refresh Cookie가 발급된다.
- [ ] 만료·위조 토큰은 `401`을 반환한다.
- [ ] 일반 사용자는 관리자 API에서 `403`을 받는다.
- [ ] 사용자 응답에서 비밀번호 관련 필드가 제외된다.
- [ ] 내 정보 수정은 부서와 전화번호만 변경한다.
- [ ] 비밀번호 변경 전 현재 비밀번호를 확인한다.
- [ ] 탈퇴 후 사용자가 더 이상 인증되지 않는다.
- [ ] 관리자 검색·부서 필터와 권한 변경이 동작한다.
- [ ] 각 정상·예외 응답의 상태 코드가 명세와 일치한다.
- [ ] 각 팀원이 최소 1개 API와 테스트를 구현한다.
- [ ] 개인 PR은 통합 브랜치에서 리뷰 후 병합한다.
- [ ] 통합 결과를 `main` 또는 `develop` 대상으로 최종 PR한다.

## 14. 미확정 사항

다음 항목은 저장소의 기존 코드와 화면만으로 완전히 확정할 수 없어 구현 시작 전에 팀 합의가 필요하다.

1. **Enum 표현 불일치**: SQLAlchemy 모델은 `M/F`, `MEDICAL/DEV/RESEARCH`, `PENDING/STAFF/ADMIN`을 사용하지만 기존 프런트엔드는 `male/female`, `medical team/developer/researcher`, 소문자 역할 값을 전송·표시한다. API와 프런트 중 어느 쪽에서 변환할지 결정해야 한다. 이 문서는 DB Enum 값을 API 표준으로 제안한다.
2. **승인 대기 사용자 로그인**: `PENDING` 사용자의 로그인 자체를 막을지, 로그인은 허용하고 업무 기능만 제한할지 결정해야 한다.
3. **Refresh Token 저장 방식**: DB 테이블, Redis, 토큰 버전 방식 중 하나를 선택해야 로그아웃 시 확실한 서버 측 무효화가 가능하다.
4. **회원 탈퇴 방식**: 화면 문구는 영구 삭제를 안내하지만 현재 User 모델에는 `is_active`가 있다. 관계 데이터 보존을 위해 비활성화를 권장하며, 실제 영구 삭제 여부를 확정해야 한다.
5. **비밀번호 최대 길이**: 화면에는 최소 규칙만 보인다. 이 문서는 학습 과제의 기존 기준을 따라 8~20자로 제안했으며 최종 요구사항 확인이 필요하다.
6. **토큰 만료 시간과 Cookie 옵션**: Access/Refresh 만료 시간, `SameSite`, 개발 환경의 `Secure` 적용 방식을 환경 설정으로 확정해야 한다.
7. **관리자 목록 페이지네이션**: 현재 화면은 검색과 부서 필터만 사용한다. 운영 데이터 규모를 고려해 페이지네이션 추가 여부를 결정해야 한다.
