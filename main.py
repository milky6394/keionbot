from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
import hashlib
import os

from config import supabase
# schemas.py からすべての型定義をインポート
from schemas import (
    LoginRequest,
    MemberCheckRequest,
    RegisterRequest,
    UpdateMemberRequest,
    DeleteAccountRequest,
    BandRegisterRequest
)

# --------------------------------------------------
# FastAPI アプリ初期化 & CORS設定
# --------------------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# API エンドポイント
# --------------------------------------------------

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


# 2. 名前チェック ＆ 既存データの返却
@app.post("/api/check-member")
def check_member(req: MemberCheckRequest):
    username = req.username.strip()

    if not username:
        return {"success": False, "message": "名前を入力してください"}

    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        response = supabase.table("members").select("*").eq("username", username).execute()
        
        if len(response.data) > 0:
            return {
                "success": True,
                "is_new_user": False,
                "user_data": response.data[0],
                "message": f"おかえりなさい、{username}さん！"
            }
        else:
            return {
                "success": True,
                "is_new_user": True,
                "message": f"{username}さんは未登録です。プロフィールを入力してください。"
            }

    except Exception as e:
        print(f"Database error: {e}")
        return {"success": False, "message": "データベース処理エラー"}


# 3. 新規部員アカウント登録
@app.post("/api/register-member")
def register_member(req: RegisterRequest):
    if not req.username.strip():
        return {"success": False, "message": "名前を入力してください"}

    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        new_data = {
            "username": req.username.strip(),
            "grade": req.grade,
            "class": req.member_class.strip(),
            "course": req.course.strip(),
            "number": req.number.strip(),
            "gender": req.gender.strip(),
            "dormitory": req.dormitory,
            "room": req.room,
            "single": req.single,
            "line": req.line.strip(),
            "multi": req.multi.strip(),
            "update": date.today().isoformat()
        }
        
        res = supabase.table("members").insert(new_data).execute()
        created_user = res.data[0] if res.data else new_data

        return {
            "success": True,
            "user_data": created_user,
            "message": f"ようこそ！{req.username}さんの部員登録が完了しました。"
        }
    except Exception as e:
        print(f"Database error: {e}")
        return {"success": False, "message": "登録処理中にエラーが発生しました"}


# 4. 部員情報の更新 API
@app.put("/api/update-member")
def update_member(req: UpdateMemberRequest):
    username = req.username.strip()

    if not username:
        return {"success": False, "message": "ユーザー名が不整合です"}

    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        updated_data = {
            "grade": req.grade,
            "class": req.member_class.strip(),
            "course": req.course.strip(),
            "number": req.number.strip(),
            "gender": req.gender.strip(),
            "dormitory": req.dormitory,
            "room": req.room,
            "single": req.single,
            "line": req.line.strip(),
            "multi": req.multi.strip(),
            "update": date.today().isoformat()
        }

        res = supabase.table("members").update(updated_data).eq("username", username).execute()

        if len(res.data) > 0:
            return {
                "success": True,
                "user_data": res.data[0],
                "message": "プロフィール情報を更新しました。"
            }
        else:
            return {"success": False, "message": "対象の部員が見つかりませんでした"}

    except Exception as e:
        print(f"Database error: {e}")
        return {"success": False, "message": "更新処理中にエラーが発生しました"}


# 5. 全部員一覧取得 API
@app.get("/api/get-members")
def get_members():
    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        res = supabase.table("members").select("*").order("grade").order("number").execute()

        return {
            "success": True,
            "members": res.data
        }
    except Exception as e:
        print(f"Database error: {e}")
        return {"success": False, "message": "部員データの取得に失敗しました"}


# 6. アカウント削除（退部） API
@app.post("/api/delete-account")
def delete_account(req: DeleteAccountRequest):
    username = req.username.strip()
    clean_password = req.password.strip()

    if not username or not clean_password:
        return {"success": False, "message": "ユーザー名とパスワードを入力してください"}

    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    # 1. 共通パスワード認証のチェック
    stored_hash = os.getenv("ADMIN_PASSWORD_HASH", "").strip()
    salt = os.getenv("ADMIN_SALT", "").strip()
    hashed_input = hashlib.sha256((clean_password + salt).encode("utf-8")).hexdigest()

    if hashed_input != stored_hash:
        return {"success": False, "message": "パスワードが正しくありません"}

    try:
        # 2. 対象ユーザーの存在確認
        check_res = supabase.table("members").select("*").eq("username", username).execute()
        if len(check_res.data) == 0:
            return {"success": False, "message": "対象の部員が見つかりませんでした"}

        # 3. Supabase からデータ削除
        res = supabase.table("members").delete().eq("username", username).execute()

        if len(res.data) > 0:
            return {
                "success": True,
                "message": f"{username}さんのアカウントを削除（退部完了）しました。"
            }
        else:
            return {"success": False, "message": "削除処理に失敗しました"}

    except Exception as e:
        print(f"Database delete error: {e}")
        return {"success": False, "message": "削除処理中にエラーが発生しました"}


# 7. バンド新規登録 API
@app.post("/api/register-band")
def register_band(req: BandRegisterRequest):
    band_name = req.band_name.strip()

    if not band_name:
        return {"success": False, "message": "バンド名を入力してください"}

    if not req.members or len(req.members) == 0:
        return {"success": False, "message": "メンバーを1人以上追加してください"}

    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        # 1. 重複チェック
        existing = supabase.table("bands").select("*").eq("band_name", band_name).execute()
        if len(existing.data) > 0:
            return {"success": False, "message": "そのバンド名は既に登録されています"}

        # 2. bands テーブルにバンドを作成
        band_res = supabase.table("bands").insert({"band_name": band_name}).execute()
        if not band_res.data:
            return {"success": False, "message": "バンドの作成に失敗しました"}

        created_band_id = band_res.data[0]["id"]

        # 3. band_members テーブルにメンバー＆パート情報をまとめて一括登録
        member_records = [
            {
                "band_id": created_band_id,
                "username": m.username.strip(),
                "part": m.part.strip()
            }
            for m in req.members if m.username.strip()
        ]

        if member_records:
            supabase.table("band_members").insert(member_records).execute()

        return {
            "success": True,
            "message": f"バンド「{band_name}」を登録しました！"
        }

    except Exception as e:
        print(f"Database error: {e}")
        return {"success": False, "message": "バンド登録処理中にエラーが発生しました"}