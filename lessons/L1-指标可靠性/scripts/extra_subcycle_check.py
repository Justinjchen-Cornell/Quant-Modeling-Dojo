# -*- coding: utf-8 -*-
"""L1 课后延伸①：拆两条腿 —— GOR 冲高是"油崩"还是"金涨"驱动的？

对每段 GOR≥45 事件，比较两腿的贡献（比值的对数变化 ≈ 金腿 − 油腿）。
数据：data/gor_long.csv（金价 × WTI）。
用法：python scripts/extra_subcycle_check.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
THRESHOLD = 45


def main():
    df = pd.read_csv(ROOT / "data" / "gor_long.csv", parse_dates=["date"]).set_index("date").sort_index()
    g = df["gor_wti"]
    above = g >= THRESHOLD
    groups = (above != above.shift()).cumsum()[above]
    for _, seg in g[above].groupby(groups):
        start, end, peak = seg.index.min(), seg.index.max(), seg.idxmax()
        pre = df.loc[:start].index[-2]  # 事件前一个月
        dg = df.loc[peak, "gold"] / df.loc[pre, "gold"] - 1
        do = df.loc[peak, "wti"] / df.loc[pre, "wti"] - 1
        who = "油崩（分母驱动）" if abs(do) > abs(dg) else "黄金涨（分子驱动）"
        print(f"事件 {start:%Y-%m}→{end:%Y-%m}｜峰 {peak:%Y-%m}（{seg.max():.1f}）"
              f"｜黄金 {dg:+.0%}｜油价 {do:+.0%}｜主角 = {who}")


if __name__ == "__main__":
    main()
