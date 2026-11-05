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
    BandRegisterRequest,
    BandUpdateRequest,
    BandDeleteRequest,
    AdminUserUpdateRequest,
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
    if not req.furigana.strip():
        return {"success": False, "message": "フリガナを入力してください"}

    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        new_data = {
            "username": req.username.strip(),
            "furigana": req.furigana.strip(),
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
    if not req.furigana.strip():
        return {"success": False, "message": "フリガナを入力してください"}

    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        updated_data = {
            "furigana": req.furigana.strip(),
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

    if not username:
        return {"success": False, "message": "ユーザー名が指定されていません"}

    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        # 1. 対象ユーザーの存在確認
        check_res = supabase.table("members").select("*").eq("username", username).execute()
        if len(check_res.data) == 0:
            return {"success": False, "message": "対象の部員が見つかりませんでした"}

        # 2. 所属しているバンドの中間テーブル (band_members) から該当ユーザーを削除
        supabase.table("band_members").delete().eq("username", username).execute()

        # 3. Supabase からユーザーデータを削除
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
def sync_member_band_details(usernames: set[str]) -> None:
    if not usernames:
        return

    bands_res = supabase.table("bands").select("id, band_name").execute()
    band_name_map = {band["id"]: band["band_name"] for band in (bands_res.data or [])}

    members_res = supabase.table("band_members").select("*").execute()
    user_bands_map = {username: [] for username in usernames}
    user_instruments_map = {username: [] for username in usernames}

    for row in (members_res.data or []):
        username = row.get("username")
        if username not in usernames:
            continue

        band_name = band_name_map.get(row.get("band_id"), "")
        if band_name and band_name not in user_bands_map[username]:
            user_bands_map[username].append(band_name)

        instrument = str(row.get("part") or row.get("instrument") or "").strip()
        for part in instrument.split():
            if part not in user_instruments_map[username]:
                user_instruments_map[username].append(part)

    for username in usernames:
        supabase.table("members").update({
            "band": ", ".join(user_bands_map[username]),
            "instrument": " ".join(user_instruments_map[username])
        }).eq("username", username).execute()


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
        member_records = []
        for m in req.members:
            if not m.username.strip():
                continue
            
            # フロントから送られてきた instrument または part から値を取得
            inst = getattr(m, 'instrument', None) or getattr(m, 'part', '') or ''
            
            member_records.append({
                "band_id": created_band_id,
                "username": m.username.strip(),
                "part": inst.strip()  # ★ DB(band_members)のカラム名である 'part' に設定！
            })

        if member_records:
            supabase.table("band_members").insert(member_records).execute()
            sync_member_band_details({member["username"] for member in member_records})

        return {
            "success": True,
            "message": f"バンド「{band_name}」を登録しました！"
        }

    except Exception as e:
        print(f"Database error: {e}")
        return {"success": False, "message": "バンド登録処理中にエラーが発生しました"}

# 8. バンド一覧 & メンバー取得 API
@app.get("/api/get-bands")
def get_bands():
    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        # 1. バンド一覧を取得（新しい順）
        bands_res = supabase.table("bands").select("*").order("id", desc=True).execute()
        bands = bands_res.data if bands_res.data else []

        if not bands:
            return {"success": True, "bands": []}

        # 2. 全メンバー構成を取得
        members_res = supabase.table("band_members").select("*").execute()
        all_members = members_res.data if members_res.data else []

        # 3. バンドIDごとにメンバーをグループ化して結合
        result = []
        for band in bands:
            band_id = band["id"]
            # このバンドに所属するメンバーを抽出
            b_members = [m for m in all_members if m["band_id"] == band_id]
            
            result.append({
                "id": band["id"],
                "band_name": band["band_name"],
                "created_at": band.get("created_at"),
                "members": b_members
            })

        return {
            "success": True,
            "bands": result
        }

    except Exception as e:
        print(f"Database error: {e}")
        return {"success": False, "message": "バンド一覧の取得に失敗しました"}

# 9. 指定したバンド1件の詳細取得 API
@app.get("/api/get-band/{band_id}")
def get_band_detail(band_id: int):
    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        # バンド本データの取得
        band_res = supabase.table("bands").select("*").eq("id", band_id).execute()
        if not band_res.data:
            return {"success": False, "message": "指定されたバンドが見つかりません"}

        band = band_res.data[0]

        # 該当バンドのメンバー取得
        members_res = supabase.table("band_members").select("*").eq("band_id", band_id).execute()
        raw_members = members_res.data if members_res.data else []

        # JS側が 'part' または 'instrument' のどちらでも受け取れるように整形
        formatted_members = []
        for m in raw_members:
            # instrument または part の値を安全に取得
            inst = m.get("instrument") or m.get("part") or ""
            formatted_members.append({
                "username": m.get("username", ""),
                "instrument": inst,
                "part": inst  # 両方のキーを持たせておくとJS側でパースエラーを防げます
            })

        return {
            "success": True,
            "band": {
                "id": band["id"],
                "band_name": band["band_name"],
                "members": formatted_members
            }
        }
    except Exception as e:
        print(f"Database error in get_band_detail: {e}")
        return {"success": False, "message": "バンド情報の取得に失敗しました"}


# 10. バンド更新 API（部員名簿 members の自動更新処理付き）
@app.get("/api/get-band/{band_id}") # 上の9番はそのまま

@app.post("/api/update-band")
def update_band(data: BandUpdateRequest):
    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        # 1. バンド名の更新
        supabase.table("bands").update({"band_name": data.band_name}).eq("id", data.band_id).execute()

        # 2. 既存のメンバー構成を一度クリア
        supabase.table("band_members").delete().eq("band_id", data.band_id).execute()

        # 3. 新しいメンバー構成を band_members に登録
        # ※ band_members テーブルには 'band' カラムが無いため除外
        # ※ カラム名は 'part'
        new_members = []
        for m in data.members:
            # instrument または part から値を取得
            inst_val = getattr(m, "instrument", None) or getattr(m, "part", "")
            new_members.append({
                "band_id": data.band_id,
                "username": m.username,
                "part": inst_val
            })

        if new_members:
            supabase.table("band_members").insert(new_members).execute()

        sync_member_band_details({member.username for member in data.members})

        return {"success": True, "message": "バンド情報と部員名簿を更新しました！"}

    except Exception as e:
        print(f"Database error in update_band: {e}")
        return {"success": False, "message": f"バンド情報の更新に失敗しました: {str(e)}"}

# 11. バンド削除 API
@app.post("/api/delete-band")
def delete_band(data: BandDeleteRequest):
    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        # 1. 関連するバンドメンバー情報を先に削除
        supabase.table("band_members").delete().eq("band_id", data.band_id).execute()

        # 2. バンド本体を削除
        res = supabase.table("bands").delete().eq("id", data.band_id).execute()

        if not res.data:
            return {"success": False, "message": "対象のバンドが見つからないか、削除に失敗しました"}

        return {"success": True, "message": "バンドを削除しました！"}

    except Exception as e:
        print(f"Database error: {e}")
        return {"success": False, "message": "バンドの削除に失敗しました"}

# 管理者ユーザー管理 API
@app.get("/api/admin/users")
def get_admin_users():
    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        # "*" を指定して members テーブルの全カラムを取得する
        res = supabase.table("members").select("*").execute()
        users = res.data if res.data else []
        return {"success": True, "users": users}
    except Exception as e:
        print(f"Error fetching users for admin: {e}")
        return {"success": False, "message": "ユーザー一覧の取得に失敗しました"}

# 2. ユーザー強制削除 API（管理者用）
@app.delete("/api/admin/users/{username}")
def delete_user_by_admin(username: str):
    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        # 関連テーブル（band_members）からの削除も合わせて実行
        supabase.table("band_members").delete().eq("username", username).execute()
        
        # members テーブルから削除
        res = supabase.table("members").delete().eq("username", username).execute()
        
        return {"success": True, "message": f"ユーザー '{username}' を削除しました"}
    except Exception as e:
        print(f"Error deleting user {username}: {e}")
        return {"success": False, "message": "ユーザーの削除に失敗しました"}

# 3. ユーザー情報更新 API（管理者用）
@app.post("/api/admin/users/update")
def update_user_by_admin(data: AdminUserUpdateRequest):
    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        update_data = {}
        if data.grade is not None:
            update_data["grade"] = data.grade
        if data.instrument is not None:
            update_data["instrument"] = data.instrument

        if not update_data:
            return {"success": False, "message": "更新対象のデータがありません"}

        supabase.table("members").update(update_data).eq("username", data.username).execute()
        return {"success": True, "message": f"ユーザー '{data.username}' の情報を更新しました"}
    except Exception as e:
        print(f"Error updating user {data.username}: {e}")
        return {"success": False, "message": "ユーザー情報の更新に失敗しました"}