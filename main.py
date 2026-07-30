from fastapi import FastAPI
from fastapi import Body
from fastapi.middleware.cors import CORSMiddleware
from assignment_logic import calculate_band_assignments
from datetime import date
import hashlib
import os
import random  # 優先度が並んだ際 ランダム要素で分ける用

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
        new_members = [
            {
                "band_id": data.band_id,
                "band": data.band_name,
                "username": m.username,
                # Pydanticモデルが instrument / part のどちらで受けていても拾えるように対応
                "instrument": getattr(m, "instrument", None) or getattr(m, "part", "")
            }
            for m in data.members
        ]

        if new_members:
            supabase.table("band_members").insert(new_members).execute()

        # -------------------------------------------------------------
        # ★ 4. members テーブル（部員名簿）の所属バンド・担当楽器を自動更新 ★
        # -------------------------------------------------------------
        # 登録された全 band_members から各部員の最新情報をまとめて集計
        all_bm_res = supabase.table("band_members").select("*").execute()
        all_bm = all_bm_res.data if all_bm_res.data else []

        # ユーザーごとにバンドリストと楽器リストを整理
        user_bands_map = {}
        user_inst_map = {}

        for row in all_bm:
            uname = row.get("username")
            b_name = row.get("band") or ""
            inst_str = row.get("instrument") or row.get("part") or ""

            if not uname:
                continue

            if uname not in user_bands_map:
                user_bands_map[uname] = []
                user_inst_map[uname] = []

            # 所属バンドを追加（重複なし）
            if b_name and b_name not in user_bands_map[uname]:
                user_bands_map[uname].append(b_name)

            # 担当楽器を分解して追加（重複なし）
            parts = inst_str.strip().split()
            for p in parts:
                if p and p not in user_inst_map[uname]:
                    user_inst_map[uname].append(p)

        # 今回更新に関わったメンバーの members テーブルを UPDATE
        for m in data.members:
            uname = m.username
            bands_str = ", ".join(user_bands_map.get(uname, []))
            # 担当楽器を半角スペース区切りで結合（例: "Gt Vo"）
            inst_str = " ".join(user_inst_map.get(uname, []))

            supabase.table("members").update({
                "band": bands_str,         # 部員名簿の所属バンド項目
                "instrument": inst_str     # 部員名簿の担当楽器項目（半角スペース区切り）
            }).eq("username", uname).execute()

        return {"success": True, "message": "バンド情報と部員名簿を更新しました！"}

    except Exception as e:
        print(f"Database error in update_band: {e}")
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
# 1. 常設20コマの取得
@app.get("/api/get-practice-slots")
async def get_practice_slots():
    try:
        res = supabase.table("practice_slots") \
            .select("*") \
            .order("day_of_week") \
            .order("slot_number") \
            .execute()
        return {"success": True, "slots": res.data or []}
    except Exception as e:
        print(f"Get Slots Error: {e}")
        return {"success": False, "message": str(e), "slots": []}

# 2. ユーザーの練習希望を取得
@app.get("/api/get-user-wishes/{username}")
async def get_user_wishes(username: str):
    try:
        res = supabase.table("practice_wishes") \
            .select("slot_id, wish_level") \
            .eq("username", username) \
            .execute()
        return {"success": True, "wishes": res.data or []}
    except Exception as e:
        print(f"Get Wishes Error: {e}")
        return {"success": False, "message": str(e), "wishes": []}

# 3. 練習希望の保存（DELETE + INSERT）
@app.post("/api/submit-wishes")
async def submit_wishes(payload: dict):
    username = payload.get("username")
    wishes = payload.get("wishes", [])
    if not username:
        return {"success": False, "message": "ユーザー名が必要です。"}

    try:
        # 古い希望データをクリアして再登録
        supabase.table("practice_wishes").delete().eq("username", username).execute()

        insert_data = [
            {"username": username, "slot_id": w["slot_id"], "wish_level": w["wish_level"]}
            for w in wishes
        ]
        if insert_data:
            supabase.table("practice_wishes").insert(insert_data).execute()

        return {"success": True, "message": "練習希望を保存しました！"}
    except Exception as e:
        print(f"Submit Wishes Error: {e}")
        return {"success": False, "message": f"保存エラー: {str(e)}"}

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
    指定されたイベントの割り当て結果を取得し、バンド名(band_name)と紐付けて返す
    """
    try:
        # 1. practice_assignments から対象イベントの割当を取得
        assign_res = supabase.table("practice_assignments") \
            .select("slot_id, band_id") \
            .eq("event_id", event_id) \
            .execute()

        if not assign_res.data:
            return {"success": True, "assignments": []}

        # 2. 全バンド情報を取得（id と band_name）
        bands_res = supabase.table("bands").select("id, band_name").execute()
        band_map = {}
        if bands_res.data:
            for b in bands_res.data:
                band_map[str(b["id"])] = b.get("band_name", "名称不明")

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

# 1. 割り当て結果の取得（event_id不問）
@app.get("/api/get-assignments")
async def get_assignments():
    try:
        assign_res = supabase.table("practice_assignments").select("slot_id, band_id").execute()
        if not assign_res.data:
            return {"success": True, "assignments": []}

        bands_res = supabase.table("bands").select("id, band_name").execute()
        band_map = {str(b["id"]): b.get("band_name", "名称不明") for b in (bands_res.data or [])}

        assignments = [
            {
                "slot_id": row["slot_id"],
                "band_id": row["band_id"],
                "band_name": band_map.get(str(row["band_id"]), "名称不明")
            }
            for row in assign_res.data
        ]
        return {"success": True, "assignments": assignments}
    except Exception as e:
        print(f"Get Assignments Error: {e}")
        return {"success": False, "message": str(e), "assignments": []}


# 2. 自動割当の実行（現時点の練習希望から再計算）
@app.post("/api/admin/calculate-assignments")
async def calculate_assignments():
    try:
        # 1. 常設コマ（20コマ）の取得
        slots_res = supabase.table("practice_slots").select("id").execute()
        all_slots = slots_res.data or []
        if not all_slots:
            return {"success": False, "message": "コマ枠データ(practice_slots)が存在しません。"}

        # 2. 部員全員の希望データ (practice_wishes) の取得
        wishes_res = supabase.table("practice_wishes").select("username, slot_id, wish_level").execute()
        all_wishes = wishes_res.data or []

        # 3. バンド一覧と各バンドのメンバー情報の取得
        bands_res = supabase.table("bands").select("id, band_name").execute()
        bands = bands_res.data or []
        
        # band_members テーブルからメンバーを取得 (テーブル名・列名は環境に合わせて確認してください)
        members_res = supabase.table("band_members").select("band_id, username").execute()
        band_members_list = members_res.data or []

        # バンドごとのメンバーリストを作成
        band_to_members = {}
        for bm in band_members_list:
            b_id = bm["band_id"]
            if b_id not in band_to_members:
                band_to_members[b_id] = []
            band_to_members[b_id].append(bm["username"])

        # ユーザー×コマの希望レベルマップを作成 { (username, slot_id): wish_level }
        wish_map = {}
        for w in all_wishes:
            wish_map[(w["username"], w["slot_id"])] = w["wish_level"]

        # --- 割り当てアルゴリズム ---
        # 各コマについて、すべてのバンドの「参加可能度（メンバー全員の希望の最低値）」を計算
        # 0: 全員◯/◎ではない（1人でも✕がいる） -> NG
        # 1: 全員行ける（◯以上）
        # 2: 全員が◎
        
        assigned_slots = set()      # 既に埋まったコマID
        assigned_bands = set()      # 既にコマが割り当たったバンドID
        new_assignments = []

        # すべての (バンド, コマ) の組み合わせのスコアを算出
        candidates = []
        for band in bands:
            b_id = band["id"]
            members = band_to_members.get(b_id, [])
            if not members:
                continue

            for slot in all_slots:
                s_id = slot["id"]
                
                # メンバー全員の希望チェック
                member_wishes = [wish_map.get((m, s_id), 1) for m in members] # デフォルト1(◯)
                
                # 1人でも 0(✕) がいればそのコマは入れない
                if 0 in member_wishes:
                    continue
                
                # 全員が 2(◎) ならスコア2、それ以外で全員1(◯)以上ならスコア1
                score = 2 if all(w == 2 for w in member_wishes) else 1
                
                # ランダム要素（同点時の分散用）
                candidates.append({
                    "band_id": b_id,
                    "slot_id": s_id,
                    "score": score,
                    "rand": random.random()
                })

        # スコアが高い順（同点ならランダム）に並び替え
        candidates.sort(key=lambda x: (x["score"], x["rand"]), reverse=True)

        # 1バンドにつき最大1コマ、1コマにつき1バンドを割り当て
        for cand in candidates:
            b_id = cand["band_id"]
            s_id = cand["slot_id"]

            if b_id not in assigned_bands and s_id not in assigned_slots:
                assigned_bands.add(b_id)
                assigned_slots.add(s_id)
                new_assignments.append({
                    "slot_id": s_id,
                    "band_id": b_id
                })

        # 4. データベースの更新
        # 既存の割り当てを一度クリア
        supabase.table("practice_assignments").delete().neq("id", 0).execute()

        # 計算結果を挿入
        if new_assignments:
            supabase.table("practice_assignments").insert(new_assignments).execute()

        return {
            "success": True, 
            "message": f"割り当てを更新しました！（{len(new_assignments)}件のバンドを自動割り当て）"
        }

    except Exception as e:
        print(f"Calculate Assignments Error: {e}")
        return {"success": False, "message": f"計算エラー: {str(e)}"}

# 3. 手動での割当変更・解除
@app.post("/api/admin/update-assignment")
async def update_assignment(payload: dict):
    slot_id = payload.get("slot_id")
    band_id = payload.get("band_id")

    if not slot_id:
        return {"success": False, "message": "slot_id は必須です。"}

    try:
        if band_id:
            # 該当スロットの割り当てを更新（UPSERT）
            supabase.table("practice_assignments").upsert(
                {"slot_id": slot_id, "band_id": band_id},
                on_conflict="slot_id"
            ).execute()
        else:
            # 未割り当て選択時は削除
            supabase.table("practice_assignments").delete().eq("slot_id", slot_id).execute()

        return {"success": True, "message": "割り当てを更新しました。"}
    except Exception as e:
        print(f"Update Assignment Error: {e}")
        return {"success": False, "message": str(e)}

# ユーザーが所属するバンド一覧の取得
@app.get("/api/get-user-bands/{username}")
async def get_user_bands(username: str):
    try:
        # band_members テーブルから該当ユーザーのバンドIDを取得
        res = supabase.table("band_members").select("band_id").eq("username", username).execute()
        if not res.data:
            return {"success": True, "bands": []}

        band_ids = [r["band_id"] for r in res.data]
        
        # バンド名を取得
        bands_res = supabase.table("bands").select("id, band_name").in_("id", band_ids).execute()
        return {"success": True, "bands": bands_res.data or []}
    except Exception as e:
        print(f"Get User Bands Error: {e}")
        return {"success": False, "message": str(e), "bands": []}

# 指定バンドのメンバーおよび全員の希望データ取得
@app.get("/api/get-band-members-wishes/{band_id}")
async def get_band_members_wishes(band_id: int):
    try:
        # 1. バンドメンバーを取得
        members_res = supabase.table("band_members").select("username").eq("band_id", band_id).execute()
        members = members_res.data or []
        
        if not members:
            return {"success": True, "members": [], "wishes_map": {}}

        member_usernames = [m["username"] for m in members]

        # 2. メンバー全員の練習希望データを取得
        wishes_res = supabase.table("practice_wishes").select("username, slot_id, wish_level").in_("username", member_usernames).execute()
        wishes = wishes_res.data or []

        # 3. { username: { slot_id: wish_level } } の構造に整理
        wishes_map = {}
        for w in wishes:
            uname = w["username"]
            s_id = w["slot_id"]
            w_lvl = w["wish_level"]

            if uname not in wishes_map:
                wishes_map[uname] = {}
            wishes_map[uname][s_id] = w_lvl

        return {
            "success": True,
            "members": members,
            "wishes_map": wishes_map
        }
    except Exception as e:
        print(f"Get Band Members Wishes Error: {e}")
        return {"success": False, "message": str(e)}

# 1. 自動割当案の試算API（DBは更新せず結果だけ返す）
@app.post("/api/admin/calculate-assignments-draft")
async def calculate_assignments_draft():
    try:
        # 1. Supabaseから必要データをすべて一括取得
        slots_res = supabase.table("practice_slots").select("*").execute()
        bands_res = supabase.table("bands").select("*").execute()
        members_res = supabase.table("band_members").select("*").execute()
        wishes_res = supabase.table("practice_wishes").select("*").execute()

        event_slots = slots_res.data or []
        bands = bands_res.data or []
        band_members = members_res.data or []
        all_wishes = wishes_res.data or []

        # 2. ロジック関数を呼び出して割り当て計算を実行！
        calculated_assignments = calculate_band_assignments(
            event_slots=event_slots,
            bands=bands,
            band_members=band_members,
            all_wishes=all_wishes
        )

        # 3. 計算されたドラフト割当案をフロントエンドに返す（まだDBには保存しない）
        return {
            "success": True, 
            "assignments": calculated_assignments
        }

    except Exception as e:
        print(f"Draft Calculation Error: {e}")
        return {"success": False, "message": f"計算処理中にエラーが発生しました: {str(e)}"}

# 2. 割当の一括確定API（DBに一括保存して全体公開）
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import traceback

@app.post("/api/admin/confirm-assignments")
async def confirm_assignments(request: Request):
    try:
        # リクエスト JSON を生データとして取得
        body = await request.json()
        print("RECEIVED BODY:", body)

        assignments = body.get("assignments", [])

        # 1. 保存対象のデータ（band_id が入っているもの）を整形
        new_records = []
        for item in assignments:
            s_id = item.get("slot_id")
            b_id = item.get("band_id")

            if s_id is not None and b_id is not None:
                new_records.append({
                    "slot_id": int(s_id),
                    "band_id": int(b_id)
                })

        # 2. 既存の割り当てを一度全削除
        # eq ではなく delete().neq("slot_id", -99999) 等で全削除
        try:
            supabase.table("practice_assignments").delete().neq("slot_id", -99999).execute()
        except Exception as del_err:
            print("Delete error (Ignored):", del_err)

        # 3. 新しい割当を保存
        if new_records:
            supabase.table("practice_assignments").insert(new_records).execute()

        return JSONResponse(content={"success": True, "message": "確定保存完了"})

    except Exception as e:
        # 発生したエラーとトレースバック（スタックトレース）を出力
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        print(f"CRITICAL ERROR in confirm_assignments:\n{stack_trace}")

        # 500 で落とさず、エラー内容をフロントエンドに 200 で返してダイアログ表示させる
        return JSONResponse(
            status_code=200,
            content={"success": False, "message": f"DB/サーバーエラー: {error_msg}"}
        )