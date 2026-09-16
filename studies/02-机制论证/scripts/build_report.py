# -*- coding: utf-8 -*-
"""02 机制论证 · 报告生成：读 data/*.csv → report.typ → 编译 PDF。"""
from pathlib import Path
import datetime as dt

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_TYP = ROOT / "report.typ"
OUT_PDF = ROOT / "报告-机制论证-暂时错价还是体制重定价.pdf"

t1 = pd.read_csv(DATA / "t1_legs.csv")
t2 = pd.read_csv(DATA / "t2_vix.csv")
scr = pd.read_csv(DATA / "screener.csv")
t3r = pd.read_csv(DATA / "t3_results.csv")
TODAY = dt.date.today().isoformat()

GI, GA = 1879, 4411  # 模型外推 / 实际金价（2026-08，见 analyze.py 输出）


def gs(df, col, val):
    sub = df[df[col] == val]
    res = sub[sub["status"] != "进行中"]
    return len(sub), len(res), (float((res["status"] == "命中").mean()) if len(res) else float("nan"))


n_o, r_o, h_o = gs(t1, "leg", "油腿主导")
n_g, r_g, h_g = gs(t1, "leg", "金腿主导")
n_p, r_p, h_p = gs(t2, "shock", "恐慌")
n_c, r_c, h_c = gs(t2, "shock", "平静")
pre = t3r.iloc[0]
post = t3r.iloc[1]
gap = float(t3r.iloc[2]["beta"])
cur = scr[scr["case"].str.contains("2026-08")].iloc[0]

chain_table = ("#table(columns: 4, stroke: 0.4pt + rgb(\"#cccccc\"), inset: 5pt,\n"
               "  table.header([链],[逻辑],[观测指标],[失效条件]),\n"
               "  [A · 供给予衡], [油价低于边际成本 → 减产 / 资本开支收缩 → 供给收缩 → 价格回归], [页岩盈亏线、OPEC 财政平衡价、钻机数、库存], [需求永久性破坏；卡特尔破裂；替代加速],\n"
               "  [B · 冲击-修复], [极端读数 = 需求崩塌事件 → 事件结束 → 修复（2020 型）], [VIX、信用利差、政策响应速度], [事件不结束；政策失效；需求疤痕化],\n"
               "  [C · 金融化], [极低油价 → 期货超级升水 → 囤油套利 → 现货抽紧], [期限结构、库存、CFTC 持仓], [曲线不升水；利率与仓储成本高企],\n"
               "  [D · 货币腿], [金价重估（信用 / 赤字）→ GOR 被动抬高 → 与油无关], [实际利率残差（重估缺口）], [—— 不是油机制，对油无预测力],\n"
               ")")

rows_scr = []
for _, r in scr.iterrows():
    rows_scr.append(
        f"[{r['case']}], [金 {r['d_gold']:+.0%} / 油 {r['d_oil']:+.0%} → {'油腿 ✓' if r['s1'] else '金腿 ✗'}], "
        f"[VIX {r['vix']:.1f}（阈 {r['vix_thr']:.1f}）{'✓' if r['s2'] else '✗'}], "
        f"[{r['oil_pctl']:.0%} {'✓' if r['s3'] else '✗'}], [{int(r['npass'])}/3], [{r['verdict']}],"
    )
scr_table = ("#text(size: 8.5pt)[#table(columns: 6, stroke: 0.3pt + rgb(\"#dddddd\"), inset: 3.5pt,\n"
             "  table.header([案例],[拆腿],[恐慌签名],[油分位],[通过],[结论]),\n  "
             + "\n  ".join(rows_scr) + "\n)]")


head = r'''#set document(title: "机制论证——暂时错价还是体制重定价")
#set page(paper: "a4", margin: (x: 2.1cm, y: 2.3cm), numbering: "1", number-align: center)
#set text(font: ("Microsoft YaHei", "SimSun"), size: 10pt, lang: "zh")
#set par(justify: true, leading: 0.72em)
#set heading(numbering: "1.1")
#show heading.where(level: 1): set text(size: 15pt)
#show heading.where(level: 2): set text(size: 12pt)

#align(center)[
  #text(size: 19pt, weight: "bold")[机制论证 ——「暂时错价」还是「体制重定价」？]
  #v(0.2em)
  #text(size: 11.5pt)[跨体制样本研究 ② · 用因果链与恐慌签名，给「回归逻辑」装一个筛选器]
  #v(0.4em)
  #text(size: 9.5pt, fill: rgb("#666666"))[定量建模训练场 · 延伸研究 #02 ｜ 2026-09 ｜ 数据 1971–2026]
]
#v(0.6em)'''

abstract = f'''#rect(width: 100%, inset: (x: 12pt, y: 10pt), radius: 3pt, fill: rgb("#faf6f5"), stroke: 0.6pt + rgb("#d9b8b3"))[
*摘要。* ① 留下一个谜：55 个极端事件里约 1/3 没有回归。本报告用机制把这一刀切开——那 1/3 不是运气，它有可识别的「体质」。

- *恐惧是分水岭*：触发时带「恐慌签名」的事件半程回归率 *{h_p:.1%}*（n={r_p}），平静组只有 *{h_c:.1%}*（n={r_c}）——后者 ≈ 随机基准 52%。① 的失败几乎全部来自平静组；
- *拆腿分类预测不了结局*（油腿 {h_o:.0%} vs 金腿 {h_g:.0%}）——它回答「哪个机制在场」，不回答「会不会兑现」；
- *黄金重估*：金价对实际利率的月度敏感性没变（β {pre["beta"]:+.2f} → {post["beta"]:+.2f}），但水位被抬高 *+{gap:.0%}*——「金腿」背后是一个与油无关、仍在持续的机制；
- *机制筛选器 v1.0 → 回放暴露误报 → v1.1（恐慌签名设为一票必要条件）→ 回放全部对齐*；当前 GOR（2026-08）通过 1/3 → *红：不是「油被错杀」*。
]'''

sec1 = '''
= 背景与问题

① 的结论：比值极端后 {hold} 半程回归——一个「中等强度」的倾向。剩下的 1/3 失败不是随机噪声：它们集中在「体制重定价」时刻（2014 年油崩、2000 年信用、2005 年铜）。

问题：*能不能在事前把「暂时错价」和「体制重定价」分开？*

路径② 的答案：不靠价格本身，靠*机制*——写下因果链、给每一环配可观测指标、检验中间变量、筛掉「机制不在场」的读数。'''.replace("{hold}", "64.7%")

sec2 = f'''
= 因果链：把「为什么」写出来

对「GOR 高读数 → 油会涨」这个推断，可能存在四种机制（下表）。*机制论证的纪律：每条链都要有可观测指标，并给出证伪条件*——「如果机制对，我应该看到 X（而我现在还没看到）」。

{chain_table}

本报告只检验能拿到免密钥数据的三个环节：拆腿（哪条腿在场）、恐慌签名（链 B 的入口）、黄金重估（链 D 的证据）。'''

sec3 = f'''
= 检验一：拆腿分类（语义有用，预测无用）

用每个事件触发前 12 个月的腿部贡献分类（图 1）：油腿主导 {n_o} 个、半程回归 {h_o:.1%}；金腿主导 {n_g} 个（可判定 {r_g}）、半程回归 {h_g:.1%}。

*结论：拆腿是有用的语义工具*（它告诉你此刻在场的是供给予衡还是货币重估），*但不是预测工具*——两者差异（{h_o:.0%} vs {h_g:.0%}）在 n=7~19 的样本量内无统计意义。真正的分水岭在下一节。

#figure(image("figures/fig1_legs.png", width: 100%), caption: [T1 · 左：每个金油比事件的腿部贡献（12 个月）与结局；右：油腿 vs 金腿的半程回归率。])

= 检验二：恐慌签名（分水岭）

把每个事件触发月的 VIX 与它自己的滚动 10 年 P80 比较：≥ 判为「恐慌」（图 2 右区）。

- 恐慌组：{n_p} 个事件，可判定 {r_p}，半程回归 *{h_p:.1%}*；
- 平静组：{n_c} 个事件，可判定 {r_c}，半程回归 *{h_c:.1%}*（≈ 随机基准 52%）；
- 1990 年前 5 个事件无 VIX 数据，未计入。

*读数：极端读数「有救」的前提，是背后有一个会结束的恐慌事件（链 B）；平静时期的高读数，大概率是重定价或漂移——在那种时刻用回归逻辑，等于抛硬币。*

#figure(image("figures/fig2_vix.png", width: 100%), caption: [T2 · 左：事件触发时 VIX 的滚动 10 年分位（红=恐慌，蓝=平静；x=未命中，空心=进行中）；右：两组半程回归率。])

= 检验三：黄金重估（「金腿」的机制）

金价对 10Y 实际利率的月度回归：2003–2019 β = {pre["beta"]:+.2f}（se {pre["se"]:.2f}，R² {pre["r2"]:.2f}）；2020–2026 β = {post["beta"]:+.2f}（se {post["se"]:.2f}，R² {post["r2"]:.2f}）。

敏感性没变，但把 2003–2019 的模型向 2020 年后外推：模型说 2026-08 金价应为 {GI} 美元，实际 {GA} 美元——*重估缺口 +{gap:.0%}*。这不是「油便宜」，是「货币的水位在换」。链 D 对「油会涨」没有任何预测力；它只提醒你：*GOR 的高读数可以完全由分子制造。*

#figure(image("figures/fig3_gold.png", width: 100%), caption: [T3 · 左：金价 vs 实际利率的两个时代（β 几乎没变）；右：「重估缺口」——实际 vs 旧机制外推。])'''

sec4 = f'''
= 机制筛选器：v1.0 → 回放 → v1.1

三屏（全部免密钥数据、事前可算）：

1. *拆腿*：油腿主导？（金腿 → 直接退出「油回归」逻辑）
2. *恐慌签名*：VIX ≥ 滚动 10 年 P80？（链 B 的入口）
3. *油迫近*：油价 ≤ 滚动 10 年 P25？（供给压力的粗代理）

*v1.0（纯计数）回放*：2020-03 → 3/3 绿 ✓；2014-12 → 2/3 绿 ✗（实际失败——误报）；2025-04 → 1/3；当前 → 1/3。

*误报的诊断*：2014-12 的「油腿 + 低位」都成立，但没有恐慌——供给过剩型的体制重定价，恰恰「安静地发生」。*v1.1 修正：恐慌签名一票必要条件*（没有恐慌，最高只能到「黄」）。修正后回放全部对齐：

{scr_table}

规则：绿 = 恐慌 ✓ 且 ≥2/3（历史预期命中率 ≈ 恐慌组 {h_p:.0%}）；黄 = 观察区；红 = 体制重定价候选，勿用回归逻辑。

= 应用到当下（2026-08）

- 拆腿：金 {cur["d_gold"]:+.0%} / 油 {cur["d_oil"]:+.0%} → {'油腿 ✓（近 12 个月油涨得比金快）' if cur["s1"] else '金腿 ✗（抬高来自金价重估）'}；
- 恐慌签名：VIX {cur["vix"]:.1f} vs 阈值 {cur["vix_thr"]:.1f} → {'恐慌 ✓' if cur["s2"] else '平静 ✗'}；
- 油分位：{cur["oil_pctl"]:.0%} → {'低位 ✓' if cur["s3"] else '非低位 ✗'}；
- *结论：红（1/3）*。当前 GOR 高位不是「油被错杀」，不要用回归逻辑交易它；把它留在观察区，等机制变化（恐慌出现 / 油迫近），或者干脆承认：这一轮的主角是黄金的重估机制（链 D），与油无关。

*对你框架的含义*：你在判词里写的「二次确认（油价绝对低位 + VIX）」——数据把 *VIX 推上了王座*（最强单屏，35pp 的分水岭），把「油价低位」降为辅助屏。建议升级：三屏筛选器 + 恐慌签名为必要条件。'''

sec5 = f'''
= 局限

1. VIX 自 1990 年——1970–80 年代的 5 个事件未计入；
2. 「油迫近」用价格分位代理边际成本（免费盈亏线数据不可得）；
3. 样本小（恐慌组仅 {r_p} 个可判定事件）；三屏之间并非完全独立；
4. 筛选器是决策辅助，不改变 ① 的结论：即使绿区（{h_p:.1%}），仍需分仓 + 先恶化缓冲。

= 复现

- 数据：`python scripts/fetch_data.py`（VIX / 实际利率；其余复用 01 与 L1）
- 分析：`python scripts/analyze.py` → data/*.csv、figures/*.png
- 本报告：`python scripts/build_report.py`（自动生成于 {TODAY}）

#v(1em)
#align(center)[#text(size: 8.5pt, fill: rgb("#888888"))[定量建模训练场 · 延伸研究 #02 ｜ 数据：FRED ｜ build_report.py 自动生成]]'''

src = "\n\n".join([head, abstract, sec1, sec2, sec3, sec4, sec5])
OUT_TYP.write_text(src, encoding="utf-8")
print("report.typ 已生成：", len(src), "字符")

import typst  # noqa: E402
typst.compile(str(OUT_TYP), output=str(OUT_PDF))
print("PDF 已生成：", OUT_PDF.name, OUT_PDF.stat().st_size, "bytes")
