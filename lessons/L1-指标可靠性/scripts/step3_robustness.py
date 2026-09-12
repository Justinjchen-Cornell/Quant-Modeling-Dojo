# -*- coding: utf-8 -*-
"""L1 步骤 3：稳健性网格 —— 换个起点/阈值/持有期，结论还站得住吗？

网格：起点 ∈ {1990, 2000, 2010, 2015, 2020} × 阈值 ∈ {40, 45, 50, 55} × 持有期 ∈ {6, 12, 24}
指标：口径A（满足月）条件均值 − 基准均值、胜率、n
输出：outputs/step3_robustness.png/.pdf + outputs/step3_robustness_table.csv
"""
from common import load_gor, setup_style, save, OUT
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

STARTS = [1990, 2000, 2010, 2015, 2020]
THRESHOLDS = [40, 45, 50, 55]
HORIZONS = [6, 12, 24]
AREA = "brent"


def build_table(df0):
    rows = []
    for start in STARTS:
        df = df0[df0.index >= f"{start}-01-01"]
        price, g = df[AREA], df[f"gor_{AREA}"]
        for h in HORIZONS:
            fwd = price.shift(-h) / price - 1
            base = fwd.dropna().mean()
            for t in THRESHOLDS:
                x = fwd[g >= t].dropna()
                rows.append(dict(
                    start=start, horizon=h, thr=t, n=len(x),
                    diff=(x.mean() - base) if len(x) else np.nan,
                    win=((x > 0).mean() if len(x) else np.nan),
                ))
    return pd.DataFrame(rows)


def main():
    setup_style()
    res = build_table(load_gor())

    fmt = lambda v: "—" if pd.isna(v) else f"{v:+.1%}"  # noqa: E731
    fmtw = lambda v: "—" if pd.isna(v) else f"{v:.0%}"  # noqa: E731
    pd.set_option("display.width", 200)
    print(res.to_string(index=False, formatters={"diff": fmt, "win": fmtw}))
    print()
    print("读法：diff = 条件均值 − 基准均值。看同一行（起点）在不同阈值之间、")
    print("      以及同一列在不同起点之间的变化——变化越大，结论越不稳。")

    fig, axes = plt.subplots(1, len(HORIZONS), figsize=(4.4 * len(HORIZONS) + 1.2, 3.8), sharey=True)
    vmax = float(np.nanmax(np.abs(res["diff"]))) if res["diff"].notna().any() else 0.1
    vmax = max(vmax, 0.05)
    im = None
    for ax, h in zip(axes, HORIZONS):
        sub = res[res.horizon == h]
        piv = sub.pivot(index="start", columns="thr", values="diff")
        n_piv = sub.pivot(index="start", columns="thr", values="n")
        im = ax.imshow(piv.values, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
        ax.set_xticks(range(len(THRESHOLDS)), THRESHOLDS)
        ax.set_yticks(range(len(STARTS)), [f"{s} 起" for s in STARTS])
        ax.set_title(f"持有期 {h} 个月")
        ax.set_xlabel("阈值")
        if ax is axes[0]:
            ax.set_ylabel("样本起点")
        ax.grid(False)
        for i in range(piv.shape[0]):
            for j in range(piv.shape[1]):
                v, nn = piv.values[i, j], n_piv.values[i, j]
                txt = "—" if np.isnan(v) else f"{v:+.0%}\n(n={int(nn)})"
                ax.annotate(txt, xy=(j, i), ha="center", va="center", fontsize=8)
    fig.suptitle(f"稳健性网格：条件均值 − 基准（{AREA.upper()}）· 颜色越红差异越大", y=1.04)
    fig.colorbar(im, ax=axes, shrink=0.82, format=lambda v, _: f"{v:+.0%}")
    save(fig, "step3_robustness")

    res.to_csv(OUT / "step3_robustness_table.csv", index=False, float_format="%.4f")
    print("表格已保存: outputs/step3_robustness_table.csv")


if __name__ == "__main__":
    main()
