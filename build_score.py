# -*- coding: utf-8 -*-
"""
PS5 游戏推荐游玩度评分 —— 最终流程
数据：/tmp 抓取的 2468c.com/ps5game 全 40 页，共 977 条
评分：两遍人工策展（score_ps5.TITLES + curate2.C），取最长匹配优先
输出：ps5_scored.json（排序后）
"""
import json, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
ITEMS = os.path.join(HERE, "ps5_items.json")
OUT = os.path.join(HERE, "ps5_scored.json")

import score_ps5 as S1
import curate2 as S2

# 合并两遍策展表
TABLE = {}
for src in (S1.TITLES, S2.C):
    for k, v in src.items():
        if not isinstance(k, str) or not k.strip():
            continue
        if not isinstance(v, (tuple, list)) or len(v) < 3:
            continue
        if not isinstance(v[0], (int, float)) or v[0] <= 0:
            continue
        TABLE[k.strip()] = (float(v[0]), str(v[1]), str(v[2]))

print("策展条目总数:", len(TABLE))


# 精确修正表：处理子串歧义导致的误配（键为标题中的唯一切片）
FIX = {
    "深海迷航：冰点之下": (7.5, "生存", "续作缩水，但海洋恐惧氛围仍在"),
    "Subnautica: Below Zero": (7.5, "生存", "续作缩水，氛围仍在"),
    "机械战警：暴戾都市 – 未尽之事": (7.0, "射击", "RoboCop 续作，枪手感扎实"),
    "机械战警：暴戾都市": (7.0, "射击", "RoboCop 开放世界射击"),
    "RoboCop": (7.0, "射击", "机械战警射击"),
    "模拟山羊3": (5.5, "搞笑", "模拟山羊，纯粹发泄用"),
    "模拟建筑：黄金版": (5.0, "模拟", "城市建设模拟，内容重复"),
    "城市模拟": (4.8, "模拟", "驾驶模拟器填充"),
    "都市": (5.0, "模拟", "都市题材偏模拟"),
    "死亡之屋": (7.5, "射击", "街机射击重制，操作上瘾"),
    "沙罗周期": (8.7, "RPG", "Sci-Fi 叙事实验"),
    "Nioh Collection": (8.5, "动作", "仁王合集"),
    "NiOH Collection": (8.5, "动作", "仁王合集"),
}


def score_one(item):
    title = item["title"]
    cats = item.get("cats", [])
    # 优先应用精确修正
    for k, v in FIX.items():
        if k in title:
            return v
    best = None
    # 长键优先；同长度时，优先在标题中出现位置更靠前者（更可能是主标题而非副标题）
    for k, v in TABLE.items():
        if k in title:
            key = (len(k), -title.index(k))
            if best is None or key > best[0]:
                best = (key, k, v)
    if best:
        _, k, (sc, g, note) = best
        if "PS VR" in cats and g != "VR":
            sc = round(sc - 0.5, 1)
            g = g + "/VR"
            note = "含 PS VR 支持（降低 0.5）；" + note
        return sc, g, note
    s, g, note = S1.pick_genre(title, cats)
    if "PS VR" in cats:
        s = round(s - 0.7, 1)
        return s, "VR", "PS VR 专属/加强，需持机才划算"
    return s, g, note


def tier_of(x):
    for lim, t in [(9.3, "S"), (8.8, "A+"), (8.2, "A"), (7.5, "B+"),
                   (7.0, "B"), (6.5, "C+"), (6.0, "C"), (5.0, "D")]:
        if x >= lim:
            return t
    return "E"


def main():
    items = json.load(open(ITEMS, encoding="utf-8"))
    for it in items:
        sc, g, note = score_one(it)
        it["score"] = sc
        it["genre"] = g
        it["note"] = note
        it["tier"] = tier_of(sc)
    items.sort(key=lambda x: (-x["score"], x["title"]))
    for i, it in enumerate(items, 1):
        it["rank"] = i
    json.dump(items, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    from collections import Counter
    order = ["S", "A+", "A", "B+", "B", "C+", "C", "D", "E"]
    print("\n总数:", len(items))
    print("分档分布:")
    c = Counter(i["tier"] for i in items)
    for t in order:
        if c.get(t):
            print(f"  {t:<3}{c[t]:>4}  {'█' * max(1, c[t] // 8)}")
    fb = [i for i in items if i["note"] == "资料有限，口碑待观察"]
    print(f"\n有策展依据: {len(items) - len(fb)}   类型兜底: {len(fb)}")
    print("\nTOP 50:")
    for it in items[:50]:
        print(f"{it['rank']:>3}. {it['score']:.1f} [{it['tier']:<2}] {it['genre']:<9} {it['title'][:44]}")


if __name__ == "__main__":
    main()