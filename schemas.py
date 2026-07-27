from pydantic import BaseModel

class LoginRequest(BaseModel):
    password: str

class MemberCheckRequest(BaseModel):
    username: str

class RegisterRequest(BaseModel):
    username: str
    grade: int
    member_class: str
    course: str
    number: str
    gender: str
    dormitory: bool
    room: int | None = None
    single: bool
    line: str
    multi: str

class UpdateMemberRequest(BaseModel):
    username: str
    grade: int
    member_class: str
    course: str
    number: str
    gender: str
    dormitory: bool
    room: int | None = None
    single: bool
    line: str
    multi: str

class DeleteAccountRequest(BaseModel):
    username: str
    password: str