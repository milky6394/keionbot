from collections import defaultdict
import random

def calculate_band_assignments(event_slots, bands, band_members, all_wishes):
    """
    バンド間の練習コマ枠自動割り当て計算ロジック（修正版）
    """

    # 1. 部員ごとの希望データを参照しやすい辞書形式に変換 { (username, slot_id): wish_level }
    wish_dict = {}
    for w in all_wishes:
        # slot_id や wish_level を数値型に安全変換
        try:
            slot_id = int(w["slot_id"])
            level = int(w.get("wish_level", 0))
            username = str(w["username"]).strip()
            wish_dict[(username, slot_id)] = level
        except (ValueError, TypeError, KeyError):
            continue

    # 2. バンドごとに所属メンバーのリストを作成
    band_member_map = defaultdict(list)
    for bm in band_members:
        try:
            band_id = int(bm["band_id"])
            username = str(bm["username"]).strip()
            band_member_map[band_id].append(username)
        except (ValueError, TypeError, KeyError):
            continue

    # 3. 各コマ・各バンドにおける「割り当て可能性」と「スコア」を判定
    slot_candidates = defaultdict(list)

    for slot in event_slots:
        try:
            sid = int(slot["id"])
        except (ValueError, TypeError):
            continue

        for band in bands:
            try:
                bid = int(band["id"])
            except (ValueError, TypeError):
                continue

            members = band_member_map.get(bid, [])

            if not members:
                print(f"DEBUG: バンドID {bid} ({band.get('band_name')}) にメンバーが紐付いていません")
                continue  # メンバーがいないバンドはスキップ

            # メンバー全員の回答を確認
            is_available = True
            total_score = 0

            for username in members:
                # 未回答または0(NG)の場合は即不可
                level = wish_dict.get((username, sid), 0)
                if level <= 0:  # 0以下(NG/未回答)はNG
                    is_available = False
                    print(f"DEBUG: NG判定 -> ユーザー: {username}, コマ: {sid}, レベル: {level}")
                    break
                total_score += level

            # 1人でもNGがいなければ候補に追加
            if is_available:
                slot_candidates[sid].append({
                    "band_id": bid,
                    "score": total_score
                })

    # 4. コマ枠の割り当て計算
    assigned_results = []
    band_assigned_counts = {int(b["id"]): 0 for b in bands if "id" in b}

    # コマ枠を順に処理
    sorted_slots = sorted(event_slots, key=lambda s: len(slot_candidates[int(s["id"])]))

    for slot in sorted_slots:
        sid = int(slot["id"])
        candidates = slot_candidates.get(sid, [])

        if not candidates:
            print(f"DEBUG: コマID {sid} に割り当て可能なバンドがありませんでした")
            continue  # どのバンドも練習できないコマ枠

        # 割り当て数が少ない ＞ スコアが高い ＞ ランダム
        candidates.sort(key=lambda c: (
            band_assigned_counts.get(c["band_id"], 0),
            -c["score"],
            random.random()
        ))

        # 最適なバンドを1つ確定
        selected_candidate = candidates[0]
        selected_band_id = selected_candidate["band_id"]

        # バンド名を取得
        band_name = ""
        for b in bands:
            if int(b.get("id", -1)) == selected_band_id:
                band_name = b.get("band_name", "")
                break

        assigned_results.append({
            "slot_id": sid,
            "band_id": selected_band_id,
            "band_name": band_name
        })

        # 割り当て状態の更新
        band_assigned_counts[selected_band_id] = band_assigned_counts.get(selected_band_id, 0) + 1

    return assigned_results