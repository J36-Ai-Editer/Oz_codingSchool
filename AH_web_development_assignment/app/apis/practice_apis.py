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


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=10)
    age: int = Field(ge=14)
    email: str = Field(max_length=30)
    password: str = Field(min_length=8, max_length=20)


class UserUpdate(BaseModel):
    age: int = Field(ge=14)
    email: str = Field(max_length=30)
    


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


def is_valid_email(email: str):
    email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(email_pattern, email) is not None


def is_duplicate_email(email: str, user_id=None):
    for user in user_list:
        if user["email"] == email and user["id"] != user_id:
            return True
    return False


def is_valid_password(password: str):
    if re.search(r"[A-Z]", password) is None:
        return False

    if re.search(r"[a-z]", password) is None:
        return False

    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password) is None:
        return False

    return True


@app.get("/practice_api/users", status_code=200)
def get_users():
    return [hide_password(user) for user in user_list]


@app.get("/practice_api/users/{user_id}", status_code=200)
def get_user(user_id: int = Path(...)):
    user = find_user(user_id)

    if user is None:
        return {
            "message": "유효한 id가 아닙니다."
        }

    return hide_password(user)


@app.post("/practice_api/users", status_code=201)
def create_user(user: UserCreate):
    if not is_valid_email(user.email):
        return {
            "message": "email 형식이 올바르지 않습니다."
        }

    if is_duplicate_email(user.email):
        return {
            "message": "중복된 email은 사용할 수 없습니다."
        }

    if not is_valid_password(user.password):
        return {
            "message": "비밀번호는 대문자, 소문자, 특수문자가 각각 1개 이상 필요합니다."
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


@app.patch("/practice_api/users/{user_id}", status_code=200)
def update_user(
    user_id: int = Path(...),
    update_data: UserUpdate = None
):
    user = find_user(user_id)

    if user is None:
        return {
            "message": "유효한 id가 아닙니다."
        }

    if update_data is None:
        return {
            "message": "수정할 정보를 입력해주세요."
        }

    if not is_valid_email(update_data.email):
        return {
            "message": "email 형식이 올바르지 않습니다."
        }

    if is_duplicate_email(update_data.email, user_id):
        return {
            "message": "중복된 email은 사용할 수 없습니다."
        }

    user["age"] = update_data.age
    user["email"] = update_data.email

    return {
        "message": "회원 정보가 수정되었습니다.",
        "user": {
            "age": user["age"],
            "email": user["email"],
            "password": user["password"]
        }
    }


@app.delete("/practice_api/users/{user_id}", status_code=200)
def delete_user(user_id: int = Path(...)):
    user = find_user(user_id)

    if user is None:
        return {
            "message": "유효한 id가 아닙니다."
        }

    user_list.remove(user)

    return {
        "message": "회원 정보가 삭제 되었습니다."}