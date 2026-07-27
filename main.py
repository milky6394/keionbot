from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import hashlib
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエストデータの定義
class LoginRequest(BaseModel):
    password: str

class MemberRequest(BaseModel):
    username: str

MEMBERS_FILE = "members.json"

# 名簿（メンバー一覧）の読み込み
def load_members():
    if not os.path.exists(MEMBERS_FILE):
        return []
    with open(MEMBERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

# 名簿の保存
def save_members(members):
    with open(MEMBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(members, f, ensure_ascii=False, indent=2)


# --- 1. 部の共通パスワード認証 ---
@app.post("/api/verify-password")
def verify_password(req: LoginRequest):
    stored_hash = os.getenv("ADMIN_PASSWORD_HASH", "").strip()
    salt = os.getenv("ADMIN_SALT", "").strip()
    clean_password = req.password.strip()

    # ハッシュ化して照合
    hashed_input = hashlib.sha256((clean_password + salt).encode("utf-8")).hexdigest()

    if hashed_input == stored_hash:
        return {"success": True, "message": "パスワード認証成功"}
    else:
        return {"success": False, "message": "パスワードが正しくありません"}


# --- 2. 名前チェック ＆ ログイン／登録分岐 ---
@app.post("/api/check-member")
def check_member(req: MemberRequest):
    username = req.username.strip()

    if not username:
        return {"success": False, "message": "名前を入力してください"}

    members = load_members()

    # 既存ユーザーかどうかの判定
    if username in members:
        return {
            "success": True,
            "is_new_user": False,
            "message": f"おかえりなさい、{username}さん！"
        }
    else:
        # 未登録なら名簿に追加して保存
        members.append(username)
        save_members(members)
        return {
            "success": True,
            "is_new_user": True,
            "message": f"ようこそ！{username}さんを名簿に新規登録しました。"
        }