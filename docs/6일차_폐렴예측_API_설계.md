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

## 8. 테스트 및 성능 검증

### 8.1 자동화 테스트

| 구분 | 검증 내용 | 기대 결과 |
| --- | --- | --- |
| 모델 전처리 | 입력 이미지의 채널·크기 변환 | `[1, 1, 128, 128]` 텐서 |
| 모델 예측 | 클래스, 확률 범위와 합계 | `NORMAL` 또는 `PNEUMONIA`, 확률 합 약 1 |
| 잘못된 이미지 | 이미지가 아닌 데이터 입력 | `InvalidImageError` |
| 모델 재사용 | 여러 예측 사이 모델 객체 비교 | 전역 `MODEL` 객체 재사용 |
| 예측 API | 의료진의 예측 실행 | `201 Created` |
| 결과 조회 API | 승인 사용자의 결과 목록 조회 | `200 OK` |
| 인증·권한 | 미인증 및 `PENDING` 사용자 요청 | 각각 `401`, `403` |
| 대상 없음 | 존재하지 않는 진료기록 예측 | `404 Not Found` |

테스트 코드는 `tests/test_worker_model.py`와
`tests/test_ai_prediction_apis.py`에 작성했다.

### 8.2 추론 성능 측정 방법

- 모델 로딩과 최초 장치 초기화의 영향을 줄이기 위해 3회 워밍업 후 측정한다.
- 동일한 `128x128` 흑백 입력으로 20회 추론한다.
- 평균, p95, 최댓값을 기록한다.
- 과제의 3초 이내 응답 목표를 고려해 p95 추론시간 3초 미만을 합격 기준으로 삼는다.

실행 명령어:

```bash
uv run pytest tests/test_worker_model.py tests/test_ai_prediction_apis.py -v -s
```

### 8.3 검증 결과

2026년 7월 22일 Windows, Python 3.14.4, CPU 실행 환경에서 측정했다.

| 항목 | 결과 |
| --- | --- |
| 자동화 테스트 | `10 passed` |
| 평균 추론시간 | `0.0022초` |
| p95 추론시간 | `0.0034초` |
| 최대 추론시간 | `0.0041초` |
| p95 3초 미만 | 충족 |

측정값은 실행 장비와 부하 상태에 따라 달라질 수 있다. 이 결과는 코드 동작과
단일 이미지 추론 지연시간 검증이며, HTTP·DB·파일 I/O가 포함된 전체 부하 테스트는
아니다.

## 9. 현재 제한사항

- 제공된 SimpleCNN은 Grad-CAM heatmap을 생성하지 않으므로 `heatmap_url`은 빈 문자열로 저장한다.
- 클래스 순서와 전처리는 팀이 확인한 모델 설정인 `NORMAL=0`, `PNEUMONIA=1`, 흑백 `128x128`을 사용한다.
- 모델의 Accuracy, Precision, Recall, F1-score는 정답 라벨이 포함된 별도 평가 데이터셋이 필요하다.
- 폐렴 탐지에서는 False Negative를 줄이기 위해 향후 `PNEUMONIA Recall`을 주요 지표로 검증한다.
- 예측 결과는 의료진의 진단을 보조하며 최종 진단을 대체하지 않는다.
