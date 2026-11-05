from pydantic import BaseModel
from typing import List, Optional

class LoginRequest(BaseModel):
    password: str

class MemberCheckRequest(BaseModel):
    username: str

class RegisterRequest(BaseModel):
    username: str
    furigana: str
    grade: int
    member_class: str
    course: str
    number: str
    gender: str
    dormitory: bool
    room: Optional[int] = None
    single: bool
    line: str
    multi: str

class UpdateMemberRequest(BaseModel):
    username: str
    furigana: str
    grade: int
    member_class: str
    course: str
    number: str
    gender: str
    dormitory: bool
    room: Optional[int] = None
    single: bool
    line: str
    multi: str

class DeleteAccountRequest(BaseModel):
    username: str

# 1. メンバー単体の定義（こちらを上に置く）
class BandMemberItem(BaseModel):
    username: str
    instrument: Optional[str] = None  # ★ DB用の instrument を追加
    part: Optional[str] = None        # ★ 既存の part も受け取れるように残す

# 2. バンド全体の定義（上で定義した BandMemberItem を使う）
class BandRegisterRequest(BaseModel):
    band_name: str
    members: List[BandMemberItem]

# バンド編集用のメンバー構造
class MemberUpdateItem(BaseModel):
    username: str
    part: str

class BandMemberData(BaseModel):
    username: str
    instrument: Optional[str] = None
    part: Optional[str] = None

# バンド編集リクエストボディ
class BandUpdateRequest(BaseModel):
    band_id: int
    band_name: str
    members: List[BandMemberData]

class BandDeleteRequest(BaseModel):
    band_id: int

class AdminUserUpdateRequest(BaseModel):
    username: str
    grade: Optional[int] = None
    instrument: Optional[str] = None