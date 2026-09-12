# -*- coding: utf-8 -*-
"""L1 步骤 2：条件收益 vs 基准 —— "涨 54–167%" 是怎么算出来的？

两种口径：
  A. 全部满足月（GOR≥阈值 的所有月份）→ 重叠样本，n 虚高
  B. 首次穿越（从 <阈值 升破 阈值的月份）→ 独立事件，n 很小
关键：条件收益要和"全样本基准"比。
改什么：HORIZON 12 → 6 / 24；AREA "brent" → "wti"
"""
from common import load_gor, setup_style, save, C_RED, C_GREEN
import matplotlib.pyplot as plt
import numpy as np

THRESHOLD = 45
HORIZON = 12      # 持有期（月）← 亲手改这里
AREA = "brent"    # brent 或 wti ← 或这里


def stats(x):
    x = x.dropna()
    if len(x) == 0:
        return None
    return {
        "n": len(x), "mean": x.mean(), "median": x.median(),
        "win": (x > 0).mean(), "p10": x.quantile(0.1), "p90": x.quantile(0.9),
    }


def fmt(s):
    if s is None:
        return "无样本"
    return (f"n={s['n']:>3} | 均值 {s['mean']:+7.1%} | 中位 {s['median']:+7.1%} | "
            f"胜率 {s['win']:5.1%} | P10 {s['p10']:+6.1%} | P90 {s['p90']:+7.1%}")


def main():
    setup_style()
    df = load_gor()
    price = df[AREA]
    g = df[f"gor_{AREA}"]
    fwd = price.shift(-HORIZON) / price - 1

    base = stats(fwd)
    mask_a = g >= THRESHOLD
    a = stats(fwd[mask_a])
    cross = mask_a & (g.shift(1) < THRESHOLD)
    b = stats(fwd[cross])

    print(f"资产: {AREA.upper()} | 持有期: {HORIZON} 个月 | 阈值: {THRESHOLD}")
    print(f"基准（全样本）        : {fmt(base)}")
    print(f"口径A（满足月）       : {fmt(a)}   ← 重叠窗口！独立样本≈n/{HORIZON}")
    print(f"口径B（首次穿越事件） : {fmt(b)}")
    if a and b:
        print(f"对照: 口径A比基准均值差 {a['mean'] - base['mean']:+.1%}；"
              f"口径B只有 {b['n']} 个独立事件（样本这么小，谈'历史规律'要谨慎）")
    print()
    print("提示：口径A的 n 看起来很大，但相邻观测高度重叠，不能按独立样本解读。")

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))

    ax = axes[0]
    xb = fwd.dropna().values
    xa = fwd[mask_a].dropna().values
    lo = min(xb.min(), xa.min()) if len(xa) else xb.min()
    hi = max(xb.max(), xa.max())
    bins = np.linspace(lo, hi, 32)
    ax.hist(xb, bins=bins, density=True, color="#c8cdd3", alpha=0.85,
            label=f"基准（全样本 n={base['n']}）")
    ax.hist(xa, bins=bins, density=True, color=C_RED, alpha=0.55,
            label=f"GOR≥{THRESHOLD}（n={a['n'] if a else 0}）")
    ax.axvline(0, color="k", lw=0.8)
    ax.legend(fontsize=9, framealpha=0.9)
    ax.set_title(f"{AREA.upper()} 未来 {HORIZON} 个月收益：条件 vs 基准")
    ax.set_xlabel("未来收益率")
    ax.set_ylabel("密度")

    ax = axes[1]
    labels = ["基准", "口径A\n(满足月)", "口径B\n(穿越事件)"]
    means = [base["mean"], a["mean"] if a else np.nan, b["mean"] if b else np.nan]
    wins = [base["win"], a["win"] if a else np.nan, b["win"] if b else np.nan]
    xpos = np.arange(3)
    ax.bar(xpos - 0.18, means, width=0.34, color=["#7f8c8d", C_RED, C_GREEN], label="平均收益")
    ax.bar(xpos + 0.18, wins, width=0.34, color=["#bdc3c7", "#e6b0aa", "#a9dfbf"], label="胜率")
    for i, (m, w) in enumerate(zip(means, wins)):
        if not np.isnan(m):
            ax.annotate(f"{m:+.0%}", xy=(i - 0.18, m), ha="center", va="bottom", fontsize=9)
            ax.annotate(f"{w:.0%}", xy=(i + 0.18, w), ha="center", va="bottom", fontsize=9)
    ax.set_xticks(xpos, labels)
    ax.set_title("两种口径 vs 基准（收益 / 胜率）")
    ax.legend(fontsize=9)

    fig.tight_layout()
    save(fig, "step2_conditional")


if __name__ == "__main__":
    main()
