# -*- coding: utf-8 -*-
"""01 比值回归研究 · 报告生成：读 data/*.csv → 生成 report.typ → 编译 PDF。

用法：python scripts/build_report.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_TYP = ROOT / "report.typ"
OUT_PDF = ROOT / "报告-比值型指标均值回归研究.pdf"

ev = pd.read_csv(DATA / "events.csv", parse_dates=["date"])
st = pd.read_csv(DATA / "world_stats.csv")


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def get(world, ym, side="高"):
    m = ev[(ev.world == world) & (ev.date.dt.strftime("%Y-%m") == ym) & (ev.side == side)]
    assert len(m) == 1, (world, ym)
    return m.iloc[0]


# ---------- 表 1：世界统计 ----------
rows_w = []
for _, r in st.iterrows():
    rows_w.append(
        f"[{r['world']}], [{r['years']}], [{int(r['n'])}（{int(r['n_hi'])}/{int(r['n_lo'])}）], "
        f"[{int(r['n_resolved'])}], [{int(r['half_hits'])}（{pct(r['half_rate'])}）], "
        f"[{r['median_half_month']:.0f} 个月], [{pct(r['full_rate'])}], [{pct(r['sim_half_mean'])}],"
    )
world_table = ("#table(columns: 8, stroke: 0.4pt + rgb(\"#cccccc\"), inset: 5pt,\n"
               "  table.header([世界],[样本],[事件（高/低）],[可判定],[半程命中],[中位用时],[完全回归],[随机基准]),\n  "
               + "\n  ".join(rows_w) + "\n)")

# ---------- 表 2：事件明细（附录） ----------
rows_e = []
for _, r in ev.sort_values(["world", "date"]).iterrows():
    if pd.isna(r["half_month"]):
        hm, status = "—", ("进行中" if r["truncated"] else "未命中")
    else:
        hm, status = f"{int(r['half_month'])}", "命中"
    rows_e.append(
        f"[{r['world']}], [{r['side']}], [{r['date']:%Y-%m}], [{r['level']:.2f}], [{r['median']:.2f}], "
        f"[{hm}], [{r['adverse'] * 100:+.0f}%], [{status}],"
    )
event_table = ("#text(size: 7.5pt)[#table(columns: 8, stroke: 0.3pt + rgb(\"#dddddd\"), inset: 3.5pt,\n"
               "  table.header([世界],[方向],[触发月],[触发值],[滚动中位],[半程回归（月）],[先恶化],[状态]),\n  "
               + "\n  ".join(rows_e) + "\n)]")

# ---------- 数据源表 ----------
data_table = ("#table(columns: 4, stroke: 0.4pt + rgb(\"#cccccc\"), inset: 5pt,\n"
              "  table.header([世界],[构建],[数据源],[样本期]),\n"
              "  [金油比·Brent], [金价 ÷ Brent 油价], [LBMA 月均（datahub）＋ FRED 日频→月均], [1987-05 – 2026-08],\n"
              "  [金油比·WTI], [金价 ÷ WTI 油价], [同上 ＋ FRED WTISPLC], [1971-01 – 2026-08（1971 前为布雷顿森林固定金价，截除）],\n"
              "  [金银比], [金价 ÷ 银价], [LBMA ＋ Yahoo SI=F（分段日线→月均）], [2000-08 – 2026-08],\n"
              "  [铜金比], [铜价 ÷ 金价], [FRED PCOPPUSDM（美元/吨，月频）], [1992-01 – 2026-07],\n"
              "  [信用利差], [Baa 收益率 − 10Y 国债], [FRED BAA10Y（HY OAS 因 ICE 下载限制未采用）], [1990-01 – 2026-09],\n"
              ")")

# ---------- 案例数字 ----------
c1 = get("金油比·Brent", "2020-03")
c2 = get("金油比·WTI", "2020-02")
c3 = get("金油比·Brent", "2014-12")
c4 = get("信用利差·Baa-10Y", "2008-03")
c5 = get("金银比", "2025-04")
pool = st[st.world.str.contains("全部")].iloc[0]


import datetime as dt
TODAY = dt.date.today().isoformat()
peak1 = c1.level * (1 + c1.adverse)
peak2 = c2.level * (1 + c2.adverse)

head = r'''#set document(title: "比值型估值指标的均值回归——跨体制样本研究")
#set page(paper: "a4", margin: (x: 2.1cm, y: 2.3cm), numbering: "1", number-align: center)
#set text(font: ("Microsoft YaHei", "SimSun"), size: 10pt, lang: "zh")
#set par(justify: true, leading: 0.72em)
#set heading(numbering: "1.1")
#show heading.where(level: 1): set text(size: 15pt)
#show heading.where(level: 2): set text(size: 12pt)

#align(center)[
  #text(size: 19pt, weight: "bold")[比值型估值指标的均值回归]
  #v(0.2em)
  #text(size: 11.5pt)[跨体制样本研究 ① · 55 个极端事件里，「极端之后会回归」是真的吗？]
  #v(0.4em)
  #text(size: 9.5pt, fill: rgb("#666666"))[定量建模训练场 · 延伸研究 #01 ｜ 2026-09 ｜ 数据 1986–2026]
]
#v(0.6em)'''

abstract = f'''#rect(width: 100%, inset: (x: 12pt, y: 10pt), radius: 3pt, fill: rgb("#faf6f5"), stroke: 0.6pt + rgb("#d9b8b3"))[
*摘要。* 本报告把「金油比 45」抽象为现象类——*比值型指标触及历史极端后，是否均值回归*——并在 5 个平行世界（金油比 ×2、金银比、铜金比、信用利差）中收集了 {int(pool.n)} 个独立事件。

- 半程回归率 *{pct(pool.half_rate)}*（{int(pool.half_hits)}/{int(pool.n_resolved)} 个可判定事件），随机游走基准 {pct(pool.sim_half_mean)}——*现象存在，但是中等强度的倾向，不是规律*；
- 命中的事件中位 *{pool.median_half_month:.0f} 个月*完成半程回归；完全回归到中位数的只有 {pct(pool.full_rate)}；
- *约三分之一（{int(pool.n_resolved) - int(pool.half_hits)}/{int(pool.n_resolved)}）并未回归*——失败多发生在「体制重定价」而非「暂时错价」的时刻；
- *回归之前的「先恶化」是主要成本*：2020 金油比先恶化 {c1.adverse:+.0%}（WTI 口径 {c2.adverse:+.0%}）才折返；信用利差 2008 年先恶化 {c4.adverse:+.0%}；
- 对 GOR 45 的校准：这类判断的行业基准率 ≈ *{pct(pool.half_rate)} 命中 · 中位 {pool.median_half_month:.0f} 个月 · 1/3 失败 · 尾部先恶化可达 +100~200%*——支持「观察区 + 二次确认 + 三三四分仓」，而不是「触发即重仓」。
]'''

sec1 = '''
= 背景与问题

这个研究回答一个具体问题：*比值型估值指标——金油比、金银比、铜金比、信用利差这类以「比值」或「点位」表达估值状态的指标——在触及历史极端之后，是否均值回归？*

动机来自前一个环节：金油比「45」的经验规律，56 年里只有两个宏观世界、两三个独立故事，统计上无法定论。路径①的思路是：把「金油比 45」抽象成 *「比值极端 → 回归」这一现象类*，去收集平行世界——让样本从 2 个故事，变成几十个独立事件。

本报告即该路径的第一步：5 个平行世界、55 个极端事件、统一口径、先定后验。'''

sec2 = f'''
= 方法与口径（先定后验）

所有定义在查看结果之前确定，并在脚本中冻结：

- *极值定义*：滚动 10 年窗口（120 个月，最少 60 个月）的第 95 / 第 5 百分位——用「滚动」而非「全样本」，避免前视偏差；
- *事件定义*：首次穿越（前一个月不极端）；同一方向的两次事件至少间隔 6 个月。**计数的是事件，不是月份**；
- *回归判据*（24 个月观察窗；触发时把当下的滚动中位数冻结为目标）：
  - 半程回归 = 朝中位数方向走完全程距离的 50%；完全回归 = 触及中位数；
- *先恶化*：回归之前，指标继续远离中位数的最大幅度（相对触发值）；
- *随机基准*：对每个世界自己的历史做 12 个月块自助抽样（1000 条 24 个月路径），回答「若未来只是该世界的随机重演，同样起点的半程回归概率是多少」。

{data_table}

> 口径备注：为保持跨世界可比，全部使用月度均值；各世界样本起点不同（受数据可得性限制）；「极端」是相对各世界自身分布而言，深层含义不完全一致（见讨论）。'''

sec3a = f'''
= 结果

== 总账：{int(pool.n)} 个事件

合并池共 *{int(pool.n)} 个事件*（极端高 {int(pool.n_hi)} / 极端低 {int(pool.n_lo)}），其中 {int(pool.n_resolved)} 个可判定，{int(pool["n_pending"])} 个仍在观察期。

- 半程回归：*{int(pool.half_hits)}/{int(pool.n_resolved)} = {pct(pool.half_rate)}*（随机基准 {pct(pool.sim_half_mean)}）
- 半程回归中位用时：*{pool.median_half_month:.0f} 个月*
- 完全回归（触及中位数）：{pct(pool.full_rate)}

{world_table}

== 五个平行世界'''

figs = '''
#figure(image("figures/fig1_worlds.png", width: 100%), caption: [五个平行世界的比值史与极端事件标记（红色下三角 = 极端高，蓝色上三角 = 极端低；纵轴为对数）。])

#figure(image("figures/fig2_outcomes.png", width: 100%), caption: [左：半程回归用时（月），x = 期内未回归，空心方块 = 仍在观察期；右：回归前最大反向偏移（%）——注意 2020 金油比·WTI 的 +222%。])

#figure(image("figures/fig3_vs_random.png", width: 100%), caption: [极端事件后的半程回归概率 vs 随机基准（块自助 1000 条路径）。])'''

cases = f'''
== 案例深读

*① 2020 金油比：先恶化 {c1.adverse:+.0%}（WTI 口径 {c2.adverse:+.0%}）才回归。*
Brent 口径 2020-03 触发（{c1.level:.1f}，滚动中位 {c1["median"]:.1f}）；之后比值继续上冲约 {peak1:.0f}，直到第 {int(c1.half_month)} 个月才完成半程回归。WTI 口径同一事件更极端：先恶化到约 {peak2:.0f}，第 {int(c2.half_month)} 个月回归。*如果按信号重仓、又没有承受这段先恶化，大概率死在黎明前。*

*② 2014-12 金油比：24 个月内未回归（失败样本）。*
比值先恶化 {c3.adverse:+.0%}。这不是「暂时错价」，而是油价从 100 美元跌向 30 美元的*体制重定价*——「回到旧中位数」的前提消失了。

*③ 信用利差 2008-03：危机里，「极端」可以极上加极。*
雷曼倒闭前约半年触发，先恶化 {c4.adverse:+.0%}，21 个月后才半程回归。

*④ 金银比 2025-04：{int(c5.half_month)} 个月完成半程回归（最快命中）。*
白银单边行情把比值迅速拉回——同一现象类中的「顺利版本」。'''

disc = f'''
= 讨论与边界

== 现象是真实的，但只是「倾向」

半程回归 {pct(pool.half_rate)} vs 随机基准 {pct(pool.sim_half_mean)}（+{(pool.half_rate - pool.sim_half_mean) * 100:.0f}pp）。它不是噪声——但也不是规律。*「极端之后」不保证「回归」；它只是把回归的概率抬高了一档。*

== 失败的模式：体制重定价

失败案例（2014-12 金油比、2000-04 信用利差、2005-02 铜金比、2017-12 金银比）多发生在价格进入新体制的时刻。这是路径②（机制论证）要正面处理的问题：*先判断「暂时错价」还是「体制重定价」，再决定用不用回归逻辑。*

== 成本在「先恶化」，不在「不回归」

中位事件的先恶化约 {pool.median_adverse:+.0%}——多数回归来得不痛不痒；但尾部可达 {c2.adverse:+.0%}（2020 金油比·WTI）。*对交易的含义：分仓、确认、缓冲，全部围绕这段「先恶化」来设计*——这正是「三三四分仓 + 二次确认」的数量依据。

== 对 GOR 45 的校准（本研究的核心产出）

把行业基准率带回工作台：*这类信号 ≈ {pct(pool.half_rate)} 命中 / 中位 {pool.median_half_month:.0f} 个月 / 1/3 失败 / 尾部先恶化 2–3 倍*。注意：本研究的「极端」= 滚动 P95，比固定的 45 宽松得多——它校准的是*先验*，不是*验证* 45。45 的专属证据仍然只有那两个故事。

== 四个诚实条款

1. 判据敏感：半程回归 {pct(pool.half_rate)} vs 完全回归 {pct(pool.full_rate)}——任何「回归率」必须附带判据定义；
2. 平行世界共享共同因子（2020 年多世界同时极端）——55 个事件的「独立世界数」小于 55；
3. 数据断点：各世界起点、频率、来源不同（白银自 2000、铜自 1992、信用自 1990）；
4. 待观察事件 {int(pool["n_pending"])} 个（2024–2025 触发）将在未来 1–2 年自然结算，届时可复算。'''

repro = f'''
= 复现

- 数据：`python scripts/fetch_data.py`（免密钥；金 / 油复用 L1 数据）
- 分析：`python scripts/analyze.py` → `data/events.csv`、`data/world_stats.csv`、`figures/*.png`
- 本报告：`python scripts/build_report.py`（本 PDF 由脚本自动生成于 {TODAY}）

= 附录 A · 事件明细

{event_table}

#v(1em)
#align(center)[#text(size: 8.5pt, fill: rgb("#888888"))[定量建模训练场 · 延伸研究 #01 ｜ 数据：FRED / datahub.io / Yahoo ｜ build_report.py 自动生成]]'''

src = "\n\n".join([head, abstract, sec1, sec2, sec3a, figs, cases, disc, repro])
OUT_TYP.write_text(src, encoding="utf-8")
print("report.typ 已生成：", len(src), "字符")

import typst  # noqa: E402
typst.compile(str(OUT_TYP), output=str(OUT_PDF))
print("PDF 已生成：", OUT_PDF.name, OUT_PDF.stat().st_size, "bytes")
