# -*- coding: utf-8 -*-
"""L1 增补演示：③ 照片 vs 事件 & ④ 显著性的四个阶梯（真实数据）。

数据：data/gor_monthly.csv（Brent 口径，1987–2026）
用法：python scripts/extra_overlap_demo.py
输出：outputs/extra_overlap_demo.png/.pdf + 控制台
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from scipy import stats as sps

from common import setup_style, save

ROOT = Path(__file__).resolve().parents[1]
THR = 45
H = 12


def main():
    setup_style()
    df = pd.read_csv(ROOT / "data" / "gor_monthly.csv", parse_dates=["date"]).set_index("date").sort_index()
    g = df["gor_brent"]
    fwd = df["brent"].shift(-H) / df["brent"] - 1

    cond = fwd[g >= THR].dropna()
    allr = fwd.dropna()
    base_mean = allr.mean()

    # ---------- ③ 照片列表 ----------
    print("=== ③ 10 张“照片”（=满足月起的未来 12 个月收益） ===")
    for m, v in cond.items():
        print(f"  {m:%Y-%m} → {m + pd.DateOffset(months=12):%Y-%m}    {v:+.0%}")
    print("  相邻照片重叠：11/12 个月")
    print()

    # ---------- ④ 四个阶梯 ----------
    n_c = len(cond)
    sd_c = cond.std(ddof=1)
    t1 = (cond.mean() - base_mean) / (sd_c / np.sqrt(n_c))
    p1 = sps.t.sf(t1, n_c - 1)

    cross = (g >= THR) & (g.shift(1).fillna(False) < THR)
    ev = fwd[cross].dropna()
    t2 = (ev.mean() - base_mean) / (ev.std(ddof=1) / np.sqrt(len(ev)))
    p2 = sps.t.sf(t2, len(ev) - 1)

    # Newey-West（L=12，处理重叠窗口的误差修正）
    Dd = (g >= THR)
    idx = fwd.dropna().index
    Y = fwd.loc[idx].to_numpy()
    Dv = Dd.loc[idx].astype(float).to_numpy()
    X = np.column_stack([np.ones_like(Dv), Dv])
    beta = np.linalg.lstsq(X, Y, rcond=None)[0]
    resid = Y - X @ beta
    XtX_inv = np.linalg.inv(X.T @ X)
    L = 12
    S = (X * resid[:, None]).T @ (X * resid[:, None])
    for k in range(1, L + 1):
        w = 1 - k / (L + 1)
        A = X[k:] * resid[k:, None]
        B = X[:-k] * resid[:-k, None]
        Gk = A.T @ B
        S += w * (Gk + Gk.T)
    V = XtX_inv @ S @ XtX_inv
    t3 = beta[1] / np.sqrt(V[1, 1])
    p3 = sps.t.sf(t3, n_c - 1)

    # 反事实：最弱事件归零
    ev2 = ev.copy()
    weakest = ev.idxmin()
    ev2.loc[weakest] = 0.0
    t4 = (ev2.mean() - base_mean) / (ev2.std(ddof=1) / np.sqrt(len(ev2)))
    p4 = sps.t.sf(t4, len(ev2) - 1)

    print("=== ④ 显著性的四个阶梯（基准均值 {:+.1%}，单侧检验） ===".format(base_mean))
    print(f"  ① 朴素（10 张照片当 10 个独立样本）    : t = {t1:5.2f} ｜ p = {p1:.4f}")
    print(f"  ② 事件级（{len(ev)} 个故事）                : t = {t2:5.2f} ｜ p = {p2:.4f}")
    print(f"  ③ Newey-West 校正（L={L}，扣重叠分）   : t = {t3:5.2f} ｜ p = {p3:.4f}")
    print(f"  ④ 反事实（把最弱事件 {weakest:%Y-%m} 改为 0）: t = {t4:5.2f} ｜ p = {p4:.4f}")
    print(f"  （事件值：{', '.join(f'{m:%Y-%m}={v:+.0%}' for m, v in ev.items())}）")

    # ---------- 图：照片窗口 ----------
    months = list(cond.index)
    vals = list(cond.values)
    groups = []
    for m in months:
        if m < pd.Timestamp("2020-06-01"):
            groups.append("疫情第一波")
        elif m < pd.Timestamp("2021-01-01"):
            groups.append("疫情余波")
        else:
            groups.append("黄金重估")
    colors = {"疫情第一波": "#c0392b", "疫情余波": "#e67e22", "黄金重估": "#1e8449"}

    t0 = pd.Timestamp("2019-01-01")
    fig, ax = plt.subplots(figsize=(10.5, 5))
    for i, (m, v, grp) in enumerate(zip(months, vals, groups)):
        x0 = (m - t0).days
        ax.barh(i, 365, left=x0, height=0.62, color=colors[grp], alpha=0.88)
        ax.text(x0 + 365 + 14, i, f"{v:+.0%}", va="center", fontsize=9)
    ax.set_yticks(range(len(months)), [f"{m:%Y-%m}" for m in months])
    ax.invert_yaxis()
    ticks = [(pd.Timestamp(f"{y}-01-01") - t0).days for y in range(2020, 2028)]
    ax.set_xticks(ticks, [str(y) for y in range(2020, 2028)])
    ax.set_xlim((pd.Timestamp("2019-10-01") - t0).days, (pd.Timestamp("2027-06-01") - t0).days)
    ax.set_title("10 张“照片” vs 3 个场景 —— GOR≥45 的未来 12 个月窗口（Brent）")
    ax.set_xlabel("每一行 = 该月起未来 12 个月的收益窗口；横向叠得越厚 = 看到的“未来”越是同一段")
    ax.legend(handles=[Patch(color=c, label=k) for k, c in colors.items()],
              loc="lower right", fontsize=9)
    fig.tight_layout()
    save(fig, "extra_overlap_demo")


if __name__ == "__main__":
    main()
