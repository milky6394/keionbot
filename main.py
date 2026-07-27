from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import hashlib
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabaseクライアントの初期化
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# リクエストデータ構造
class LoginRequest(BaseModel):
    password: str

class MemberRequest(BaseModel):
    username: str

# 1. 共通パスワード認証
@app.post("/api/verify-password")
def verify_password(req: LoginRequest):
    stored_hash = os.getenv("ADMIN_PASSWORD_HASH", "").strip()
    salt = os.getenv("ADMIN_SALT", "").strip()
    clean_password = req.password.strip()

    hashed_input = hashlib.sha256((clean_password + salt).encode("utf-8")).hexdigest()

    if hashed_input == stored_hash:
        return {"success": True, "message": "パスワード認証成功"}
    else:
        return {"success": False, "message": "パスワードが正しくありません"}

# 2. 名前チェック ＆ Supabaseへのログイン/保存
@app.post("/api/check-member")
def check_member(req: MemberRequest):
    username = req.username.strip()

    if not username:
        return {"success": False, "message": "名前を入力してください"}

    if not supabase:
        return {"success": False, "message": "データベース接続が設定されていません"}

    try:
        # Supabaseの members テーブルから名前を検索
        response = supabase.table("members").select("*").eq("username", username).execute()
        existing_members = response.data

        # すでに登録されている場合
        if len(existing_members) > 0:
            return {
                "success": True,
                "is_new_user": False,
                "message": f"おかえりなさい、{username}さん！"
            }
        
        # 未登録の場合 ➔ members テーブルに新規挿入
        else:
            supabase.table("members").insert({"username": username}).execute()
            return {
                "success": True,
                "is_new_user": True,
                "message": f"ようこそ！{username}さんを名簿に新規登録しました。"
            }

    except Exception as e:
        print(f"Database error: {e}")
        return {"success": False, "message": "データベース処理中にエラーが発生しました"}