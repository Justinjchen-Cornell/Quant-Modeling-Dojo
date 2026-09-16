# -*- coding: utf-8 -*-
"""L1 步骤 3 加餐：长样本 —— 45 在半个多世纪里还站得住吗？

数据：data/gor_long.csv（金价 LBMA 1833+ × WTI 1946+，月均值）
口径注意：1971 年前美元与黄金固定兑换（$35/盎司，布雷顿森林），GOR 无市场含义；
          分析样本取 1971-01 起（自由浮动后的约 55 年）。
输出：outputs/step3_long_history.png/.pdf
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from common import setup_style, save

ROOT = Path(__file__).resolve().parents[1]
THRESHOLD = 45


def main():
    setup_style()
    df = pd.read_csv(ROOT / "data" / "gor_long.csv", parse_dates=["date"]).set_index("date").sort_index()
    g_all = df["gor_wti"].dropna()
    g = g_all[g_all.index >= "1971-01-01"]

    q50, q90, q95, q99 = g.quantile([0.5, 0.9, 0.95, 0.99])
    above = g >= THRESHOLD
    groups = (above != above.shift()).cumsum()[above]
    eps = [(seg.index.min(), seg.index.max(), len(seg), seg.max()) for _, seg in g[above].groupby(groups)]
    cross = int(((g >= THRESHOLD) & (g.shift(1) < THRESHOLD)).sum())

    print(f"分析样本: {g.index.min():%Y-%m} → {g.index.max():%Y-%m}，共 {len(g)} 个月（约 {len(g)/12:.0f} 年）")
    print(f"中位 {q50:.1f} | P90 {q90:.1f} | P95 {q95:.1f} | P99 {q99:.1f}")
    print(f"GOR≥{THRESHOLD}: 时间占比 {above.mean():.2%}（{int(above.sum())} 个月）"
          f"｜独立片段 {len(eps)} 段｜首次穿越 {cross} 次")
    for a_, b_, n_, pk in eps:
        print(f"  {a_:%Y-%m} → {b_:%Y-%m}   {n_:>2} 个月   峰值 {pk:.1f}")

    fig, axes = plt.subplots(2, 1, figsize=(11, 7.6), gridspec_kw={"height_ratios": [1.45, 1]})

    ax = axes[0]
    pre = g_all[g_all.index < "1971-01-01"]
    ax.axvspan(g_all.index.min(), pd.Timestamp("1971-01-01"), color="#f4f6f7", zorder=0)
    ax.plot(pre.index, pre.values, lw=1.0, color="#bdc3c7", zorder=2)
    ax.plot(g.index, g.values, lw=1.3, color="#2c3e50", zorder=3)
    ax.axhline(THRESHOLD, color="#c0392b", lw=1.2, ls="--", zorder=1)
    ax.annotate("阈值 45", xy=(pd.Timestamp("1973-01-01"), THRESHOLD), xytext=(0, 5),
                textcoords="offset points", color="#c0392b", fontsize=10)
    ax.annotate("1946–1971：金价固定 $35（布雷顿森林）\n→ GOR 无市场含义",
                xy=(pd.Timestamp("1947-06-01"), 55), fontsize=9, color="#7f8c8d")
    ax.set_title(f"金油比（金价 ÷ WTI）全史：{g_all.index.min():%Y-%m} → {g_all.index.max():%Y-%m}")
    ax.set_ylabel("GOR")

    ax = axes[1]
    ax.hist(g.values, bins=42, color="#aeb6bf", edgecolor="white", lw=0.7)
    ymax = ax.get_ylim()[1]
    for qv, c, lab, hf in ((q50, "#7f8c8d", f"中位 {q50:.0f}", 0.92),
                           (q95, "#2c3e50", f"P95 {q95:.0f}", 0.92),
                           (THRESHOLD, "#c0392b", f"{THRESHOLD}", 0.74)):
        ax.axvline(qv, color=c, lw=1.2, ls="--")
        ax.annotate(lab, xy=(qv, ymax * hf), ha="center", color=c, fontsize=9)
    ax.set_title("1971–2026 分布：45 依然在最右侧的尾巴里")
    ax.set_xlabel("GOR")

    fig.tight_layout()
    save(fig, "step3_long_history")


if __name__ == "__main__":
    main()
