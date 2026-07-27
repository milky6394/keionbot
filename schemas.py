from pydantic import BaseModel
from typing import List

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

class BandMemberItem(BaseModel):
    username: str
    part: str

class BandRegisterRequest(BaseModel):
    band_name: str
    members: List[BandMemberItem]