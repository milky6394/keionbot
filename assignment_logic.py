from collections import defaultdict
import random

def calculate_band_assignments(event_slots, bands, band_members, all_wishes):
    """
    バンド間の練習コマ枠自動割り当て計算ロジック
    
    :param event_slots: イベント内の全コマ枠リスト [{'id': 1, 'day_of_week': 1, 'slot_number': 1}, ...]
    :param bands: バンド一覧 [{'id': 10, 'band_name': 'バンドA'}, ...]
    :param band_members: バンドメンバー対応表 [{'band_id': 10, 'username': 'alice'}, ...]
    :param all_wishes: 全部員の希望データ [{'username': 'alice', 'slot_id': 1, 'wish_level': 2}, ...]
    :return: 割り当て結果リスト [{'slot_id': 1, 'band_id': 10, 'band_name': 'バンドA'}, ...]
    """

    # 1. 部員ごとの希望データを参照しやすい辞書形式に変換 { (username, slot_id): wish_level }
    wish_dict = {}
    for w in all_wishes:
        wish_dict[(w["username"], w["slot_id"])] = w.get("wish_level", 0)

    # 2. バンドごとに所属メンバーのリストを作成
    band_member_map = defaultdict(list)
    for bm in band_members:
        band_member_map[bm["band_id"]].append(bm["username"])

    # 3. 各コマ・各バンドにおける「割り当て可能性」と「スコア」を判定
    # slot_candidates[slot_id] = [ {'band_id': 10, 'score': 12}, ... ]
    slot_candidates = defaultdict(list)

    for slot in event_slots:
        sid = slot["id"]

        for band in bands:
            bid = band["id"]
            members = band_member_map.get(bid, [])

            if not members:
                continue  # メンバーがいないバンドはスキップ

            # メンバー全員の回答を確認
            is_available = True
            total_score = 0

            for username in members:
                # 未回答または0(NG)の場合は即不可
                level = wish_dict.get((username, sid), 0)
                if level == 0:
                    is_available = False
                    break
                total_score += level

            # 1人でもNGがいなければ候補に追加
            if is_available:
                slot_candidates[sid].append({
                    "band_id": bid,
                    "score": total_score
                })

    # 4. コマ枠の割り当て計算（均等分配 ＆ 重複防止）
    assigned_results = []
    band_assigned_counts = {b["id"]: 0 for b in bands}  # バンドごとの確定コマ数カウント
    used_slots = set()                                 # 割り当て済みコマIDの集合

    # コマ枠を順に処理（希望バンド数が少ない「競合度の高いコマ」から優先処理する工夫）
    sorted_slots = sorted(event_slots, key=lambda s: len(slot_candidates[s["id"]]))

    for slot in sorted_slots:
        sid = slot["id"]
        candidates = slot_candidates.get(sid, [])

        if not candidates:
            continue  # どのバンドも練習できないコマ枠

        # 候補バンドの中から「現在割り当て数が最も少ないバンド」を優先選出
        # 同数の場合はスコア（「ありがたい」の多さ）が高い方を優先
        candidates.sort(key=lambda c: (
            band_assigned_counts[c["band_id"]],  # 第一条件: 割り当てコマ数の少なさ（昇順）
            -c["score"],                         # 第二条件: 希望度スコアの高さ（降順）
            random.random()                      # 第三条件: 同条件ならランダム
        ))

        # 最適なバンドを1つ確定
        selected_candidate = candidates[0]
        selected_band_id = selected_candidate["band_id"]

        # バンド名を取得
        band_name = next((b["band_name"] for b in bands if b["id"] == selected_band_id), "")

        assigned_results.append({
            "slot_id": sid,
            "band_id": selected_band_id,
            "band_name": band_name
        })

        # 割り当て状態の更新
        band_assigned_counts[selected_band_id] += 1
        used_slots.add(sid)

    return assigned_results