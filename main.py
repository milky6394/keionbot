from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from assignment_logic import calculate_band_assignments
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
    EventCreateRequest,
    WishSubmitRequest,
    SubmitWishesRequest
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
        members = members_res.data if members_res.data else []

        return {
            "success": True,
            "band": {
                "id": band["id"],
                "band_name": band["band_name"],
                "members": members
            }
        }
    except Exception as e:
        print(f"Database error: {e}")
        return {"success": False, "message": "バンド情報の取得に失敗しました"}


# 10. バンド更新 API
@app.post("/api/update-band")
def update_band(data: BandUpdateRequest):
    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        # 1. バンド名の更新
        supabase.table("bands").update({"band_name": data.band_name}).eq("id", data.band_id).execute()

        # 2. 既存のメンバー構成を一度クリア
        supabase.table("band_members").delete().eq("band_id", data.band_id).execute()

        # 3. 新しいメンバー構成を登録
        new_members = [
            {
                "band_id": data.band_id,
                "username": m.username,
                "part": m.part
            }
            for m in data.members
        ]

        if new_members:
            supabase.table("band_members").insert(new_members).execute()

        return {"success": True, "message": "バンド情報を更新しました！"}

    except Exception as e:
        print(f"Database error: {e}")
        return {"success": False, "message": "バンド情報の更新に失敗しました"}

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

# ==================================================
# 練習希望・割り当て機能 API
# ==================================================

# 12. 管理者：練習割り当てイベントの作成 API
@app.post("/api/admin/create-event")
def create_event(data: EventCreateRequest):
    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        # 1. イベント本体の登録
        event_res = supabase.table("practice_events").insert({
            "title": data.title,
            "deadline": data.deadline,
            "status": "open"
        }).execute()

        if not event_res.data:
            return {"success": False, "message": "イベントの作成に失敗しました"}

        event_id = event_res.data[0]["id"]

        # 2. 曜日ベースのコマ枠の一括登録
        slots_to_insert = [
            {
                "event_id": event_id,
                "day_of_week": s.day_of_week,  # date から day_of_week に修正
                "slot_number": s.slot_number,
                "start_time": s.start_time,
                "end_time": s.end_time
            }
            for s in data.slots
        ]

        if slots_to_insert:
            supabase.table("practice_slots").insert(slots_to_insert).execute()

        return {"success": True, "message": "練習イベントを作成しました！", "event_id": event_id}

    except Exception as e:
        print(f"Database error: {e}")
        return {"success": False, "message": f"イベント作成処理中にエラーが発生しました: {str(e)}"}

# 13. 現在アクティブな練習イベントとコマ枠の取得 API (曜日仕様)
@app.get("/api/get-active-event")
def get_active_event():
    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        # 最新のopenまたはpublishedなイベントを取得
        event_res = supabase.table("practice_events") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        if not event_res.data:
            return {"success": False, "message": "現在募集中の練習イベントはありません"}

        event = event_res.data[0]

        # イベントに紐づくコマ枠を取得 (曜日順 -> コマ順でソート)
        slots_res = supabase.table("practice_slots") \
            .select("*") \
            .eq("event_id", event["id"]) \
            .order("day_of_week", desc=False) \
            .order("slot_number", desc=False) \
            .execute()

        return {
            "success": True,
            "event": event,
            "slots": slots_res.data if slots_res.data else []
        }

    except Exception as e:
        print(f"Database error: {e}")
        return {"success": False, "message": "イベントデータの取得に失敗しました"}

# 14. 部員：個人希望の提出・一括更新 API
@app.post("/api/submit-wishes")
def submit_wishes(data: SubmitWishesRequest):
    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        # UPSERT 用のデータを作成
        records = [
            {
                "event_id": data.event_id,
                "username": data.username,
                "slot_id": w.slot_id,
                "wish_level": w.wish_level
            }
            for w in data.wishes
        ]

        # 既存データを一括更新 (ON CONFLICT ON (username, slot_id) DO UPDATE)
        supabase.table("practice_wishes").upsert(
            records,
            on_conflict="username,slot_id"
        ).execute()

        return {"success": True, "message": "希望を正常に保存しました"}

    except Exception as e:
        print(f"Database error: {e}")
        return {"success": False, "message": f"希望の保存中にエラーが発生しました: {str(e)}"}

# 15. 部員：自分が提出済みの希望一覧取得 API
@app.get("/api/get-user-wishes/{event_id}/{username}")
def get_user_wishes(event_id: int, username: str):
    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        res = supabase.table("practice_wishes") \
            .select("*") \
            .eq("event_id", event_id) \
            .eq("username", username) \
            .execute()

        return {"success": True, "wishes": res.data if res.data else []}
    except Exception as e:
        return {"success": False, "message": str(e)}

# 16. バンド単位の希望集計 API (曜日仕様 & 全員可でないとNGルール適用)
@app.get("/api/get-band-wishes/{event_id}/{band_id}")
def get_band_wishes(event_id: int, band_id: int):
    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        # 1. バンドメンバー一覧の取得
        members_res = supabase.table("band_members").select("username").eq("band_id", band_id).execute()
        if not members_res.data:
            return {"success": False, "message": "該当バンドにメンバーが登録されていません"}

        member_usernames = [m["username"] for m in members_res.data]
        member_count = len(member_usernames)

        # 2. 対象イベントの全コマ枠を取得 (曜日順 -> コマ順でソート)
        slots_res = supabase.table("practice_slots") \
            .select("*") \
            .eq("event_id", event_id) \
            .order("day_of_week", desc=False) \
            .order("slot_number", desc=False) \
            .execute()
        
        slots = slots_res.data if slots_res.data else []

        if not slots:
            return {"success": True, "band_wishes": []}

        slot_ids = [s["id"] for s in slots]

        # 3. メンバー全員の全回答を一括取得
        wishes_res = supabase.table("practice_wishes") \
            .select("*") \
            .in_("slot_id", slot_ids) \
            .in_("username", member_usernames) \
            .execute()

        # データをコマIDごとにグループ化 -> { slot_id: { username: wish_level } }
        wishes_by_slot = {}
        for w in (wishes_res.data or []):
            sid = w["slot_id"]
            if sid not in wishes_by_slot:
                wishes_by_slot[sid] = {}
            wishes_by_slot[sid][w["username"]] = w["wish_level"]

        # 4. 各コマごとにバンド全体の希望を判定
        band_wishes_result = []

        for slot in slots:
            sid = slot["id"]
            user_responses = wishes_by_slot.get(sid, {})

            # 全員が未提出の場合は未確定（1人でも未回答なら安全のため0=NG扱い）
            if len(user_responses) < member_count:
                band_status = 0
            else:
                levels = list(user_responses.values())

                # 【最重要制約】1人でも 0 (行けない) が入っていればバンド全体も 0 (行けない)
                if 0 in levels:
                    band_status = 0
                elif all(lvl == 2 for lvl in levels):
                    band_status = 2 # 全員「ここがありがたい」
                else:
                    band_status = 1 # 全員行ける（1または2混在）

            band_wishes_result.append({
                "slot_id": sid,
                "day_of_week": slot["day_of_week"], # date から day_of_week に変更
                "slot_number": slot["slot_number"],
                "start_time": slot["start_time"],
                "end_time": slot["end_time"],
                "band_status": band_status,
                "member_responses": user_responses # 個別状況のデバッグ・確認用
            })

        return {
            "success": True,
            "band_id": band_id,
            "member_count": member_count,
            "band_wishes": band_wishes_result
        }

    except Exception as e:
        print(f"Database error: {e}")
        return {"success": False, "message": f"バンド希望集計中にエラーが発生しました: {str(e)}"}

@app.post("/api/admin/calculate-and-save-assignments/{event_id}")
def calculate_and_save_assignments(event_id: int):
    if not supabase:
        return {"success": False, "message": "データベース接続エラー"}

    try:
        # 1. 必要なデータを一括取得
        slots_res = supabase.table("practice_slots").select("*").eq("event_id", event_id).execute()
        bands_res = supabase.table("bands").select("*").execute()
        members_res = supabase.table("band_members").select("*").execute()
        wishes_res = supabase.table("practice_wishes").select("*").eq("event_id", event_id).execute()

        slots = slots_res.data or []
        bands = bands_res.data or []
        band_members = members_res.data or []
        wishes = wishes_res.data or []

        if not slots or not bands:
            return {"success": False, "message": "計算に必要なコマ枠またはバンドデータが存在しません"}

        # 2. 自動割り当て計算を実行
        assignments = calculate_band_assignments(slots, bands, band_members, wishes)

        # 3. 既存の割り当て結果をクリアして更新保存
        supabase.table("practice_assignments").delete().eq("event_id", event_id).execute()

        if assignments:
            records_to_insert = [
                {
                    "event_id": event_id,
                    "slot_id": a["slot_id"],
                    "band_id": a["band_id"]
                }
                for a in assignments
            ]
            supabase.table("practice_assignments").insert(records_to_insert).execute()

        # 4. イベントステータスを 'published' に更新
        supabase.table("practice_events").update({"status": "published"}).eq("id", event_id).execute()

        return {
            "success": True,
            "message": f"自動割り当てが完了しました！（割り当て数: {len(assignments)}コマ）",
            "assignments": assignments
        }

    except Exception as e:
        print(f"Assignment calculation error: {e}")
        return {"success": False, "message": f"計算処理中にエラーが発生しました: {str(e)}"}

# 17. 割り当て結果の取得 API
@app.get("/api/get-assignments/{event_id}")
async def get_assignments(event_id: int):
    """
    指定されたイベントの割り当て結果を取得し、バンド名と紐付けて返す
    """
    try:
        # 1. practice_assignments から対象イベントの割当を取得
        assign_res = supabase.table("practice_assignments") \
            .select("slot_id, band_id") \
            .eq("event_id", event_id) \
            .execute()

        if not assign_res.data:
            return {"success": True, "assignments": []}

        # 2. 全バンド情報を取得して ID -> 名前 の辞書を作成 (確実に名前をひくため)
        bands_res = supabase.table("bands").select("id, name").execute()
        band_map = {}
        if bands_res.data:
            for b in bands_res.data:
                band_map[str(b["id"])] = b.get("name", "名称不明")

        # 3. 割当データにバンド名をセット
        assignments = []
        for row in assign_res.data:
            b_id = str(row.get("band_id"))
            assignments.append({
                "slot_id": row.get("slot_id"),
                "band_id": row.get("band_id"),
                "band_name": band_map.get(b_id, "名称不明")
            })

        return {"success": True, "assignments": assignments}

    except Exception as e:
        print(f"Get Assignments Error: {e}")
        return {"success": False, "message": f"割り当てデータの取得に失敗しました: {str(e)}", "assignments": []}

@app.post("/api/admin/publish-event/{event_id}")
async def publish_event(event_id: int):
    """
    割り当て結果を確定し、イベントのステータスを『公開/確定済み』に変更する
    """
    try:
        # イベントの status を 'published' に更新
        res = supabase.table("practice_events").update({
            "status": "published"
        }).eq("id", event_id).execute()

        if not res.data:
            return {"success": False, "message": "対象のイベントが見つかりませんでした。"}

        return {
            "success": True, 
            "message": "割り当て結果を確定・公開しました！部員画面から確認可能になります。"
        }
    except Exception as e:
        print(f"Publish Error: {e}")
        return {"success": False, "message": f"エラーが発生しました: {str(e)}"}