# -*- coding: utf-8 -*-
"""生成 PS5 游戏推荐度排行 HTML 报告"""
import json, os, html
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "ps5_scored.json")
OUT = os.path.join(HERE, "PS5游戏推荐游玩度排行.html")

TIER_META = {
    "S":  ("S", "时代级必玩",     "#dc2626", "#fee2e2", "#7f1d1d"),
    "A+": ("A+", "顶级佳作",       "#ea580c", "#ffedd5", "#7c2d12"),
    "A":  ("A",  "强烈推荐",       "#ca8a04", "#fef9c3", "#713f12"),
    "B+": ("B+", "值得一试",       "#16a34a", "#dcfce7", "#14532d"),
    "B":  ("B",  "可以玩玩",       "#0891b2", "#cffafe", "#164e63"),
    "C+": ("C+", "看品类偏好",     "#0284c7", "#e0f2fe", "#0c4a6e"),
    "C":  ("C",  "填充向",         "#64748b", "#f1f5f9", "#334155"),
    "D":  ("D",  "可跳过",         "#94a3b8", "#f8fafc", "#475569"),
    "E":  ("E",  "纯凑数",         "#a8a29e", "#fafaf9", "#57534e"),
}


def esc(s):
    return html.escape(str(s))


def main():
    data = json.load(open(SRC, encoding="utf-8"))
    total = len(data)

    # ---- 统计 ----
    tier_cnt = Counter(d["tier"] for d in data)
    genre_cnt = Counter(d["genre"].split("/")[0] for d in data)
    fb_cnt = sum(1 for d in data if d.get("note") == "资料有限，口碑待观察")
    curated = total - fb_cnt

    # ---- 各档位代表作品（取分数最高的前 N） ----
    tier_pick = {
        "S": 24, "A+": 18, "A": 16, "B+": 14,
    }

    rows = []
    for d in data:
        t = d["tier"]
        code, label, fg, bg, dark = TIER_META[t]
        rows.append(
            f'<tr data-tier="{t}" data-genre="{esc(d["genre"])}" data-score="{d["score"]}">'
            f'<td class="num">{d["rank"]}</td>'
            f'<td class="score"><span style="color:{fg};font-weight:700">{d["score"]:.1f}</span></td>'
            f'<td><span class="badge" style="background:{bg};color:{dark}">{code}</span></td>'
            f'<td class="title">{esc(d["title"])}</td>'
            f'<td class="genre">{esc(d["genre"])}</td>'
            f'<td class="note">{esc(d["note"])}</td>'
            f'<td class="tags">{"".join(f"<span class=tag>{esc(c)}</span>" for c in d["cats"])}</td>'
            f'<td class="url"><a href="{esc(d["url"])}" target="_blank" rel="noopener">详情</a></td>'
            f'</tr>')

    # ---- 概览卡片 ----
    cards = []
    for t in ["S", "A+", "A", "B+", "B", "C+", "C", "D", "E"]:
        if not tier_cnt.get(t):
            continue
        code, label, fg, bg, dark = TIER_META[t]
        n = tier_cnt[t]
        pct = n / total * 100
        rng = [d["score"] for d in data if d["tier"] == t]
        cards.append(
            f'<div class="tier-card" style="border-top:3px solid {fg}">'
            f'<div class="tc-head"><span class="tc-code" style="background:{bg};color:{dark}">{code}</span>'
            f'<span class="tc-label">{label}</span></div>'
            f'<div class="tc-num">{n}<span class="tc-unit">款</span></div>'
            f'<div class="tc-pct">{pct:.1f}% · {min(rng):.1f}-{max(rng):.1f} 分</div>'
            f'<div class="tc-bar"><span style="width:{pct*4:.1f}%;background:{fg}"></span></div>'
            f'</div>')

    # ---- TOP 榜单 ----
    def top_card(d, i):
        t = d["tier"]
        code, label, fg, bg, dark = TIER_META[t]
        return (
            f'<div class="top-card">'
            f'<div class="tc-rank" style="background:{fg}">{i}</div>'
            f'<div class="tc-main">'
            f'<div class="tc-name">{esc(d["title"].split(".")[0])}</div>'
            f'<div class="tc-meta"><span class="badge sm" style="background:{bg};color:{dark}">{code}</span>'
            f'<span class="tc-sc" style="color:{fg}">{d["score"]:.1f}</span>'
            f'<span class="tc-gen">{esc(d["genre"])}</span></div>'
            f'<div class="tc-note">{esc(d["note"])}</div>'
            f'</div></div>')

    top_blocks = []
    for t, n in tier_pick.items():
        picks = [d for d in data if d["tier"] == t][:n]
        if not picks:
            continue
        code, label, fg, bg, dark = TIER_META[t]
        items = "".join(top_card(d, i) for i, d in enumerate(picks, 1))
        top_blocks.append(
            f'<section class="tier-block">'
            f'<h3><span class="badge lg" style="background:{bg};color:{dark}">{code}</span>'
            f'{label} <span class="h3-sub">共 {tier_cnt[t]} 款，展示前 {len(picks)} 款</span></h3>'
            f'<div class="top-grid">{items}</div></section>')

    # ---- 品类分布 ----
    gen_rows = []
    for g, n in genre_cnt.most_common():
        best = max((d for d in data if d["genre"].split("/")[0] == g),
                   key=lambda x: x["score"])
        gen_rows.append(
            f'<tr><td class="genre">{esc(g)}</td><td class="num">{n}</td>'
            f'<td class="bar-cell"><span class="hbar" style="width:{n/genre_cnt.most_common(1)[0][1]*100:.0f}%"></span></td>'
            f'<td class="score sm"><b>{best["score"]:.1f}</b></td>'
            f'<td class="note sm">{esc(best["title"][:40])}</td></tr>')

    # ---- 筛选器 ----
    ORDER = ["S", "A+", "A", "B+", "B", "C+", "C", "D", "E"]
    opts = "".join(
        f'<option value="{t}">{TIER_META[t][0]} · {TIER_META[t][1]}（{tier_cnt[t]} 款）</option>'
        for t in ORDER if tier_cnt.get(t))
    genre_sorted = sorted(genre_cnt.items(), key=lambda x: (-genre_cnt[x[0]], x[0]))
    gopts = "".join(f'<option value="{esc(g)}">{esc(g)}（{n}）</option>'
                    for g, n in genre_sorted)

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PS5 游戏推荐游玩度排行 · {total} 款</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;
 background:#f6f7f9;color:#1f2328;line-height:1.6;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1280px;margin:0 auto;padding:32px 24px 64px}}
header{{background:linear-gradient(135deg,#1e3a8a,#4c1d95);color:#fff;
 padding:40px 32px;border-radius:16px;margin-bottom:32px}}
header h1{{font-size:30px;font-weight:700;margin-bottom:10px}}
header p{{opacity:.9;font-size:15px}}
header .kpis{{display:flex;gap:32px;margin-top:24px;flex-wrap:wrap}}
.kpi .n{{font-size:28px;font-weight:700;line-height:1.2}}
.kpi .l{{font-size:13px;opacity:.85}}
h2{{font-size:20px;margin:36px 0 16px;padding-left:12px;border-left:4px solid #4c1d95}}
.tier-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin-bottom:12px}}
.tier-card{{background:#fff;border-radius:12px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.tc-head{{display:flex;align-items:center;gap:8px;margin-bottom:8px}}
.tc-code{{display:inline-flex;align-items:center;justify-content:center;
 min-width:38px;height:26px;border-radius:6px;font-weight:700;font-size:13px}}
.tc-label{{font-size:13px;color:#57606a;font-weight:500}}
.tc-num{{font-size:26px;font-weight:700;line-height:1.2}}
.tc-unit{{font-size:13px;font-weight:400;color:#8b949e;margin-left:3px}}
.tc-pct{{font-size:12px;color:#8b949e;margin-bottom:8px}}
.tc-bar{{height:5px;background:#eaeef2;border-radius:3px;overflow:hidden}}
.tc-bar span{{display:block;height:100%;border-radius:3px}}
.tier-block{{margin-bottom:34px}}
.tier-block h3{{font-size:17px;margin-bottom:14px;display:flex;align-items:center;gap:10px}}
.badge{{display:inline-flex;align-items:center;justify-content:center;min-width:34px;
 height:24px;border-radius:6px;font-size:12px;font-weight:700;padding:0 8px}}
.badge.lg{{min-width:46px;height:30px;font-size:14px}}
.badge.sm{{min-width:30px;height:20px;font-size:11px}}
.h3-sub{{font-size:12px;color:#8b949e;font-weight:400}}
.top-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}}
.top-card{{background:#fff;border-radius:10px;padding:14px;display:flex;gap:12px;
 box-shadow:0 1px 3px rgba(0,0,0,.07);border:1px solid #e8ebef}}
.tc-rank{{width:28px;height:28px;flex:0 0 28px;border-radius:7px;color:#fff;
 display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px}}
.tc-main{{flex:1;min-width:0}}
.tc-name{{font-weight:600;font-size:14px;margin-bottom:5px;word-break:break-word}}
.tc-meta{{display:flex;align-items:center;gap:8px;margin-bottom:4px;flex-wrap:wrap}}
.tc-sc{{font-weight:700;font-size:13px}}
.tc-gen{{font-size:11px;color:#8b949e;background:#f0f2f5;padding:2px 7px;border-radius:4px}}
.tc-note{{font-size:12px;color:#57606a;line-height:1.5}}
.controls{{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:16px}}
.controls input,.controls select{{padding:9px 12px;border:1px solid #d5dae0;border-radius:8px;
 font-size:13px;font-family:inherit;background:#fff;color:#1f2328}}
.controls input{{flex:1;min-width:220px}}
.controls input:focus,.controls select:focus{{outline:2px solid #4c1d95;outline-offset:-1px;border-color:transparent}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;
 box-shadow:0 1px 3px rgba(0,0,0,.08)}}
thead th{{background:#f6f8fa;font-size:12px;font-weight:600;color:#57606a;
 text-align:left;padding:11px 10px;border-bottom:1px solid #e8ebef;white-space:nowrap}}
tbody td{{padding:10px;border-bottom:1px solid #f0f2f5;font-size:13px;vertical-align:top}}
tbody tr:hover{{background:#f6f8fa}}
.num{{color:#8b949e;text-align:right;width:52px;font-variant-numeric:tabular-nums}}
.score{{width:56px;text-align:right;font-variant-numeric:tabular-nums}}
.score.sm{{text-align:left}}
.title{{font-weight:500;max-width:330px;word-break:break-word}}
.genre{{color:#57606a;font-size:12px;white-space:nowrap}}
.note{{color:#57606a;font-size:12px;max-width:260px}}
.note.sm{{font-size:11px;max-width:280px}}
.tag{{display:inline-block;background:#f0f2f5;color:#57606a;font-size:10px;
 padding:1px 6px;border-radius:4px;margin-right:4px;white-space:nowrap}}
.tags{{white-space:nowrap}}
.url a{{color:#4c1d95;text-decoration:none;font-size:12px}}
.url a:hover{{text-decoration:underline}}
#count{{font-size:13px;color:#57606a;margin-left:auto}}
.gen-table{{max-width:760px}}
.bar-cell{{width:160px}}
.hbar{{display:block;height:7px;background:linear-gradient(90deg,#4c1d95,#1e3a8a);border-radius:4px}}
.note-box{{background:#fff8e6;border:1px solid #f5e0a8;border-radius:10px;padding:16px 20px;
 font-size:13px;color:#5c4a1a;margin-bottom:28px}}
.note-box b{{color:#7c2d12}}
footer{{margin-top:48px;padding-top:20px;border-top:1px solid #e8ebef;
 font-size:12px;color:#8b949e}}
@media(max-width:640px){{
 .wrap{{padding:16px 12px 40px}} header{{padding:24px 18px}} header h1{{font-size:22px}}
 .title,.note{{max-width:200px}}
 thead th:nth-child(6),tbody td:nth-child(6),thead th:nth-child(8),tbody td:nth-child(8){{display:none}}
}}
</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>PS5 游戏推荐游玩度排行</h1>
  <p>数据抓取自 2468c.com/ps5game 列表页（每次 40 页）· {total} 款游戏（含历史累积）· 按推荐游玩度打分排序</p>
  <div class="kpis">
    <div class="kpi"><div class="n">{total}</div><div class="l">游戏总数</div></div>
    <div class="kpi"><div class="n">{tier_cnt['S']}+{tier_cnt['A+']}</div><div class="l">S级+A级 必玩清单</div></div>
    <div class="kpi"><div class="n">{len(genre_cnt)}</div><div class="l">覆盖品类</div></div>
    <div class="kpi"><div class="n">{curated}</div><div class="l">逐款策展依据</div></div>
  </div>
</header>

<div class="note-box">
  <b>评分口径说明：</b>10 分制，衡量「值不值得投入时间」而非「画面好不好」。
  S/A 级为公认口碑佳作；D/E 级为年更填充、模拟器凑数或口碑明显翻车之作。
  含 PS VR 支持的游戏已在原分基础上扣 0.5。
  ⚠️ 本站为破解资源站，列表本身仅含版本信息（如 fpkg / exFAT / LZ4）；
  本排行评的是<b>游戏本身素质</b>，建议正版入手。
</div>

<h2>分档总览</h2>
<div class="tier-grid">{''.join(cards)}</div>

<h2>必玩清单（按档位）</h2>
{''.join(top_blocks)}

<h2>品类分布</h2>
<table class="gen-table">
<thead><tr><th>品类</th><th class="num">数量</th><th>占比</th><th class="score sm">该类最高分</th><th>代表作品</th></tr></thead>
<tbody>{''.join(gen_rows)}</tbody>
</table>

<h2>完整榜单（{total} 款）</h2>
<div class="controls">
  <input type="text" id="q" placeholder="搜索游戏名 / 品类 / 特点…">
  <select id="ft"><option value="">全部档位</option>{opts}</select>
  <select id="fg"><option value="">全部品类</option>{gopts}</select>
  <span id="count"></span>
</div>
<table>
<thead><tr>
  <th class="num">#</th><th class="score">分</th><th>档</th><th>游戏</th>
  <th>品类</th><th>推荐理由</th><th>来源标签</th><th>链接</th>
</tr></thead>
<tbody id="tb">{''.join(rows)}</tbody>
</table>

<footer>
  数据来源：2468c.com/ps5game（抓取时间 2026-10-07，共 40 页 {total} 条，去重后）<br>
  评分为基于公认口碑的人工策展结果，非官方评分，仅供选购参考。
</footer>

</div>
<script>
(function(){{
  var q=document.getElementById('q'),ft=document.getElementById('ft'),
      fg=document.getElementById('fg'),tb=document.getElementById('tb'),
      cnt=document.getElementById('count'),rows=[].slice.call(tb.rows);
  function upd(){{
    var s=q.value.trim().toLowerCase(),t=ft.value,g=fg.value,n=0;
    rows.forEach(function(r){{
      var ok=(!t||r.dataset.tier===t)&&
             (!g||r.dataset.genre.split('/')[0]===g)&&
             (!s||r.textContent.toLowerCase().indexOf(s)>-1);
      r.style.display=ok?'':'none'; if(ok)n++;
    }});
    cnt.textContent='显示 '+n+' / {total} 款';
  }}
  [q,ft,fg].forEach(function(e){{e.addEventListener('input',upd);}});
  upd();
}})();
</script>
</body>
</html>"""

    open(OUT, "w", encoding="utf-8").write(doc)
    print("written:", OUT)
    print("size:", os.path.getsize(OUT) // 1024, "KB")


if __name__ == "__main__":
    main()