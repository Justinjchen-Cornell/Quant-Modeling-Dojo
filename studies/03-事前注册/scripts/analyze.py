# -*- coding: utf-8 -*-
"""03 事前注册 · 演示分析。

演示 1（模拟）：在无信号的随机世界里扫描阈值 → "总能找到铁证"；样本外归零。
演示 2（真实数据）：GOR 的"发现 → 前向"实验——每次只用当时可得的数据挑选"最优阈值"，
                     看它在之后 5 年里的触发与表现；外加阈值稀疏度阶梯。

输出：data/demo1_selection.csv、data/demo2_walkforward.csv、data/sparsity.csv、figures/*.png
"""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

L1 = ROOT.parents[1] / "lessons" / "L1-指标可靠性" / "data"

C_RED, C_GRAY, C_BLUE, C_GREEN, C_AMBER = "#c0392b", "#95a5a6", "#2471a3", "#1e8449", "#d68910"


def setup_style():
    plt.rcParams.update({
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial"],
        "axes.unicode_minus": False,
        "figure.dpi": 110, "savefig.dpi": 300,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
        "axes.titlesize": 11, "axes.labelsize": 10,
    })


# ---------------- 演示 1：随机世界里的"圣杯" ----------------
def demo1_selection(n_worlds=400, T=480, n_thr=16, seed=42):
    rng = np.random.default_rng(seed)
    grid = np.linspace(0.85, 0.99, n_thr)          # 16 档"阈值版本"
    ins_ts, oos_ts = [], []
    for _ in range(n_worlds):
        x = np.cumsum(rng.normal(0, 0.08, T))       # “比值”随机游走
        y = np.cumsum(rng.normal(0.004, 0.09, T))   # “资产价格”（有漂移、与 x 无关）
        fwd = np.full(T, np.nan)
        fwd[:-12] = y[12:] - y[:-12]
        cut = int(T * 0.6)
        edge = cut - 12          # 样本内触发的未来收益也必须在边界前"结算"（杜绝前视）
        qs = np.quantile(x[:edge], grid)
        best_t, best_q = -1e9, None
        for q in qs:
            m = np.where((x[:edge] >= q) & ~np.isnan(fwd[:edge]))[0]
            if len(m) < 5:
                continue
            c = fwd[m]
            se = c.std(ddof=1) / np.sqrt(len(m))
            if se == 0:
                continue
            tt = (c.mean() - np.nanmean(fwd[:edge])) / se
            if tt > best_t:
                best_t, best_q = tt, q
        if best_q is None:
            continue
        ins_ts.append(best_t)
        m2 = np.where((x[cut:] >= best_q) & ~np.isnan(fwd[cut:]))[0]
        if len(m2) >= 3:
            c2 = fwd[cut:][m2]
            se2 = c2.std(ddof=1) / np.sqrt(len(m2))
            oos_ts.append((c2.mean() - np.nanmean(fwd[cut:])) / se2 if se2 > 0 else np.nan)
        else:
            oos_ts.append(np.nan)
    ins_ts = np.array(ins_ts)
    oos_ts = np.array(oos_ts)
    fin = np.isfinite(oos_ts)
    res = dict(
        n=len(ins_ts),
        ins_mean=float(np.mean(ins_ts)),
        p_ins=float((ins_ts > 2).mean()),
        oos_n=int(fin.sum()),
        oos_mean=float(oos_ts[fin].mean()),
        p_oos=float((oos_ts[fin] > 2).mean()),
        oos_neg=float((oos_ts[fin] < 0).mean()),
        oos_missing=float(1 - fin.mean()),
    )
    print("=== 演示 1：随机世界扫描（16 档阈值，400 个世界）===")
    print(f"  样本内'最优阈值'的 t 均值 = {res['ins_mean']:.2f}；P(t>2) = {res['p_ins']:.0%}")
    print(f"  同一规则样本外：均值 t = {res['oos_mean']:.2f}；P(t>2) = {res['p_oos']:.0%}；"
          f"变负比例 = {res['oos_neg']:.0%}；样本外失效（无触发）比例 = {res['oos_missing']:.0%}")
    pd.DataFrame(dict(ins_t=ins_ts, oos_t=oos_ts)).to_csv(DATA / "demo1_selection.csv", index=False)
    return res, ins_ts, oos_ts


# ---------------- 演示 2：真实数据的"发现 → 前向" ----------------
def find_crossings(idx, cond):
    prev = np.concatenate([[False], cond[:-1]])
    return idx[cond & ~prev]


def demo2_walkforward(gm):
    ratio = gm["gor_brent"]
    oil = gm["brent"]
    fwd = oil.shift(-12) / oil - 1
    idx = ratio.index
    grid = list(range(30, 62, 2))                   # 30..60，16 档
    rows = []
    for Y in range(2000, 2025, 2):
        t0 = pd.Timestamp(f"{Y}-12-31")
        ins = np.asarray(idx <= t0 - pd.DateOffset(months=12))  # 触发须在前 12 个月内结算（无前视）
        base = fwd[ins].dropna().mean()
        best_q, best_x, nins = None, -1e9, 0
        for q in grid:
            m = (ratio[ins] >= q) & fwd[ins].notna()
            c = fwd[ins][m]
            if len(c) < 4:
                continue
            x = c.mean() - base
            if x > best_x:
                best_x, best_q, nins = x, q, len(c)
        fw = np.asarray((idx > t0) & (idx <= t0 + pd.DateOffset(years=5)))
        if best_q is None:
            rows.append(dict(year=Y, thr=np.nan, ins_excess=np.nan, ins_n=0,
                             fwd_events=0, fwd_months=0, fwd_excess=np.nan,
                             f45_events=int(len(find_crossings(idx[fw], (ratio >= 45).to_numpy()[fw])))))
            continue
        cond = (ratio >= best_q).to_numpy()
        ev = find_crossings(idx[fw], cond[fw])
        trig_m = int((cond[fw] & fwd[fw].notna().to_numpy()).sum())
        c2 = fwd[(fw & cond)].dropna()
        fx = (c2.mean() - fwd[fw].dropna().mean()) if len(c2) else np.nan
        e45 = find_crossings(idx[fw], (ratio >= 45).to_numpy()[fw])
        rows.append(dict(year=Y, thr=best_q, ins_excess=best_x, ins_n=nins,
                         fwd_events=len(ev), fwd_months=trig_m, fwd_excess=fx, f45_events=len(e45)))
    wf = pd.DataFrame(rows)
    print()
    print("=== 演示 2：真实数据'发现 → 前向'（GOR·Brent，1987–2026）===")
    for _, r in wf.iterrows():
        if np.isnan(r["thr"]):
            print(f"  {int(r['year'])}：样本内无从选择（可用触发月 <4）")
        else:
            fx = "—" if np.isnan(r["fwd_excess"]) else f"{r['fwd_excess']:+.0%}"
            print(f"  {int(r['year'])}：选阈值 {int(r['thr'])}（样本内超额 {r['ins_excess']:+.0%}，n={int(r['ins_n'])}）"
                  f" → 前向 5 年触发 {int(r['fwd_events'])} 次（{int(r['fwd_months'])} 个月），超额 {fx}"
                  f" ｜ 同期固定 45 触发 {int(r['f45_events'])} 次")
    wf.to_csv(DATA / "demo2_walkforward.csv", index=False, float_format="%.4f")
    return wf


def sparsity(gm):
    ratio = gm["gor_brent"]
    out = []
    for q in (40, 45, 50, 55, 60):
        m = (ratio >= q).to_numpy()
        prev = np.concatenate([[False], m[:-1]])
        out.append(dict(thr=q, months=int(m.sum()), crossings=int((m & ~prev).sum())))
    sp = pd.DataFrame(out)
    print()
    print("=== 阈值稀疏度阶梯（1987–2026）===")
    print(sp.to_string(index=False))
    sp.to_csv(DATA / "sparsity.csv", index=False)
    return sp


# ---------------- 图 ----------------
def fig_selection(res, ins_ts, oos_ts):
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), gridspec_kw={"width_ratios": [1.8, 1]})
    ax = axes[0]
    bins = np.linspace(-4, 6.5, 43)
    ax.hist(ins_ts, bins=bins, color=C_RED, alpha=0.72,
            label=f"样本内'最优阈值'的 t（均值 {res['ins_mean']:.1f}）")
    fin = oos_ts[np.isfinite(oos_ts)]
    ax.hist(fin, bins=bins, color=C_GRAY, alpha=0.88,
            label=f"同一规则样本外的 t（均值 {res['oos_mean']:.1f}）")
    ax.axvline(2, color="k", lw=1, ls="--")
    ax.annotate("t = 2（“显著”线）", xy=(2.05, ax.get_ylim()[1] * 0.88), fontsize=9)
    ax.set_xlabel("t 统计量")
    ax.set_title("随机数据里的“发现”：样本内 vs 样本外")
    ax.legend(fontsize=9, loc="upper right")
    ax = axes[1]
    ax.bar(["样本内", "样本外"], [res["p_ins"], res["p_oos"]], color=[C_RED, C_GRAY], alpha=0.88, width=0.5)
    ax.annotate(f"{res['p_ins']:.0%}", (0, res["p_ins"]), ha="center", va="bottom", fontsize=12)
    ax.annotate(f"{res['p_oos']:.0%}", (1, res["p_oos"]), ha="center", va="bottom", fontsize=12)
    ax.set_ylim(0, max(res["p_ins"], res["p_oos"]) * 1.4 + 0.02)
    ax.set_title("P( t > 2 )：“显著”的比例")
    fig.tight_layout()
    fig.savefig(FIG / "fig1_selection.png", bbox_inches="tight")
    plt.close(fig)


def fig_walkforward(wf):
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6))
    ax = axes[0]
    ok = wf[wf["thr"].notna()]
    ax.scatter(ok["year"], ok["thr"], color=C_RED, s=48, zorder=5)
    for _, r in ok.iterrows():
        ax.annotate(f"{int(r['thr'])}", (r["year"], r["thr"]), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=8.5)
    miss = wf[wf["thr"].isna()]
    for _, r in miss.iterrows():
        ax.scatter([r["year"]], [30.5], marker="x", color=C_GRAY, s=40)
    ax.annotate("被选中的阈值贴着当时历史的水位：30（2000s）→ 32（2018）→ 46（2022 后）",
                xy=(2000.6, 32.6), fontsize=9, color=C_GRAY)
    ax.axhline(45, color=C_BLUE, lw=1.2, ls="--")
    ax.annotate("固定 45", xy=(1999.6, 46.0), color=C_BLUE, fontsize=9)
    ax.set_ylim(28, 66)
    ax.set_xlabel("发现年份（只用该年之前的数据挑选“最优阈值”）")
    ax.set_ylabel("被选中的阈值")
    ax.set_title("每次“研究”挑出来的阈值")
    ax = axes[1]
    ax.bar(wf["year"], wf["fwd_events"], color=C_AMBER, alpha=0.88, width=1.4,
           label="选中阈值：前向 5 年触发次数")
    ax.plot(wf["year"], wf["f45_events"], color=C_BLUE, marker="o", lw=1.4, ms=4,
            label="同期固定 45 的触发次数")
    ax.set_xlabel("发现年份")
    ax.set_title("前向 5 年：“圣杯”开了几次火？")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "fig2_walkforward.png", bbox_inches="tight")
    plt.close(fig)


def fig_sparsity(sp):
    fig, ax = plt.subplots(figsize=(8.8, 3.9))
    x = np.arange(len(sp))
    ax.bar(x - 0.18, sp["months"], width=0.36, color="#aeb6bf", label="≥ 阈值的月份数")
    ax.bar(x + 0.18, sp["crossings"], width=0.36, color=C_RED, label="首次穿越（独立事件）次数")
    for xi in range(len(sp)):
        ax.annotate(f"{int(sp['months'].iloc[xi])}", (xi - 0.18, sp["months"].iloc[xi]),
                    ha="center", va="bottom", fontsize=9, color="#5d6d7e")
        ax.annotate(f"{int(sp['crossings'].iloc[xi])}", (xi + 0.18, sp["crossings"].iloc[xi]),
                    ha="center", va="bottom", fontsize=9, color=C_RED)
    ax.set_xticks(x, sp["thr"].astype(int))
    ax.set_xlabel("GOR 阈值")
    ax.set_title("阈值稀疏度阶梯：数字越大，“事件”越少")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "fig3_sparsity.png", bbox_inches="tight")
    plt.close(fig)


def main():
    setup_style()
    gm = pd.read_csv(L1 / "gor_monthly.csv", parse_dates=["date"]).set_index("date").sort_index()
    res, ins_ts, oos_ts = demo1_selection()
    wf = demo2_walkforward(gm)
    sp = sparsity(gm)
    fig_selection(res, ins_ts, oos_ts)
    fig_walkforward(wf)
    fig_sparsity(sp)

    lines = ["# 03 事前注册 · 结果摘要", ""]
    lines.append("## 演示 1（随机世界，400 个世界 × 16 档阈值）")
    lines.append(f"- 样本内最优 t 均值 {res['ins_mean']:.2f}，P(t>2) = {res['p_ins']:.0%}")
    lines.append(f"- 同一规则样本外：t 均值 {res['oos_mean']:.2f}，P(t>2) = {res['p_oos']:.0%}，"
                 f"变负 {res['oos_neg']:.0%}，无触发 {res['oos_missing']:.0%}")
    lines.append("")
    lines.append("## 演示 2（真实数据：发现 → 前向）")
    lines.append(wf.to_string(index=False))
    lines.append("")
    lines.append("## 稀疏度阶梯")
    lines.append(sp.to_string(index=False))
    (DATA / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print()
    print("图已保存：figures/fig1_selection.png / fig2_walkforward.png / fig3_sparsity.png")


if __name__ == "__main__":
    main()
