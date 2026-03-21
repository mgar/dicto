from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleSignInRequest(BaseModel):
    credential: str


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    is_admin: bool = False
