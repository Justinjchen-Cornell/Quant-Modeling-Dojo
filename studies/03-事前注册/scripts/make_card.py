# -*- coding: utf-8 -*-
"""03 事前注册 · 注册卡生成器：自动填充「当前状态」，预测字段留白（由人填写）。

用法：python scripts/make_card.py
输出：cards/注册卡-YYYY-MM-DD-GOR.md
"""
from pathlib import Path
import datetime as dt

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
L1 = ROOT.parents[1] / "lessons" / "L1-指标可靠性" / "data"
S02 = ROOT.parent / "02-机制论证" / "data"
CARDS = ROOT / "cards"
CARDS.mkdir(exist_ok=True)


def plus_months(date_str: str, m: int) -> str:
    return (pd.Timestamp(date_str) + pd.DateOffset(months=m)).strftime("%Y-%m-%d")


def main():
    gm = pd.read_csv(L1 / "gor_monthly.csv", parse_dates=["date"]).set_index("date").sort_index()
    gl = pd.read_csv(L1 / "gor_long.csv", parse_dates=["date"]).set_index("date").sort_index()
    macro = pd.read_csv(S02 / "macro_monthly.csv", parse_dates=["date"]).set_index("date").sort_index()
    scr = pd.read_csv(S02 / "screener.csv")

    ratio = gm["gor_brent"]
    t0 = ratio.index.max()
    gor_now = float(ratio.iloc[-1])
    pct = float((ratio <= gor_now).mean())
    tm = t0 - pd.DateOffset(months=12)
    dg = float(np.log(gl["gold"].asof(t0) / gl["gold"].asof(tm)))
    do = float(np.log(gm["brent"].asof(t0) / gm["brent"].asof(tm)))
    leg = "油腿主导" if abs(do) > abs(dg) else "金腿主导"
    vix = macro["vix"]
    v_now = float(vix.asof(t0))
    thr = vix.rolling(120, min_periods=60).quantile(0.80)
    v_thr = float(thr.asof(t0))
    shock = "恐慌" if v_now >= v_thr else "平静"
    win = gm["brent"].loc[:t0].iloc[-120:]
    oil_pctl = float((win <= gm["brent"].asof(t0)).mean())
    cur = scr[scr["case"].str.contains("2026-08")].iloc[0]

    today = dt.date.today().isoformat()
    card = f"""# 前向注册卡 · GOR ／ 编号 GOR-{today}

> 规则：**只写一次、提交即冻结**（`git commit` 即签署）；到期只读对账，不得修改本卡。

## 状态（自动填充 ｜ 数据截至 {t0:%Y-%m}）

| 指标 | 数值 |
|---|---|
| GOR（Brent） | **{gor_now:.1f}**（历史 {pct:.0%} 分位） |
| 本轮事件 | 金 {dg:+.0%} ／ 油 {do:+.0%} → **{leg}** |
| 恐慌签名 | VIX {v_now:.1f}（阈值 {v_thr:.1f}）→ **{shock}** |
| 油价分位（滚动 10 年） | {oil_pctl:.0%} |
| 机制筛选器（研究 02） | {int(cur['npass'])}/3 → **{cur['verdict']}** |

## 我的预测（待填写 ｜ 提交前写完）

- **P1**：未来 12 个月末，GOR 落在 ____ 至 ____ 区间，我给 ____% 的把握；
- **P2**：若未来 6 个月内 GOR 回落至 <40，主因预计是（油涨 ／ 金跌 ／ 两者兼有）：____；
- **P3**：对「油回归」逻辑，我的行动是（参与 ／ 观察 ／ 放弃）：____，理由是 ____。

## 判据（待填写）

- 命中条件：____
- 失败条件：____

## 签署与对账

- 签署方式：填完预测后 `git commit`（提交即冻结，之后不得修改本文件）
- 拟定对账日：6 个月后（{plus_months(today, 6)}）、12 个月后（{plus_months(today, 12)}）
- 对账规则：只读本卡；对账结果写入 `cards/对账记录.md`，不修改本卡
"""
    out = CARDS / f"注册卡-{today}-GOR.md"
    out.write_text(card, encoding="utf-8")
    print(f"注册卡已生成：{out.relative_to(ROOT)}")
    print(f"  状态摘要：GOR {gor_now:.1f}（{pct:.0%}）｜ {leg} ｜ VIX {v_now:.1f}（{shock}）｜ 筛选器 {int(cur['npass'])}/3")


if __name__ == "__main__":
    main()
