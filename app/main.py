from fastapi import FastAPI

from app.apis.practice_apis import router as practice_router


app = FastAPI(
    title="FastAPI Practice",
    description="2일차 회원 관리 API 과제",
)
app.include_router(practice_router)


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    return {"message": "FastAPI practice server is running."}
