from pydantic import BaseModel
from typing import List, Optional

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
    room: Optional[int] = None
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
    room: Optional[int] = None
    single: bool
    line: str
    multi: str

class DeleteAccountRequest(BaseModel):
    username: str

# 1. メンバー単体の定義（こちらを上に置く）
class BandMemberItem(BaseModel):
    username: str
    part: str

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

# --- イベント作成用 ---
class SlotCreateItem(BaseModel):
    day_of_week: int   # 0:日, 1:月, 2:火, 3:水, 4:木, 5:金, 6:土
    slot_number: int   # 1, 2, 3...
    start_time: str    # "10:00"
    end_time: str      # "11:00"

class EventCreateRequest(BaseModel):
    title: str
    deadline: str      # "YYYY-MM-DDTHH:MM"
    slots: List[SlotCreateItem]

# --- 部員希望提出用 ---
class SingleWishItem(BaseModel):
    slot_id: int
    wish_level: int    # 0: 行けない, 1: 行ける, 2: ここがありがたい

class SubmitWishesRequest(BaseModel):
    event_id: int
    username: str
    wishes: List[SingleWishItem]

class WishSubmitRequest(BaseModel):
    username: str
    wishes: List[SingleWishItem]

# --- 割り当て計算・保存用 ---
class CalculateAssignmentRequest(BaseModel):
    event_id: int

class AssignmentItem(BaseModel):
    slot_id: int
    band_id: Optional[int] = None

class ConfirmAssignmentsRequest(BaseModel):
    assignments: List[AssignmentItem]

class AdminUserUpdateRequest(BaseModel):
    username: str
    grade: Optional[int] = None
    instrument: Optional[str] = None