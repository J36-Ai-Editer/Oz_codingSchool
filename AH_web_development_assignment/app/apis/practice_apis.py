# app/apis/practice_apis.py
from fastapi import FastAPI, Path, Query
from fastapi import FastAPI, Response
from pydantic import BaseModel, Field, field_validator
import re
app = FastAPI()

user_list = [
	{
		"id": 1,
		"name": "홍길동",
		"age": 24,
		"email": "gildong24@example.com",
		"password": "Password1234!!"
	},
	{
		"id": 2,
		"name": "장문복",
		"age": 21,
		"email": "moonluck12@example.com",
		"password": "Check1321!"
	},
	{
		"id": 3,
		"name": "임우진",
		"age": 31,
		"email": "limousine33@example.com",
		"password": "lwsPAssword12@"
	}
]

가능해요. 단, Path, Query는 “입력값 검증 + Swagger 문서 표시”용이고, 404, 400 상태 코드를 실제 HTTP 상태로 바꾸는 기능은 아니에요.
그래도 수업용/연습용으로는 아래처럼 작성할 수 있습니다.
HTTPException, JSONResponse, Response, EmailStr, Optional 전부 사용하지 않은 버전입니다.
from fastapi import FastAPI, Path, Query
from pydantic import BaseModel, Field, field_validator
import re

app = FastAPI()

user_list = [
    {
        "id": 1,
        "name": "kim",
        "age": 20,
        "email": "kim@test.com",
        "password": "Test!1234"
    },
    {
        "id": 2,
        "name": "lee",
        "age": 25,
        "email": "lee@test.com",
        "password": "Hello@123"
    }
]


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=10)
    age: int = Field(ge=14)
    email: str = Field(max_length=30)
    password: str = Field(min_length=8, max_length=20)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

        if not re.match(email_pattern, value):
            raise ValueError("올바른 이메일 형식이 아닙니다.")

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if not re.search(r"[a-z]", value):
            raise ValueError("비밀번호에는 소문자가 1개 이상 필요합니다.")

        if not re.search(r"[A-Z]", value):
            raise ValueError("비밀번호에는 대문자가 1개 이상 필요합니다.")
		
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("비밀번호에는 특수문자가 1개 이상 필요합니다.")

        return value


class UserUpdate(BaseModel):
    age: int | None = Field(default=None, ge=14)
    email: str | None = Field(default=None, max_length=30)
    password: str | None = Field(default=None, min_length=8, max_length=20)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if value is None:
            return value

        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

        if not re.match(email_pattern, value):
            raise ValueError("올바른 이메일 형식이 아닙니다.")

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if value is None:
            return value
        if not re.search(r"[a-z]", value):
            raise ValueError("비밀번호에는 소문자가 1개 이상 필요합니다.")

        if not re.search(r"[A-Z]", value):
            raise ValueError("비밀번호에는 대문자가 1개 이상 필요합니다.")
		
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("비밀번호에는 특수문자가 1개 이상 필요합니다.")

        return value

@app.get("practice_apie/us")
def find_user(user_id: int):
    for user in user_list:
        if user["id"] == user_id:
            return user
    return None


def hide_password(user):
    return {
        "id": user["id"],
        "name": user["name"],
        "age": user["age"],
        "email": user["email"]
    }


@app.get("/practice_api/users")
def get_users(
    min_age: int | None = Query(default=None, ge=0),
    keyword: str | None = Query(default=None)
):
    result = user_list

    if min_age is not None:
        result = [user for user in result if user["age"] >= min_age]

    if keyword is not None:
        result = [user for user in result if keyword in user["name"]]

    return [hide_password(user) for user in result]


@app.get("/practice_api/users/{user_id}")
def get_user(
    user_id: int = Path(gt=0)
):
    user = find_user(user_id)

    if user is None:
        return {
            "status_code": 404,
            "message": "해당 회원을 찾을 수 없습니다."
        }

    return hide_password(user)


@app.post("/practice_api/users")
def create_user(user: UserCreate):
    for saved_user in user_list:
        if saved_user["email"] == user.email:
            return {
                "status_code": 400,
                "message": "이미 사용 중인 이메일입니다."
            }

    new_user = {
        "id": len(user_list) + 1,
        "name": user.name,
        "age": user.age,
        "email": user.email,
        "password": user.password
    }

    user_list.append(new_user)

    return hide_password(new_user)


@app.patch("/practice_api/users/{user_id}")
def update_user(
    user_id: int = Path(gt=0),
    update_data: UserUpdate = None
):
    user = find_user(user_id)

    if user is None:
        return {
            "status_code": 404,
            "message": "해당 회원을 찾을 수 없습니다."
        }

    if update_data is None:
        return {
            "status_code": 400,
            "message": "수정할 정보를 입력해주세요."
        }

    data = update_data.model_dump(exclude_unset=True)

    if not data:
        return {
            "status_code": 400,
            "message": "수정할 항목을 입력해주세요."
        }

    if "email" in data:
        for saved_user in user_list:
            if saved_user["email"] == data["email"] and saved_user["id"] != user_id:
                return {
                    "status_code": 400,
                    "message": "이미 사용 중인 이메일입니다."
                }

    user.update(data)

    return hide_password(user)


@app.delete("/practice_api/users/{user_id}")
def delete_user(
    user_id: int = Path(gt=0)
):
    user = find_user(user_id)

    if user is None:
        return {
            "status_code": 404,
            "message": "해당 회원을 찾을 수 없습니다."
        }

    user_list.remove(user)

    return {
        "message": "회원 정보가 삭제되었습니다."
    }