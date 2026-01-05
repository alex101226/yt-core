from typing import List

from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    username: str
    password: str
    domain: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    mobile: str
    nickname: str

    class Config:
        from_attributes = True

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    email: EmailStr
    nickname: str
    domain: str
    # mobile: str = Field( ..., pattern=r"^1[3-9]\d{9}$", description="中国大陆手机号")

class RefreshTokenIn(BaseModel):
    domain: str
    refresh_token: str


class LogoutRequest(BaseModel):
    domain: str
    user_id: int = 0


class UserOutSchema(BaseModel):
    id: int
    username: str
    email: str
    nickname: str
    class Config:
        from_attributes = True

class UserPageSchema(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[UserOutSchema]