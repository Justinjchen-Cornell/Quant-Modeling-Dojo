# -*- coding: utf-8 -*-
"""02 机制论证 · 三项机制检验 + 机制筛选器。

检验：
  T1 拆腿分类：金油比事件中，油腿主导 vs 金腿主导 → 回归结局对比
  T2 恐慌签名：全部 55 事件（自 01）触发时的 VIX 滚动分位 → 恐慌组 vs 平静组
  T3 黄金重估：金价对 10Y 实际利率的回归（2003–2019 vs 2020–2026）→ "重估缺口"

筛选器 v1.0：三屏（拆腿 / 恐慌签名 / 油价迫近）→ 绿/黄/红；回放 3 个历史案 + 应用到当前。
输出：data/t1_legs.csv、data/t2_vix.csv、data/screener.csv、data/t3_gold.csv、figures/*.png
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
S01 = ROOT.parent / "01-比值回归" / "data"

C_HI, C_LO, C_G, C_GREEN, C_AMBER = "#c0392b", "#2471a3", "#7f8c8d", "#1e8449", "#d68910"


def setup_style():
    plt.rcParams.update({
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial"],
        "axes.unicode_minus": False,
        "figure.dpi": 110, "savefig.dpi": 300,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
        "axes.titlesize": 11, "axes.labelsize": 10,
    })


def load_all():
    gm = pd.read_csv(L1 / "gor_monthly.csv", parse_dates=["date"]).set_index("date").sort_index()
    gl = pd.read_csv(L1 / "gor_long.csv", parse_dates=["date"]).set_index("date").sort_index()
    macro = pd.read_csv(DATA / "macro_monthly.csv", parse_dates=["date"]).set_index("date").sort_index()
    ev = pd.read_csv(S01 / "events.csv", parse_dates=["date"])
    return gm, gl, macro, ev


# ---------------- T1 拆腿分类 ----------------
def t1_legs(gm, gl, ev):
    gold = gl["gold"]
    rows = []
    for _, r in ev[ev.world.str.startswith("金油比")].iterrows():
        oil = gm["brent"] if "Brent" in r["world"] else gl["wti"]
        t0 = r["date"]
        tm = t0 - pd.DateOffset(months=12)
        dg = float(np.log(gold.asof(t0) / gold.asof(tm)))
        do = float(np.log(oil.asof(t0) / oil.asof(tm)))
        leg = "油腿主导" if abs(do) > abs(dg) else "金腿主导"
        status = "命中" if pd.notna(r["half_month"]) else ("进行中" if r["truncated"] else "未命中")
        rows.append(dict(world=r["world"], date=t0, side=r["side"], d_gold=dg, d_oil=do,
                         leg=leg, status=status))
    t1 = pd.DataFrame(rows)
    print("=== T1 拆腿分类（金油比事件 × 12 个月腿部贡献）===")
    for leg in ("油腿主导", "金腿主导"):
        sub = t1[t1.leg == leg]
        res = sub[sub.status != "进行中"]
        rate = (res.status == "命中").mean() if len(res) else np.nan
        print(f"  {leg}: {len(sub)} 个事件（可判定 {len(res)}），半程回归率 {rate:.1%}")
        for _, r in sub.iterrows():
            print(f"     {r['date']:%Y-%m} [{r['side']}] 金 {r['d_gold']:+.0%} / 油 {r['d_oil']:+.0%} → {r['status']}")
    t1.to_csv(DATA / "t1_legs.csv", index=False, float_format="%.4f")
    return t1


# ---------------- T2 恐慌签名 ----------------
def t2_vix(macro, ev):
    vix = macro["vix"]
    thr = vix.rolling(120, min_periods=60).quantile(0.80)
    rows = []
    for _, r in ev.iterrows():
        t0 = r["date"]
        if t0 not in vix.index:
            rows.append(dict(world=r["world"], date=t0, side=r["side"], vix=np.nan,
                             shock="无数据", status=""))
            continue
        v = float(vix.loc[t0])
        t = float(thr.loc[t0]) if t0 in thr.index and pd.notna(thr.loc[t0]) else np.nan
        cls = "恐慌" if (np.isfinite(t) and v >= t) else ("平静" if np.isfinite(t) else "无数据")
        status = "命中" if pd.notna(r["half_month"]) else ("进行中" if r["truncated"] else "未命中")
        rows.append(dict(world=r["world"], date=t0, side=r["side"], vix=v, shock=cls, status=status))
    t2 = pd.DataFrame(rows)
    print()
    print("=== T2 恐慌签名（VIX ≥ 滚动 10 年 P80 判为恐慌）===")
    for cls in ("恐慌", "平静"):
        sub = t2[t2.shock == cls]
        res = sub[sub.status != "进行中"]
        rate = (res.status == "命中").mean() if len(res) else np.nan
        print(f"  {cls}: {len(sub)} 个事件（可判定 {len(res)}），半程回归率 {rate:.1%}")
    print(f"  无数据（1990 前）: {(t2.shock == '无数据').sum()} 个")
    t2.to_csv(DATA / "t2_vix.csv", index=False, float_format="%.4f")
    return t2


def ols(y, x):
    X = np.column_stack([np.ones_like(x), np.asarray(x, float)])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n, k = X.shape
    s2 = resid @ resid / (n - k)
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    r2 = 1 - (resid @ resid) / ((y - y.mean()) @ (y - y.mean()))
    return beta, se, r2


# ---------------- T3 黄金重估 ----------------
def t3_gold(gl, macro):
    gold = gl["gold"]
    real10 = macro["real10"]
    df = pd.concat([np.log(gold).diff().rename("gr"),
                    real10.diff().rename("dr")], axis=1, join="inner").dropna()
    pre = df[df.index <= "2019-12-31"]
    post = df[df.index >= "2020-01-01"]
    out = {}
    for name, sub in (("2003–2019", pre), ("2020–2026", post)):
        b, se, r2 = ols(sub["gr"].to_numpy(), sub["dr"].to_numpy())
        out[name] = dict(beta=b[1], se=se[1], r2=r2, n=len(sub))
        print(f"=== T3 黄金 vs 实际利率 · {name} ===")
        print(f"  β(实际利率每 +1pp) = {b[1]:+.2f} ± {se[1]:.2f} ｜ R² = {r2:.2f} ｜ n = {len(sub)}")
    # 重估缺口：用 2003–2019 模型外推到 2020+
    b, se, r2 = ols(pre["gr"].to_numpy(), pre["dr"].to_numpy())
    a, beta = b[0], b[1]
    lvl_actual, lvl_impl = [], []
    g0 = float(gold.asof(pd.Timestamp("2019-12-31")))
    la, li = g0, g0
    for t, dr in post["dr"].items():
        la = float(gold.asof(t))
        li = li * float(np.exp(a + beta * dr))
        lvl_actual.append((t, la)); lvl_impl.append((t, li))
    ga = pd.Series(dict(lvl_actual), name="actual")
    gi = pd.Series(dict(lvl_impl), name="implied")
    gap = float(ga.iloc[-1] / gi.iloc[-1] - 1)
    print(f"  重估缺口（2026-08）：实际金价 {ga.iloc[-1]:.0f} vs 模型外推 {gi.iloc[-1]:.0f} → 超出 {gap:+.0%}")
    t3 = df.copy()
    t3.to_csv(DATA / "t3_gold.csv", float_format="%.4f")
    pd.DataFrame(
        [dict(period=k, beta=v["beta"], se=v["se"], r2=v["r2"], n=v["n"]) for k, v in out.items()]
        + [dict(period="重估缺口(2026-08)", beta=gap, se=np.nan, r2=np.nan, n=np.nan)]
    ).to_csv(DATA / "t3_results.csv", index=False, float_format="%.4f")
    return t3, ga, gi, out


# ---------------- 机制筛选器 v1.0 ----------------
def screen_row(t0, gm, gl, macro):
    gold, oil = gl["gold"], gm["brent"]
    tm = t0 - pd.DateOffset(months=12)
    dg = float(np.log(gold.asof(t0) / gold.asof(tm)))
    do = float(np.log(oil.asof(t0) / oil.asof(tm)))
    s1 = abs(do) > abs(dg)                     # 屏幕 1：油腿主导？
    vix = macro["vix"]
    thr = vix.rolling(120, min_periods=60).quantile(0.80)
    v, tv = float(vix.asof(t0)), float(thr.asof(t0)) if pd.notna(thr.asof(t0)) else np.nan
    s2 = np.isfinite(tv) and v >= tv           # 屏幕 2：恐慌签名？
    win = oil.loc[:t0].iloc[-120:]
    o = float(oil.asof(t0))
    pctl = float((win <= o).mean()) if len(win) >= 60 else np.nan
    s3 = np.isfinite(pctl) and pctl <= 0.25    # 屏幕 3：油价处于滚动 10 年低区（≤P25）？
    npass = int(s1) + int(s2) + int(s3)
    # v1.1 规则：恐慌签名（S2）为一票必要条件——回放显示纯计数会把 2014-12 误报为绿
    if s2 and npass >= 2:
        verdict = "绿：回归逻辑可用（仍需分仓与确认）"
    elif (s2 and npass <= 1) or ((not s2) and npass >= 2):
        verdict = "黄：观察区，暂不触发"
    else:
        verdict = "红：体制重定价候选，勿用回归逻辑"
    return dict(date=t0, d_gold=dg, d_oil=do, vix=v, vix_thr=tv, oil=o, oil_pctl=pctl,
                s1=s1, s2=s2, s3=s3, npass=npass, verdict=verdict)


def screener(gm, gl, macro):
    cases = {
        "2020-03 金油比（实际命中案例）": pd.Timestamp("2020-03-31"),
        "2014-12 金油比（实际失败案例）": pd.Timestamp("2014-12-31"),
        "2025-04 金油比（当前轮触发）": pd.Timestamp("2025-04-30"),
        "当前（2026-08 最新）": gm.index.max(),
    }
    rows = []
    print()
    print("=== 机制筛选器 v1.0 回放与当前 ===")
    for label, t0 in cases.items():
        r = screen_row(t0, gm, gl, macro)
        r["case"] = label
        rows.append(r)
        print(f"  {label}")
        print(f"    拆腿: 金 {r['d_gold']:+.0%} / 油 {r['d_oil']:+.0%} → {'油腿✓' if r['s1'] else '金腿✗'}"
              f" ｜ VIX {r['vix']:.1f}（阈值 {r['vix_thr']:.1f}）→ {'恐慌✓' if r['s2'] else '平静✗'}"
              f" ｜ 油分位 {r['oil_pctl']:.0%} → {'低位✓' if r['s3'] else '非低位✗'}")
        print(f"    → 通过 {r['npass']}/3 ｜ {r['verdict']}")
    scr = pd.DataFrame(rows)
    scr.to_csv(DATA / "screener.csv", index=False, float_format="%.4f")
    return scr


# ---------------- 图 ----------------
def fig_legs(t1):
    t1s = t1.sort_values(["world", "date"]).reset_index(drop=True)
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 8.4), gridspec_kw={"width_ratios": [2.3, 1]})
    ax = axes[0]
    y = np.arange(len(t1s))
    cg = (np.exp(t1s["d_gold"]) - 1) * 100
    co = (np.exp(-t1s["d_oil"]) - 1) * 100
    ax.barh(y + 0.19, cg, height=0.36, color=C_HI, alpha=0.85, label="金腿贡献")
    ax.barh(y - 0.19, co, height=0.36, color=C_LO, alpha=0.85, label="油腿贡献")
    mx = float(max(cg.max(), co.max()))
    ax.set_xlim(-8, mx * 1.30)
    labels = [f"{r['date']:%y-%m} {'Brent' if 'Brent' in r['world'] else 'WTI'}" for _, r in t1s.iterrows()]
    ax.set_yticks(y, labels, fontsize=7.5)
    for yi, (_, r) in enumerate(t1s.iterrows()):
        c = C_GREEN if r["status"] == "命中" else (C_G if r["status"] == "进行中" else "#95a5a6")
        ax.text(mx * 1.05, yi, r["status"], fontsize=7.5, va="center", color=c)
    ax.legend(loc="lower right", fontsize=9)
    ax.set_title("T1 · 每个金油比事件的腿部贡献（12 个月）与结局")
    ax.set_xlabel("对 GOR 变化的贡献（%，近似）")

    ax = axes[1]
    legs = ["油腿主导", "金腿主导"]
    rates, ns = [], []
    for leg in legs:
        sub = t1[t1.leg == leg]
        res = sub[sub.status != "进行中"]
        rates.append((res.status == "命中").mean() if len(res) else np.nan)
        ns.append(len(res))
    ax.bar(legs, rates, color=[C_LO, C_HI], alpha=0.88, width=0.55)
    for i, (r, n) in enumerate(zip(rates, ns)):
        ax.annotate(f"{r:.0%}\n(n={n})", xy=(i, r), ha="center", va="bottom", fontsize=10)
    ax.set_ylim(0, 1.12)
    ax.set_title("T1 · 半程回归率：油腿 vs 金腿")
    ax.set_ylabel("半程回归率")
    fig.tight_layout()
    fig.savefig(FIG / "fig1_legs.png", bbox_inches="tight")
    plt.close(fig)


def fig_vix(t2, macro):
    vix = macro["vix"]
    rows = t2[t2.shock != "无数据"].copy().reset_index(drop=True)
    pcts = []
    for _, r in rows.iterrows():
        w = vix.loc[:r["date"]].iloc[-120:]
        pcts.append(float((w <= r["vix"]).mean()))
    rows["pctl"] = pcts
    worlds = list(pd.unique(t2["world"]))
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2), gridspec_kw={"width_ratios": [2.2, 1]})
    ax = axes[0]
    rng = np.random.default_rng(5)
    for yi, wname in enumerate(worlds):
        sub = rows[rows.world == wname]
        for _, r in sub.iterrows():
            mk = "o" if r["status"] == "命中" else ("s" if r["status"] == "进行中" else "x")
            mk = "o" if r["status"] == "命中" else ("s" if r["status"] == "进行中" else "x")
            col = C_HI if r["shock"] == "恐慌" else C_LO
            jy = yi + rng.uniform(-0.12, 0.12)
            if r["status"] == "进行中":
                ax.scatter([r["pctl"] * 100], [jy], marker=mk, facecolors="none", edgecolors=col, s=40, zorder=5)
            else:
                ax.scatter([r["pctl"] * 100], [jy], marker=mk, color=col, s=40, zorder=5)
    ax.axvline(80, color=C_G, ls="--", lw=1)
    ax.annotate("恐慌线 P80", xy=(80, len(worlds) - 0.45), fontsize=9, color=C_G, ha="left")
    ax.set_yticks(range(len(worlds)), worlds)
    ax.set_xlabel("触发时 VIX 的滚动 10 年分位（%）；红=恐慌，蓝=平静；x=未命中，空心=进行中")
    ax.set_title("T2 · 事件触发时的恐慌签名")
    ax = axes[1]
    rates, ns = [], []
    for cls in ("恐慌", "平静"):
        sub = t2[t2.shock == cls]
        res = sub[sub.status != "进行中"]
        rates.append((res.status == "命中").mean() if len(res) else np.nan)
        ns.append(len(res))
    ax.bar(["恐慌", "平静"], rates, color=[C_HI, C_LO], alpha=0.88, width=0.5)
    for i, (r, n) in enumerate(zip(rates, ns)):
        ax.annotate(f"{r:.0%}\n(n={n})", xy=(i, r), ha="center", va="bottom", fontsize=10)
    ax.set_ylim(0, 1.12)
    ax.set_title("T2 · 半程回归率：恐慌 vs 平静")
    fig.tight_layout()
    fig.savefig(FIG / "fig2_vix.png", bbox_inches="tight")
    plt.close(fig)


def fig_gold(t3, ga, gi, res):
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.0))
    ax = axes[0]
    pre = t3[t3.index <= "2019-12-31"]
    post = t3[t3.index >= "2020-01-01"]
    ax.scatter(pre["dr"], pre["gr"] * 100, s=14, color=C_LO, alpha=0.6, label=f"2003–2019（β={res['2003–2019']['beta']:+.2f}）")
    ax.scatter(post["dr"], post["gr"] * 100, s=14, color=C_HI, alpha=0.6, label=f"2020–2026（β={res['2020–2026']['beta']:+.2f}）")
    for sub, c in ((pre, C_LO), (post, C_HI)):
        b, _, _ = ols(sub["gr"].to_numpy(), sub["dr"].to_numpy())
        xs = np.linspace(sub["dr"].min(), sub["dr"].max(), 20)
        ax.plot(xs, (b[0] + b[1] * xs) * 100, color=c, lw=1.6)
    ax.axhline(0, color="#bbb", lw=0.8); ax.axvline(0, color="#bbb", lw=0.8)
    ax.set_xlabel("10Y 实际利率的月度变化（pp）")
    ax.set_ylabel("金价月收益（%）")
    ax.set_title("T3 · 金价 vs 实际利率：两个时代")
    ax.legend(fontsize=8.5)
    ax = axes[1]
    ax.plot(ga.index, ga.values, lw=1.6, color=C_HI, label="实际金价")
    ax.plot(gi.index, gi.values, lw=1.6, color=C_G, ls="--", label="2003–2019 模型外推")
    ax.fill_between(ga.index, gi.values, ga.values, color=C_HI, alpha=0.12)
    ax.annotate(f"重估缺口\n{ga.iloc[-1] / gi.iloc[-1] - 1:+.0%}",
                xy=(ga.index[-1], ga.iloc[-1]), xytext=(-90, -18), textcoords="offset points",
                fontsize=9.5, color=C_HI,
                arrowprops=dict(arrowstyle="-", color=C_HI, lw=0.8))
    ax.set_title("T3 · 「重估缺口」：实际 vs 旧机制外推（2020–2026）")
    ax.legend(fontsize=8.5)
    fig.tight_layout()
    fig.savefig(FIG / "fig3_gold.png", bbox_inches="tight")
    plt.close(fig)


def main():
    setup_style()
    gm, gl, macro, ev = load_all()
    t1 = t1_legs(gm, gl, ev)
    t2 = t2_vix(macro, ev)
    t3, ga, gi, res = t3_gold(gl, macro)
    scr = screener(gm, gl, macro)
    fig_legs(t1); fig_vix(t2, macro); fig_gold(t3, ga, gi, res)

    lines = ["# 02 机制论证 · 结果摘要", ""]
    lines.append("## T1 拆腿分类")
    for leg in ("油腿主导", "金腿主导"):
        sub = t1[t1.leg == leg]
        r_ = sub[sub.status != "进行中"]
        lines.append(f"- {leg}: {len(sub)} 事件，可判定 {len(r_)}，半程回归率 "
                     f"{(r_.status == '命中').mean():.1%}")
    lines.append("")
    lines.append("## T2 恐慌签名")
    for cls in ("恐慌", "平静"):
        sub = t2[t2.shock == cls]
        r_ = sub[sub.status != "进行中"]
        lines.append(f"- {cls}: {len(sub)} 事件，可判定 {len(r_)}，半程回归率 "
                     f"{(r_.status == '命中').mean():.1%}")
    lines.append("")
    lines.append("## T3 黄金重估")
    for k, v in res.items():
        lines.append(f"- {k}: β = {v['beta']:+.2f}（se {v['se']:.2f}），R² = {v['r2']:.2f}，n = {v['n']}")
    lines.append(f"- 重估缺口（2026-08）：实际 {ga.iloc[-1]:.0f} vs 外推 {gi.iloc[-1]:.0f}"
                 f" → {ga.iloc[-1] / gi.iloc[-1] - 1:+.0%}")
    lines.append("")
    lines.append("## 筛选器回放")
    lines.append(scr[["case", "s1", "s2", "s3", "npass", "verdict"]].to_string(index=False))
    (DATA / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print()
    print("图已保存：figures/fig1_legs.png / fig2_vix.png / fig3_gold.png；摘要 data/summary.md")


if __name__ == "__main__":
    main()
