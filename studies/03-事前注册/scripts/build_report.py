# -*- coding: utf-8 -*-
"""03 事前注册 · 报告生成：读 data/*.csv → report.typ → 编译 PDF。"""
from pathlib import Path
import datetime as dt

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_TYP = ROOT / "report.typ"
OUT_PDF = ROOT / "报告-事前注册-先写规则再看数据.pdf"
TODAY = dt.date.today().isoformat()

d1 = pd.read_csv(DATA / "demo1_selection.csv")
wf = pd.read_csv(DATA / "demo2_walkforward.csv")
sp = pd.read_csv(DATA / "sparsity.csv")

import numpy as np  # noqa: E402

ins = d1["ins_t"].to_numpy()
oos = d1["oos_t"].to_numpy()
fin = np.isfinite(oos)
RES = dict(
    n=len(ins), ins_mean=float(ins.mean()), p_ins=float((ins > 2).mean()),
    oos_mean=float(oos[fin].mean()), p_oos=float((oos[fin] > 2).mean()),
    oos_neg=float((oos[fin] < 0).mean()), oos_missing=float(1 - fin.mean()),
)

ok = wf[wf["thr"].notna()]
w24 = wf[wf["year"] == 2024].iloc[0]

rows_wf = []
for _, r in wf.iterrows():
    if pd.isna(r["thr"]):
        rows_wf.append(f"[{int(r['year'])}], [—], [样本内无从选择], [—], [—], [{int(r['f45_events'])}],")
    else:
        fx = "—" if pd.isna(r["fwd_excess"]) else f"{r['fwd_excess']:+.0%}"
        rows_wf.append(
            f"[{int(r['year'])}], [{int(r['thr'])}], [{r['ins_excess']:+.0%}（n={int(r['ins_n'])}）], "
            f"[{int(r['fwd_events'])}], [{fx}], [{int(r['f45_events'])}],")
wf_table = ("#text(size: 8.5pt)[#table(columns: 6, stroke: 0.3pt + rgb(\"#dddddd\"), inset: 3.5pt,\n"
            "  table.header([发现年份],[选中阈值],[样本内超额],[前向 5 年触发（次）],[前向超额],[同期固定 45 触发（次）]),\n  "
            + "\n  ".join(rows_wf) + "\n)]")

rows_sp = [f"[{int(r['thr'])}], [{int(r['months'])}], [{int(r['crossings'])}]," for _, r in sp.iterrows()]
sp_table = ("#table(columns: 3, stroke: 0.4pt + rgb(\"#cccccc\"), inset: 5pt,\n"
            "  table.header([阈值],[≥ 阈值的月份数],[首次穿越（独立事件）]),\n  "
            + "\n  ".join(rows_sp) + "\n)")

tools_table = ("#table(columns: 3, stroke: 0.4pt + rgb(\"#cccccc\"), inset: 5pt,\n"
               "  table.header([工具],[作用],[落地物]),\n"
               "  [前向注册卡], [事前写下预测与判据，commit 即冻结；到期只读对账], [`cards/注册卡-2026-09-17-GOR.md`、`templates/注册卡模板.md`],\n"
               "  [前向检验], [把「未来」当唯一干净的样本外：触发先写剧本，到期结算], [对账日自动写入卡内（6 / 12 个月）],\n"
               "  [尝试台账], [记录每一个试过的口径；报告必须披露总行数], [`cards/台账.md`（已回填 8 行）],\n"
               "  [规则版本化], [改规则先 commit「愿望版」再回测；git 即签署机制], [沿用本仓库 git 流程],\n"
               ")")


head = r'''#set document(title: "事前注册——先写规则，再看数据")
#set page(paper: "a4", margin: (x: 2.1cm, y: 2.3cm), numbering: "1", number-align: center)
#set text(font: ("Microsoft YaHei", "SimSun"), size: 10pt, lang: "zh")
#set par(justify: true, leading: 0.72em)
#set heading(numbering: "1.1")
#show heading.where(level: 1): set text(size: 15pt)
#show heading.where(level: 2): set text(size: 12pt)

#align(center)[
  #text(size: 19pt, weight: "bold")[事前注册 —— 先写规则，再看数据]
  #v(0.2em)
  #text(size: 11.5pt)[跨体制样本研究 ③ · 三个敌人、两场演示、四件套工具]
  #v(0.4em)
  #text(size: 9.5pt, fill: rgb("#666666"))[定量建模训练场 · 延伸研究 #03 ｜ 2026-09 ｜ 数据 1987–2026]
]
#v(0.6em)'''

abstract = f'''#rect(width: 100%, inset: (x: 12pt, y: 10pt), radius: 3pt, fill: rgb("#faf6f5"), stroke: 0.6pt + rgb("#d9b8b3"))[
*摘要。* ①② 教会我们"怎么研究"；③ 处理最后一环：*研究者自己*——挑数据、事后编故事、只报赢的。

- *演示一（随机世界）*：在 {RES['n']} 个**完全无信号**的世界里扫描 16 档阈值——*{RES['p_ins']:.0%} 的「发现」能过 t>2*；同一规则样本外 t 均值归零（{RES['oos_mean']:+.2f}），*{RES['oos_neg']:.0%} 变负、{RES['oos_missing']:.0%} 连触发机会都没有*；
- *演示二（真实数据）*：同一套流程，不同年代"发现"不同阈值（*30 → 32 → 46*，贴着当时历史水位）；样本内 **+{w24['ins_excess']:.0%}** 的"最优"规则（2024 年选出的阈值 46），前向只剩 *+{w24['fwd_excess']:.0%}*；前向 5 年大多只触发 0–1 次；
- *连我们自己都无法免疫*：本研究开发中抓住并修正了一次前视偏差——这正是 ③ 存在的理由；
- *四件套工具 + 首张实卡*：注册卡（已生成，预测栏留白待签）· 前向检验 · 尝试台账（已回填 8 行）· 规则版本化（commit 即签署）。
]'''

sec1 = '''
= 背景：三个敌人

① ② 把"研究怎么做"讲清楚了，但工具会被使用者的手污染。三个敌人：

- *挑数据（data snooping）*：试到满意为止；
- *事后编故事（HARKing）*：先看到结果，再"推导"假说；
- *选择性报告*：只报赢的。

而且这不是别人家的病：研究 02 的筛选器 v1.0 把 2014-12 误报为绿（回放修正）；研究 03 的演示初版把"样本内触发"的前向收益完成在发现时点之后（前视，自查修正）。*两次都是制度抓出来的——没有制度，它们会安静地留在结论里。*

路径③ 的四件套：注册卡 / 前向检验 / 尝试台账 / 规则版本化。'''

sec2 = f'''
= 演示一：随机世界里的「圣杯」

在 {RES['n']} 个**完全没有信号**的随机世界里，模拟同一套研究流程：扫描 16 档阈值，挑表现最好的那一档（t 检验 vs 基准；样本内触发的未来收益也必须在样本内"结算"）。

- 样本内"最优阈值"的 t 均值 = *{RES['ins_mean']:.2f}*，*P(t>2) = {RES['p_ins']:.0%}*——四成的世界里，"研究"能找到"统计显著"的规律，而那里本来什么都没有；
- 把**同一个规则**放到样本外：t 均值 = *{RES['oos_mean']:+.2f}*；*{RES['oos_neg']:.0%} 变负*；*{RES['oos_missing']:.0%} 连触发机会都没有*；P(t>2) 降到 {RES['p_oos']:.0%}。

*一句话：试得足够多，"发现"是必然的，"复现"才是意外。*

#figure(image("figures/fig1_selection.png", width: 100%), caption: [演示一 · 左：样本内"最优阈值"的 t 分布 vs 同一规则样本外的 t 分布；右：P(t>2) 对比。])'''

sec3 = f'''
= 演示二：真实数据的「发现 → 前向」

用 GOR·Brent（1987–2026）复盘：每个发现年份只用当时可见的数据（且触发须在前 12 个月内结算）挑选最优阈值，再看它之后 5 年的命运。

- **阈值随时代漂移**：*30（2000s）→ 32（2018）→ 46（2022 后）*——同一套流程，不同年代"发现"不同规则。你事前能注册的规则，永远贴着当时历史的水位；55 / 60 这些"事后最亮"的阈值，在 2026 年之前的世界里**根本无法被"发现"**；
- 样本内超额看起来香（+26% ~ +126%），但前向 5 年**大多只触发 0–1 次**——"圣杯"在样本外连开火的机会都稀缺；
- 最刺眼的一组：2024 年选出的最优规则（阈值 46）——样本内 *+{w24['ins_excess']:.0%}*，前向 *+{w24['fwd_excess']:.0%}*。

#figure(image("figures/fig2_walkforward.png", width: 100%), caption: [演示二 · 左：每次"研究"挑出的阈值（红点）与固定 45（蓝线）；右：前向 5 年触发次数——大多数年份"圣杯"开不了火。])

#figure(image("figures/fig3_sparsity.png", width: 100%), caption: [阈值稀疏度阶梯：月份数随阈值迅速衰减（27 → 6）；独立事件从头到尾都只有个位数。])

{wf_table}

== 阈值稀疏度（全历史）

{sp_table}'''

sec4 = f'''
= 四件套工具与首张实卡

{tools_table}

#rect(width: 100%, inset: (x: 12pt, y: 10pt), radius: 3pt, fill: rgb("#f0f6ff"), stroke: 0.6pt + rgb("#b8c8dd"))[
*首张实卡（{TODAY}，已生成待签）* —— `cards/注册卡-{TODAY}-GOR.md`

- 状态：GOR **48.4**（历史 97 分位）｜ 油腿主导（金 +27% / 油 +29%）｜ VIX **15.2**（平静）｜ 油分位 89% ｜ 筛选器 **1/3（红）**；
- 待你填写：P1（12 个月后 GOR 区间与把握）· P2（若回落，主因）· P3（对"油回归"逻辑：参与 / 观察 / 放弃）；
- 签署方式：填完 `git commit` 即冻结 ｜ 对账日：2027-03-17 与 2027-09-17。
]'''

sec5 = f'''
= 局限

1. 演示一为教学模拟（世界参数化：随机游走 + 漂移），量级可参照、绝对值勿外推；
2. 演示二的阈值网格（30–60、步长 2）本身是一组口径选择——已记入台账；
3. 注册卡的有效性依赖"真的到期对账"——制度 > 意志力；
4. 前向检验慢：干净的样本外数据以"年"为单位积累——这是它的优点，也是它的成本。

= 复现

- 演示分析：`python scripts/analyze.py` → data/*.csv、figures/*.png
- 注册卡：`python scripts/make_card.py` → cards/注册卡-{TODAY}-GOR.md
- 本报告：`python scripts/build_report.py`（自动生成于 {TODAY}）

#v(1em)
#align(center)[#text(size: 8.5pt, fill: rgb("#888888"))[定量建模训练场 · 延伸研究 #03 ｜ build_report.py 自动生成]]'''

src = "\n\n".join([head, abstract, sec1, sec2, sec3, sec4, sec5])
OUT_TYP.write_text(src, encoding="utf-8")
print("report.typ 已生成：", len(src), "字符")

import typst  # noqa: E402
typst.compile(str(OUT_TYP), output=str(OUT_PDF))
print("PDF 已生成：", OUT_PDF.name, OUT_PDF.stat().st_size, "bytes")
