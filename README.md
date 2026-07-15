AI 헬스케어 Web Development

## 2일차 FastAPI 회원 관리 과제

### 설치 및 실행

```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

서버 실행 후 다음 주소에서 API를 확인할 수 있습니다.

- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>

### API

| Method | Endpoint | 설명 |
|---|---|---|
| `GET` | `/practice_api/users` | 모든 회원 조회 |
| `GET` | `/practice_api/users/{user_id}` | 특정 회원 조회 |
| `POST` | `/practice_api/users` | 회원 추가 |
| `PATCH` | `/practice_api/users/{user_id}` | 회원 정보 일부 수정 |
| `DELETE` | `/practice_api/users/{user_id}` | 특정 회원 삭제 |

### 테스트

```powershell
python -m pytest -q
```
