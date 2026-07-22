# 6일차 폐렴 예측 API 설계

## 1. 목적

진료기록에 저장된 흉부 X-ray 이미지를 AI 모델로 분석하고, 폐렴 예측 결과를 저장·조회하기 위한 API를 정의한다.

## 2. 공통 정책

- Base URL: `/api/v1`
- 인증: `Authorization: Bearer <access_token>`
- 예측 실행: 의료진(`MEDICAL STAFF`) 또는 관리자(`ADMIN`)
- 결과 조회: 승인된 직원(`STAFF`) 또는 관리자(`ADMIN`)
- 모델: `SimpleCNN-v1`
- 클래스: `0=NORMAL`, `1=PNEUMONIA`
- 신뢰도: 화면과 DB 형식에 맞춰 `0.00~100.00` 백분율로 반환한다.
- 하나의 진료기록에 예측 이력을 여러 건 저장할 수 있다.
- 여러 X-ray가 있다면 ID가 가장 큰 최신 이미지를 사용한다.

## 3. API 목록

| 요구사항 | 기능 | Method | Endpoint | 성공 |
| --- | --- | --- | --- | --- |
| REQ-PRED-001 | AI 폐렴 예측 실행 | `POST` | `/api/v1/medical-records/{record_id}/predict` | `201` |
| REQ-PRED-002 | 예측 결과 목록 조회 | `GET` | `/api/v1/medical-records/{record_id}/analyses` | `200` |

## 4. AI 폐렴 예측 실행

### 요청

```http
POST /api/v1/medical-records/10/predict
Authorization: Bearer <access_token>
```

Request Body는 사용하지 않는다. `record_id`로 진료기록과 저장된 X-ray를 조회한다.

### 응답

```json
{
  "id": 1,
  "record_id": 10,
  "is_pneumonia": true,
  "confidence": 91.25,
  "heatmap_url": "",
  "ai_model": "SimpleCNN-v1",
  "created_at": "2026-07-22T15:00:00",
  "updated_at": null
}
```

### 처리 흐름

1. 사용자 인증과 의료진 권한을 확인한다.
2. 진료기록과 최신 X-ray를 조회한다.
3. 저장된 이미지 경로가 `media/` 내부인지 검증한다.
4. worker의 메모리 상주 모델로 예측한다.
5. 예측 확률을 백분율로 변환해 `ai_analysis_results`에 저장한다.
6. 저장된 결과를 반환한다.

## 5. 예측 결과 목록 조회

### 요청

```http
GET /api/v1/medical-records/10/analyses
Authorization: Bearer <access_token>
```

### 응답

최신 결과부터 배열로 반환한다. 예측 이력이 없으면 `[]`를 반환한다.

```json
[
  {
    "id": 1,
    "record_id": 10,
    "is_pneumonia": true,
    "confidence": 91.25,
    "heatmap_url": "",
    "ai_model": "SimpleCNN-v1",
    "created_at": "2026-07-22T15:00:00",
    "updated_at": null
  }
]
```

## 6. 예외 처리

| 상태 코드 | 조건 |
| ---: | --- |
| `401 Unauthorized` | 토큰이 없거나 유효하지 않음 |
| `403 Forbidden` | 승인 또는 의료진 권한이 없음 |
| `404 Not Found` | 진료기록, X-ray 정보 또는 실제 이미지 파일이 없음 |
| `422 Unprocessable Entity` | 저장된 파일이 올바른 이미지가 아님 |
| `500 Internal Server Error` | 저장된 이미지 경로가 `media/` 외부를 가리킴 |

오류 응답은 FastAPI 공통 형식인 `{"detail": "메시지"}`를 사용한다.

## 7. 구현 파일

| 계층 | 파일 |
| --- | --- |
| Router | `app/apis/ai_predictions.py` |
| Schema | `app/schemas/ai_analysis.py` |
| Service | `app/services/ai_analysis_service.py` |
| Repository | `app/repositories/ai_analysis_repository.py` |
| AI Worker | `worker/model.py` |

## 8. 현재 제한사항

- 제공된 SimpleCNN은 Grad-CAM heatmap을 생성하지 않으므로 `heatmap_url`은 빈 문자열로 저장한다.
- 클래스 순서와 전처리는 팀이 확인한 모델 설정인 `NORMAL=0`, `PNEUMONIA=1`, 흑백 `128x128`을 사용한다.
- 예측 결과는 의료진의 진단을 보조하며 최종 진단을 대체하지 않는다.
