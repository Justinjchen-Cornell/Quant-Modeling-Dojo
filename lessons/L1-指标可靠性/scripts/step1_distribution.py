# -*- coding: utf-8 -*-
"""L1 步骤 1：GOR 长什么样？—— 分布与分位。

看什么：样本区间 / 中位数 / 90、95、99 分位 / 45 的位置 / ≥45 的时间占比 / 独立片段数
改什么：命令行传阈值（如 python step1_distribution.py 40），观察"极端"叙事怎么变
"""
import sys

from common import load_gor, setup_style, save, C_MAIN, C_RED, C_GREY
import matplotlib.pyplot as plt

THRESHOLD = int(sys.argv[1]) if len(sys.argv) > 1 else 45  # 命令行可传：python step1_distribution.py 40


def main():
    setup_style()
    df = load_gor()
    g = df["gor_brent"].dropna()
    last = g.iloc[-1]

    q50, q90, q95, q99 = g.quantile([0.5, 0.9, 0.95, 0.99])
    pct = (g <= last).mean()
    share = (g >= THRESHOLD).mean()

    above = g >= THRESHOLD
    runs = (above != above.shift()).cumsum()[above]
    n_runs = runs.nunique()
    longest = int(runs.value_counts().max()) if n_runs else 0

    print(f"样本区间: {g.index.min():%Y-%m} → {g.index.max():%Y-%m}，共 {len(g)} 个月")
    print(f"中位数 {q50:.1f} | 90分位 {q90:.1f} | 95分位 {q95:.1f} | 99分位 {q99:.1f}")
    print(f"当前值 {last:.1f}（{g.index.max():%Y-%m}）→ 位于 {pct:.0%} 分位")
    print(f"GOR≥{THRESHOLD} 时间占比: {share:.1%}（{int(above.sum())} 个月）")
    print(f"≥{THRESHOLD} 的独立片段数: {n_runs}，最长持续 {longest} 个月")

    fig, axes = plt.subplots(2, 1, figsize=(10, 7.5), gridspec_kw={"height_ratios": [1.35, 1]})

    ax = axes[0]
    ax.plot(g.index, g.values, lw=1.3, color=C_MAIN)
    ax.axhline(THRESHOLD, color=C_RED, lw=1.2, ls="--")
    ax.annotate(f"阈值 {THRESHOLD}", xy=(g.index[len(g) // 24], THRESHOLD), xytext=(0, 6),
                textcoords="offset points", color=C_RED, fontsize=10)
    ax.set_title(f"金油比 GOR（金价 ÷ 布伦特油价）— 月频，{g.index.min():%Y-%m} 至 {g.index.max():%Y-%m}")
    ax.set_ylabel("GOR")

    ax = axes[1]
    ax.hist(g.values, bins=36, color="#aeb6bf", edgecolor="white", lw=0.7)
    ymax = ax.get_ylim()[1]
    for qv, c, lab, hfrac in ((q50, C_GREY, f"中位 {q50:.0f}", 0.92),
                              (q95, C_MAIN, f"P95 {q95:.0f}", 0.92),
                              (THRESHOLD, C_RED, f"{THRESHOLD}", 0.76)):
        ax.axvline(qv, color=c, lw=1.2, ls="--")
        ax.annotate(lab, xy=(qv, ymax * hfrac), ha="center", color=c, fontsize=9)
    ax.set_title("GOR 分布：45 在历史里算什么水平？")
    ax.set_xlabel("GOR")

    fig.tight_layout()
    save(fig, "step1_distribution" if THRESHOLD == 45 else f"step1_distribution_t{THRESHOLD}")


if __name__ == "__main__":
    main()
