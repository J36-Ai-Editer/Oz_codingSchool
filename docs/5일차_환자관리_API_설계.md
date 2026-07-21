# 5일차 환자 관리 API 설계

## 1. 문서 목적

이 문서는 AI 헬스케어 웹 서비스의 환자 관리와 진료기록 API를 구현하기 전에 요구사항, HTTP 인터페이스, 데이터 검증, 인증·권한, 파일 저장, 예외 처리 기준을 합의하기 위한 API 명세서다.

설계 근거는 다음과 같다.

- 환자 관리 요구사항 `REQ-PTNT-001`부터 `REQ-PTNT-005`, 성능 요구사항 `NFR-PTNT-001`
- 진료기록 요구사항 `REQ-MDR-001`부터 `REQ-MDR-003`, 성능 요구사항 `NFR-MDR-001`
- `app/models/patient.py`, `app/models/medical_record.py`, `app/models/xray_image.py`의 SQLAlchemy 모델
- `app/models/enums.py`의 성별·권한 열거형과 4일차 User API의 인증·권한 정책

모든 Endpoint의 공통 Prefix는 `/api/v1`이다. 날짜·시간은 ISO 8601 문자열로 표현하고, `PATCH` 요청은 전달된 필드만 변경한다. 4일차에서 정한 JWT 인증 정책(`Authorization: Bearer <access_token>`)을 그대로 사용한다.

## 2. 요구사항 요약

| ID | 사용자 요구사항 | 인증·권한 | 핵심 규칙 |
| --- | --- | --- | --- |
| REQ-PTNT-001 | 의료진이 환자 정보를 등록한다. | 의료진 | 이름·나이·성별·연락처 필수 |
| REQ-PTNT-002 | 승인된 직원이 환자 목록을 조회한다. | 승인 직원 | 이름 검색, 성별·나이 범위 필터 |
| REQ-PTNT-003 | 승인된 직원이 환자 상세를 조회한다. | 승인 직원 | 이름·성별·연락처·나이 확인 |
| REQ-PTNT-004 | 의료진이 환자 정보를 수정한다. | 의료진 | 이름·연락처만 부분 수정 |
| REQ-PTNT-005 | 의료진이 환자를 삭제한다. | 의료진 | 환자·진료기록·X-Ray를 영구 삭제(하드 삭제) |
| REQ-MDR-001 | 의료진이 X-Ray를 포함한 진료기록을 등록한다. | 의료진 | 환자·차트번호·증상·이미지 필수, 이미지는 로컬 저장 |
| REQ-MDR-002 | 승인된 직원이 환자별 진료기록 목록을 조회한다. | 승인 직원 | 증상 100자 초과 시 축약 표시 |
| REQ-MDR-003 | 승인된 직원이 진료기록 상세를 조회한다. | 승인 직원 | 차트번호·증상·X-Ray·생성일시 확인 |
| NFR-PTNT-001, NFR-MDR-001 | 모든 API를 3초 이내에 응답한다. | 해당 없음 | 검색·조회 컬럼 인덱싱으로 응답 시간 확보 |

### 2.1 접근 권한 정의

4일차 `REQ-USER-005`가 정의한 역할 체계(`PENDING`, `STAFF`, `ADMIN`)를 그대로 따른다. 환자·진료기록 요구사항의 "의료인 역할"과 "로그인된 개발진·의료진·연구진"을 다음 두 단계 권한으로 매핑한다.

| 권한 단계 | 의존성(제안) | 판정 기준 | 적용 대상 |
| --- | --- | --- | --- |
| 승인 직원(읽기) | `CurrentApprovedUser` | `role ∈ {STAFF, ADMIN}` | 목록·상세 조회 |
| 의료진(쓰기) | `CurrentMedicalStaff` | `role == ADMIN` 또는 (`department == MEDICAL` 그리고 `role ∈ {STAFF, ADMIN}`) | 등록·수정·삭제 |

- `PENDING` 사용자는 마이페이지 외 접근이 차단되므로 두 단계 모두에서 `403`을 받는다.
- 쓰기 작업을 "의료진"으로 한정한 근거는 REQ-PTNT-001·004·005·MDR-001의 "사내 의료인 역할" 문구다. 부서 기준으로 쓰기를 제한할지, 승인된 `STAFF` 전체에 허용할지는 15장 미확정 사항에서 팀 확정이 필요하다.

## 3. 요구사항–API 매핑

| 요구사항 ID | API | Method | Endpoint |
| --- | --- | --- | --- |
| REQ-PTNT-001 | 환자 등록 | `POST` | `/api/v1/patients` |
| REQ-PTNT-002 | 환자 목록 조회 | `GET` | `/api/v1/patients` |
| REQ-PTNT-003 | 환자 상세 조회 | `GET` | `/api/v1/patients/{patient_id}` |
| REQ-PTNT-004 | 환자 정보 수정 | `PATCH` | `/api/v1/patients/{patient_id}` |
| REQ-PTNT-005 | 환자 삭제 | `DELETE` | `/api/v1/patients/{patient_id}` |
| REQ-MDR-001 | 진료기록 등록 | `POST` | `/api/v1/patients/{patient_id}/medical-records` |
| REQ-MDR-002 | 진료기록 목록 조회 | `GET` | `/api/v1/patients/{patient_id}/medical-records` |
| REQ-MDR-003 | 진료기록 상세 조회 | `GET` | `/api/v1/medical-records/{record_id}` |

환자에 종속된 컬렉션(등록·목록)은 `/patients/{patient_id}/medical-records`로 중첩하고, 개별 진료기록 상세는 전역 식별자를 쓰는 `/medical-records/{record_id}`로 접근한다.

## 4. 공통 API 규칙

### 4.1 요청과 응답

- 일반 Request·Response Body는 `application/json`을 사용한다.
- 진료기록 등록은 이미지 업로드를 포함하므로 `multipart/form-data`를 사용한다.
- 인증이 필요한 요청은 `Authorization: Bearer <access_token>` 헤더를 사용한다.
- `PATCH` 요청은 전달된 필드만 변경하며, 빈 요청은 `400`으로 거부한다.
- 목록 조회 결과가 없으면 오류가 아닌 빈 배열 `[]`을 반환한다.

### 4.2 성공 상태 코드

| 상황 | 상태 코드 |
| --- | --- |
| 환자·진료기록 생성 성공 | `201 Created` |
| 조회·수정 성공 | `200 OK` |
| 응답 본문이 필요 없는 삭제 성공 | `204 No Content` |

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
| `400 Bad Request` | 비즈니스 규칙 위반 | 빈 수정 요청, 잘못된 나이 범위(`min_age > max_age`) |
| `401 Unauthorized` | 인증 실패 | 없거나 만료된 토큰 |
| `403 Forbidden` | 권한 부족 | `PENDING` 사용자 접근, 비의료진의 쓰기 시도 |
| `404 Not Found` | 대상 없음 | 존재하지 않는 환자·진료기록 |
| `409 Conflict` | 고유값 충돌 | 차트번호 중복 |
| `413 Payload Too Large` | 업로드 용량 초과 | X-Ray 이미지 크기 제한 초과 |
| `415 Unsupported Media Type` | 형식 불일치 | 허용하지 않는 이미지 확장자 |
| `422 Unprocessable Entity` | 입력 형식·범위 오류 | 필수값 누락, Enum 오류 |

## 5. 전체 Endpoint 목록

| 번호 | 기능 | Method | Endpoint | 인증 | 권한 | 성공 코드 |
| ---: | --- | --- | --- | --- | --- | ---: |
| 1 | 환자 등록 | `POST` | `/api/v1/patients` | 필요 | 의료진 | `201` |
| 2 | 환자 목록 조회 | `GET` | `/api/v1/patients` | 필요 | 승인 직원 | `200` |
| 3 | 환자 상세 조회 | `GET` | `/api/v1/patients/{patient_id}` | 필요 | 승인 직원 | `200` |
| 4 | 환자 정보 수정 | `PATCH` | `/api/v1/patients/{patient_id}` | 필요 | 의료진 | `200` |
| 5 | 환자 삭제 | `DELETE` | `/api/v1/patients/{patient_id}` | 필요 | 의료진 | `204` |
| 6 | 진료기록 등록 | `POST` | `/api/v1/patients/{patient_id}/medical-records` | 필요 | 의료진 | `201` |
| 7 | 진료기록 목록 조회 | `GET` | `/api/v1/patients/{patient_id}/medical-records` | 필요 | 승인 직원 | `200` |
| 8 | 진료기록 상세 조회 | `GET` | `/api/v1/medical-records/{record_id}` | 필요 | 승인 직원 | `200` |

## 6. API별 상세 명세

### 6.1 환자 등록

| 항목 | 내용 |
| --- | --- |
| 요구사항 | REQ-PTNT-001 |
| Method·Endpoint | `POST /api/v1/patients` |
| 인증·권한 | 의료진 |
| Request Body | `name`, `age`, `gender`, `phone` 모두 필수 |
| Response Body | 생성된 환자 정보 |
| 성공 | `201 Created` |
| 예외 | `401` 인증 실패, `403` 권한 부족, `422` 입력 검증 실패 |

요청 예시:

```json
{
  "name": "김환자",
  "age": 42,
  "gender": "M",
  "phone": "01012345678"
}
```

응답 예시:

```json
{
  "id": 1,
  "name": "김환자",
  "age": 42,
  "gender": "M",
  "phone": "01012345678",
  "created_at": "2026-07-20T10:00:00",
  "updated_at": null
}
```

### 6.2 환자 목록 조회

| 항목 | 내용 |
| --- | --- |
| 요구사항 | REQ-PTNT-002 |
| Method·Endpoint | `GET /api/v1/patients` |
| 인증·권한 | 승인 직원 |
| Query Parameter | `name` 이름 부분 검색, `gender` 성별 필터, `min_age`·`max_age` 나이 범위 필터 |
| Response Body | 환자 정보 배열 |
| 성공 | `200 OK` |
| 예외 | `400` `min_age > max_age`, `401` 인증 실패, `403` 권한 부족, `422` 잘못된 성별·나이 값 |

요청 예시:

```text
GET /api/v1/patients?name=김&gender=M&min_age=30&max_age=50
```

응답 예시:

```json
[
  {
    "id": 1,
    "name": "김환자",
    "age": 42,
    "gender": "M",
    "phone": "01012345678",
    "created_at": "2026-07-20T10:00:00",
    "updated_at": null
  }
]
```

검색·필터 조건은 AND로 결합하고, 조건에 맞는 환자가 없으면 빈 배열을 반환한다.

### 6.3 환자 상세 조회

| 항목 | 내용 |
| --- | --- |
| 요구사항 | REQ-PTNT-003 |
| Method·Endpoint | `GET /api/v1/patients/{patient_id}` |
| 인증·권한 | 승인 직원 |
| Path Parameter | `patient_id` 환자 고유 ID |
| Response Body | 환자 상세(이름·성별·연락처·나이 포함) |
| 성공 | `200 OK` |
| 예외 | `401` 인증 실패, `403` 권한 부족, `404` 환자 없음 |

응답 예시는 6.1의 응답과 동일한 환자 표현을 사용한다.

### 6.4 환자 정보 수정

| 항목 | 내용 |
| --- | --- |
| 요구사항 | REQ-PTNT-004 |
| Method·Endpoint | `PATCH /api/v1/patients/{patient_id}` |
| 인증·권한 | 의료진 |
| Request Body | `name`, `phone` 선택 입력 |
| Response Body | 수정된 환자 정보 |
| 성공 | `200 OK` |
| 예외 | `400` 수정 필드 없음, `401` 인증 실패, `403` 권한 부족, `404` 환자 없음, `422` 형식 오류 |
| 비즈니스 규칙 | 전달된 필드만 수정하며 나이·성별은 이 API에서 수정하지 않는다 |

요청 예시:

```json
{
  "name": "김환자수정",
  "phone": "01098765432"
}
```

### 6.5 환자 삭제

| 항목 | 내용 |
| --- | --- |
| 요구사항 | REQ-PTNT-005 |
| Method·Endpoint | `DELETE /api/v1/patients/{patient_id}` |
| 인증·권한 | 의료진 |
| Path Parameter | `patient_id` 환자 고유 ID |
| Response Body | 없음 |
| 성공 | `204 No Content` |
| 예외 | `401` 인증 실패, `403` 권한 부족, `404` 환자 없음 |
| 비즈니스 규칙 | 환자와 연결된 진료기록·X-Ray 이미지·AI 분석 결과를 함께 영구 삭제하고, 저장된 이미지 파일도 로컬 저장소에서 제거한다 |

이 삭제는 User의 소프트 삭제(4일차 REQ-USER-009)와 달리 하드 삭제다. DB 관계는 `medical_records`·`xray_images`·`ai_analysis_results`에 설정된 `ON DELETE CASCADE`로 함께 제거되며, 물리 파일 삭제는 서비스 계층에서 명시적으로 수행한다.

### 6.6 진료기록 등록

| 항목 | 내용 |
| --- | --- |
| 요구사항 | REQ-MDR-001 |
| Method·Endpoint | `POST /api/v1/patients/{patient_id}/medical-records` |
| Content-Type | `multipart/form-data` |
| 인증·권한 | 의료진 |
| Form Field | `chart_number`, `symptoms` 필수, `xray_image` 파일 1개 이상 필수, `shooting_datetime` 선택 |
| Response Body | 생성된 진료기록 상세 |
| 성공 | `201 Created` |
| 예외 | `401` 인증 실패, `403` 권한 부족, `404` 환자 없음, `409` 차트번호 중복, `413` 용량 초과, `415` 형식 오류, `422` 필수값 누락 |
| 비즈니스 규칙 | 이미지를 로컬 저장소에 저장하고 저장 경로를 `image_url`로 기록한다. `shooting_datetime` 미입력 시 업로드 시각으로 대체한다 |

`patient_id`는 URL 경로로 전달하며, 존재하지 않으면 `404`를 반환한다. 차트번호는 전역 UNIQUE이므로 중복 시 `409`를 반환한다.

응답 예시:

```json
{
  "id": 10,
  "patient_id": 1,
  "chart_number": "CHART-2026-0001",
  "symptoms": "기침과 발열이 3일간 지속됨",
  "xray_images": [
    {
      "id": 100,
      "image_url": "/media/xray/2026/07/20/uuid.png",
      "shooting_datetime": "2026-07-20T09:30:00",
      "created_at": "2026-07-20T10:05:00"
    }
  ],
  "created_at": "2026-07-20T10:05:00",
  "updated_at": null
}
```

### 6.7 진료기록 목록 조회

| 항목 | 내용 |
| --- | --- |
| 요구사항 | REQ-MDR-002 |
| Method·Endpoint | `GET /api/v1/patients/{patient_id}/medical-records` |
| 인증·권한 | 승인 직원 |
| Path Parameter | `patient_id` 환자 고유 ID |
| Response Body | 해당 환자의 진료기록 배열(요약) |
| 성공 | `200 OK` |
| 예외 | `401` 인증 실패, `403` 권한 부족, `404` 환자 없음 |
| 비즈니스 규칙 | `symptoms`가 100자를 초과하면 앞 100자만 남기고 `…`를 붙여 반환한다 |

응답 예시:

```json
[
  {
    "id": 10,
    "chart_number": "CHART-2026-0001",
    "symptoms": "기침과 발열이 3일간 지속됨",
    "created_at": "2026-07-20T10:05:00"
  }
]
```

### 6.8 진료기록 상세 조회

| 항목 | 내용 |
| --- | --- |
| 요구사항 | REQ-MDR-003 |
| Method·Endpoint | `GET /api/v1/medical-records/{record_id}` |
| 인증·권한 | 승인 직원 |
| Path Parameter | `record_id` 진료기록 고유 ID |
| Response Body | 진료기록 상세와 X-Ray 이미지 목록 |
| 성공 | `200 OK` |
| 예외 | `401` 인증 실패, `403` 권한 부족, `404` 진료기록 없음 |

응답 본문은 6.6의 생성 응답과 동일한 구조를 사용하며, `symptoms`는 축약하지 않고 전체를 반환한다.

## 7. Pydantic Schema 설계

### 7.1 Schema 목록

| Schema | 용도 | 주요 필드 |
| --- | --- | --- |
| `PatientCreateRequest` | 환자 등록 요청 | `name`, `age`, `gender`, `phone` |
| `PatientUpdateRequest` | 환자 수정 요청 | `name`, `phone` |
| `PatientListQuery` | 환자 목록 검색 | `name`, `gender`, `min_age`, `max_age` |
| `PatientResponse` | 환자 응답 | `id`, `name`, `age`, `gender`, `phone`, `created_at`, `updated_at` |
| `MedicalRecordCreateRequest` | 진료기록 등록(Form) | `chart_number`, `symptoms`, `xray_image`, `shooting_datetime` |
| `MedicalRecordListItem` | 진료기록 목록 항목 | `id`, `chart_number`, `symptoms`(축약), `created_at` |
| `MedicalRecordResponse` | 진료기록 상세 | `id`, `patient_id`, `chart_number`, `symptoms`, `xray_images`, `created_at`, `updated_at` |
| `XrayImageResponse` | X-Ray 이미지 응답 | `id`, `image_url`, `shooting_datetime`, `created_at` |

### 7.2 필드 검증 규칙

| 필드 | Python 타입 | 필수 여부 | 검증 규칙 |
| --- | --- | --- | --- |
| `name` | `str` | 등록 필수, 수정 선택 | 앞뒤 공백 제거, 1~30자 |
| `age` | `int` | 등록 필수 | 0~150 범위 |
| `gender` | `Gender` | 등록 필수 | `M`, `F` 중 하나 |
| `phone` | `str` | 등록 필수, 수정 선택 | 숫자만 저장, `01`로 시작하는 10~11자리 |
| `min_age` / `max_age` | `int \| None` | 선택 | 0 이상, `min_age ≤ max_age` |
| `chart_number` | `str` | 필수 | 1~50자, 전역 UNIQUE |
| `symptoms` | `str` | 필수 | 1자 이상 |
| `xray_image` | `UploadFile` | 필수 | 허용 확장자(`png`, `jpg`, `jpeg`)와 최대 용량 검증 |
| `shooting_datetime` | `datetime \| None` | 선택 | 미입력 시 업로드 시각 사용 |

`PatientUpdateRequest`는 두 필드 모두 선택이지만 모두 누락된 경우 `model_validator`로 거부한다. 전화번호 정규화 규칙은 User API의 검증 함수를 재사용한다.

## 8. 모델 매핑

| API 필드 | 모델 컬럼 | 변환·주의사항 |
| --- | --- | --- |
| `patient.id` | `Patient.id: BigInteger` | 자동 증가, Request에서 받지 않음 |
| `patient.name` | `Patient.name: String(30)` | 최대 30자 |
| `patient.age` | `Patient.age: SmallInteger` | 0~150 |
| `patient.gender` | `Patient.gender: Enum(Gender)` | 모델은 nullable이나 등록 시 필수로 받는다(15장 확인 필요) |
| `patient.phone` | `Patient.phone: String(11)` | 숫자만 정규화, 최대 11자 |
| `record.chart_number` | `MedicalRecord.chart_number: String(50)` | UNIQUE, 중복 시 409 |
| `record.symptoms` | `MedicalRecord.symptoms: Text` | 목록에서만 100자 축약 |
| `record.patient_id` | `MedicalRecord.patient_id: FK(CASCADE)` | 부모 삭제 시 함께 삭제 |
| `xray.image_url` | `XrayImage.image_url: String(2048)` | 로컬 저장 경로 |
| `xray.uploader_id` | `XrayImage.uploader_id: FK(SET NULL)` | 현재 로그인 사용자 ID로 기록 |
| `xray.shooting_datetime` | `XrayImage.shooting_datetime: DateTime` | 미입력 시 업로드 시각 |
| `created_at` / `updated_at` | `TimestampMixin` | 읽기 전용. `XrayImage`는 `updated_at`이 없다 |

현재 모델은 요구 필드를 모두 포함하므로 컬럼 추가는 필요하지 않다.

## 9. 인증·권한·보안 정책

- 모든 Endpoint는 4일차의 `get_current_user` 의존성으로 토큰·계정 활성 상태를 확인한다.
- 조회 API는 `CurrentApprovedUser`(role ∈ {STAFF, ADMIN})를, 쓰기 API는 `CurrentMedicalStaff`를 의존성으로 사용한다.
- `PENDING` 사용자는 모든 환자·진료기록 API에서 `403`을 받는다.
- 새 의존성은 `app/core/dependencies.py`에 추가하며, 4일차의 현재 사용자 의존성을 재사용한다.

## 10. 파일 저장 정책

- X-Ray 이미지는 서버가 실행되는 환경의 로컬 저장소에 저장한다(`app/main.py`가 마운트한 `media/` 경로 활용).
- 파일명은 원본 이름을 그대로 쓰지 않고 UUID 등으로 재생성하여 충돌과 경로 조작을 방지한다.
- 저장 경로 규칙은 `media/xray/<YYYY>/<MM>/<DD>/<uuid>.<ext>` 형태를 제안한다.
- 허용 확장자와 최대 용량을 서버에서 검증하고, 위반 시 `415` 또는 `413`을 반환한다.
- 환자 삭제 시 DB 레코드 삭제와 함께 물리 파일도 삭제한다. 파일 삭제 실패가 트랜잭션 전체를 되돌리지 않도록 처리 순서와 예외 정책을 정한다.

## 11. 예외 응답 정책

| 상황 | 상태 코드 | 예시 메시지 |
| --- | ---: | --- |
| 권한 부족 | `403` | `접근 권한이 없습니다.` |
| 환자 없음 | `404` | `환자를 찾을 수 없습니다.` |
| 진료기록 없음 | `404` | `진료기록을 찾을 수 없습니다.` |
| 차트번호 중복 | `409` | `이미 사용 중인 차트번호입니다.` |
| 빈 수정 요청 | `400` | `수정할 항목을 하나 이상 입력해주세요.` |
| 잘못된 나이 범위 | `400` | `나이 범위가 올바르지 않습니다.` |
| 이미지 형식 오류 | `415` | `지원하지 않는 이미지 형식입니다.` |
| 이미지 용량 초과 | `413` | `허용된 파일 크기를 초과했습니다.` |
| Schema 검증 실패 | `422` | FastAPI 기본 검증 오류 배열 |

차트번호 UNIQUE 제약에서 경쟁 상태로 `IntegrityError`가 발생하면 트랜잭션을 rollback하고 `409`로 변환한다.

## 12. 계층별 구현 흐름

```text
Client
  → API Router: 요청 수신, 인증 의존성 주입, 상태 코드·응답 모델 선언
  → Pydantic Schema: 타입·형식·길이·Enum 검증
  → Service: 권한·중복·파일 저장 등 비즈니스 규칙 판단
  → Repository: SQLAlchemy 조회·생성·수정·삭제
  → SQLAlchemy Model (Patient, MedicalRecord, XrayImage)
  → MySQL Database + 로컬 파일 저장소
```

| 계층 | 예상 파일 | 책임 |
| --- | --- | --- |
| Router | `app/apis/patients.py`, `app/apis/medical_records.py` | HTTP 요청·응답과 인증 의존성 연결 |
| Schema | `app/schemas/patient.py`, `app/schemas/medical_record.py` | 요청·응답 모델과 값 검증 |
| Service | `app/services/patient_service.py`, `app/services/medical_record_service.py` | 비즈니스 규칙, 파일 저장·삭제, 트랜잭션 경계 |
| Repository | `app/repositories/patient_repository.py`, `app/repositories/medical_record_repository.py` | 조회·저장·삭제 쿼리 |
| Core | `app/core/dependencies.py`, `app/core/storage.py`(제안) | 권한 의존성, 로컬 파일 저장 유틸 |
| Model | 기존 `app/models/*.py` | DB 테이블 매핑(변경 없음) |

Repository는 HTTP 상태 코드를 알지 않고 조회 결과 또는 `None`을 반환한다. Service가 예외를 판단하며, 쓰기는 성공 시 `commit`, 실패 시 `rollback`한다. 라우터는 `app/main.py`에서 통합 시 등록한다.

## 13. 성능(NFR) 대응

- `Patient.name`에 인덱스를 추가해 이름 검색을 빠르게 한다.
- `MedicalRecord.patient_id` 외래키 인덱스로 환자별 목록 조회를 최적화한다.
- 목록 API는 필요 시 `page`, `size` 기반 페이지네이션을 추가할 수 있도록 설계하되, 현재 요구사항에는 포함하지 않는다.
- 이미지 저장·응답은 파일 스트림 처리로 메모리 사용을 제한해 3초 이내 응답 목표를 지킨다.

## 14. 구현 및 테스트 체크리스트

- [ ] 8개 Endpoint가 Swagger UI에 표시된다.
- [ ] 의료진만 환자·진료기록을 등록·수정·삭제할 수 있다.
- [ ] `PENDING` 사용자는 모든 환자 API에서 `403`을 받는다.
- [ ] 이름 검색과 성별·나이 범위 필터가 동작한다.
- [ ] 진료기록 목록에서 100자 초과 증상이 축약된다.
- [ ] 진료기록 등록 시 이미지가 로컬에 저장되고 경로가 응답에 포함된다.
- [ ] 차트번호 중복 시 `409`를 반환한다.
- [ ] 환자 삭제 시 진료기록·X-Ray가 함께 삭제되고 파일도 제거된다.
- [ ] 존재하지 않는 환자·진료기록 접근 시 `404`를 반환한다.
- [ ] 각 정상·예외 응답의 상태 코드가 명세와 일치한다.
- [ ] 문서를 GitHub Flow 절차에 따라 작업 브랜치에서 PR로 병합한다.

## 15. 미확정 사항

구현 시작 전에 팀 합의가 필요한 항목이다.

1. **쓰기 권한 범위**: 환자·진료기록 쓰기를 `department == MEDICAL`로 제한할지, 승인된 `STAFF` 전체에 허용할지 확정해야 한다. 이 문서는 "의료진(MEDICAL 또는 ADMIN)"으로 제안했다.
2. **성별 필수 여부**: `Patient.gender`는 모델상 nullable이지만 REQ-PTNT-001은 필수 입력으로 규정한다. API에서 필수로 받되 모델 제약을 맞출지 결정해야 한다.
3. **X-Ray 이미지 개수**: 진료기록당 이미지를 1개만 받을지 여러 장을 허용할지 확정해야 한다. 모델은 1:N을 지원한다.
4. **촬영 일시 입력**: `shooting_datetime`을 사용자 입력으로 받을지 업로드 시각으로 자동 기록할지 결정해야 한다.
5. **이미지 제약**: 허용 확장자, 최대 용량, 저장 경로 규칙을 환경 설정으로 확정해야 한다.
6. **삭제 시 파일 정리 실패 처리**: DB 삭제와 물리 파일 삭제의 순서, 파일 삭제 실패 시 재시도·로깅 정책을 정해야 한다.
7. **목록 페이지네이션**: 환자·진료기록 목록의 페이지네이션 도입 시점을 데이터 규모에 맞춰 결정해야 한다.
