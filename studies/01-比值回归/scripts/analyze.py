# -*- coding: utf-8 -*-
"""01 比值回归研究 · 事件分析（先定后验口径）。

口径：
- 极值：滚动 10 年（120 个月，最少 60）第 95 / 第 5 百分位
- 事件：首次穿越（前月不极端）；同侧事件间隔 >= 6 个月
- 回归判据（24 个月窗口，触发时冻结滚动中位数为目标）：
    半程回归 = 朝中位数走完 50% 距离；完全回归 = 触及中位数
- 先恶化 = 回归前继续远离中位数的最大幅度（相对触发值）
- 随机基准 = 该世界自身月度变化做 12 个月块自助抽样（1000 条路径）

输出：data/events.csv、data/world_stats.csv、data/summary.md、figures/*.png
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

WIN, MINP = 120, 60
P_HI, P_LO = 0.95, 0.05
HORIZON = 24
GAP_DAYS = 180
N_SIM, BLOCK = 1000, 12

C_HI, C_LO, C_G = "#c0392b", "#2471a3", "#7f8c8d"


def setup_style():
    plt.rcParams.update({
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial"],
        "axes.unicode_minus": False,
        "figure.dpi": 110, "savefig.dpi": 300,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
        "axes.titlesize": 11, "axes.labelsize": 10,
    })


def load_worlds():
    l1 = ROOT.parents[1] / "lessons" / "L1-指标可靠性" / "data"
    gm = pd.read_csv(l1 / "gor_monthly.csv", parse_dates=["date"]).set_index("date").sort_index()
    gl = pd.read_csv(l1 / "gor_long.csv", parse_dates=["date"]).set_index("date").sort_index()
    sv = pd.read_csv(DATA / "silver_monthly.csv", parse_dates=["date"]).set_index("date").sort_index()
    cu = pd.read_csv(DATA / "copper_monthly.csv", parse_dates=["date"]).set_index("date").sort_index()
    cu.index = cu.index + pd.offsets.MonthEnd(0)  # FRED 月频为月初，统一到月末以对齐
    cr = pd.read_csv(DATA / "credit_monthly.csv", parse_dates=["date"]).set_index("date").sort_index()

    w = {}
    w["金油比·Brent"] = gm["gor_brent"].dropna()
    wti = (gl["gold"] / gl["wti"]).dropna()
    w["金油比·WTI"] = wti[wti.index >= "1971-01-01"]
    w["金银比"] = (gl["gold"] / sv["silver"]).dropna()
    w["铜金比"] = (cu["copper"] / gl["gold"]).dropna()
    w["信用利差·Baa-10Y"] = cr["credit"].dropna()
    return w


def find_events(idx, cond):
    ev, state, last_end = [], False, None
    for i, t in enumerate(idx):
        c = bool(cond[i])
        if c and not state:
            if last_end is None or (t - last_end).days >= GAP_DAYS:
                ev.append(t)
            state = True
        elif (not c) and state:
            state = False
            last_end = t
    return ev


def sim_half_prob(logret, L0, M0, side):
    rng = np.random.default_rng(7)
    nb = HORIZON // BLOCK
    starts = rng.integers(0, len(logret) - BLOCK, size=(N_SIM, nb))
    seg = np.stack([logret[s:s + BLOCK] for s in starts.flatten()]).reshape(N_SIM, HORIZON)
    lv = L0 * np.exp(np.cumsum(seg, axis=1))
    if side == "高":
        return float((lv <= L0 - 0.5 * (L0 - M0)).any(axis=1).mean())
    return float((lv >= L0 + 0.5 * (M0 - L0)).any(axis=1).mean())


def analyze_world(name, s):
    idx = s.index
    roll_med = s.rolling(WIN, min_periods=MINP).median()
    roll_hi = s.rolling(WIN, min_periods=MINP).quantile(P_HI)
    roll_lo = s.rolling(WIN, min_periods=MINP).quantile(P_LO)
    logret_all = np.log(s).diff().dropna().to_numpy()
    rows = []
    for side, cond_s in (("高", s >= roll_hi), ("低", s <= roll_lo)):
        cond = cond_s.fillna(False).to_numpy()
        for t0 in find_events(idx, cond):
            L0, M0 = float(s.loc[t0]), float(roll_med.loc[t0])
            if not np.isfinite(M0) or L0 == M0:
                continue
            end = t0 + pd.DateOffset(months=HORIZON)
            win = s.loc[t0:end]
            after = win.iloc[1:]
            truncated = s.index.max() < end
            if side == "高":
                hit_half = (after <= L0 - 0.5 * (L0 - M0)).to_numpy()
                hit_full = (after <= M0).to_numpy()
                adverse = float(win.max() / L0 - 1.0)
            else:
                hit_half = (after >= L0 + 0.5 * (M0 - L0)).to_numpy()
                hit_full = (after >= M0).to_numpy()
                adverse = float(win.min() / L0 - 1.0)
            hp = int(np.argmax(hit_half) + 1) if hit_half.any() else np.nan
            fp = int(np.argmax(hit_full) + 1) if hit_full.any() else np.nan
            ret12 = float(win.iloc[12] / L0 - 1.0) if len(win) > 12 else np.nan
            ret24 = float(win.iloc[24] / L0 - 1.0) if len(win) > 24 else np.nan
            rows.append(dict(
                world=name, side=side, date=t0, level=L0, median=M0,
                gap=(L0 - M0) / M0, half_month=hp, full_month=fp,
                ret12=ret12, ret24=ret24, adverse=adverse, truncated=truncated,
                sim_half=sim_half_prob(logret_all, L0, M0, side),
            ))
    return rows


def main():
    setup_style()
    worlds = load_worlds()
    all_rows = []
    for name, s in worlds.items():
        rows = analyze_world(name, s)
        all_rows += rows
        print(f"== {name} ==  样本 {s.index.min():%Y-%m} 至 {s.index.max():%Y-%m}（{len(s)} 个月），事件 {len(rows)} 个")
        for r in rows:
            hp = "-" if np.isnan(r["half_month"]) else str(int(r["half_month"]))
            stat = "命中" if not np.isnan(r["half_month"]) else ("进行中" if r["truncated"] else "未命中")
            d = r["date"]
            print(f"   {d:%Y-%m} [{r['side']}] 触发 {r['level']:.2f}（中位 {r['median']:.2f}）"
                  f" 半程 {hp} 月（{stat}） 先恶化 {r['adverse']:+.0%} 随机基准 {r['sim_half']:.0%}")

    ev = pd.DataFrame(all_rows)
    ev.to_csv(DATA / "events.csv", index=False, float_format="%.4f")

    stats = []
    for name in worlds:
        e = ev[ev.world == name]
        resolvable = e[~e.truncated | e.half_month.notna()]
        hits = resolvable[resolvable.half_month.notna()]
        full_hits = resolvable[resolvable.full_month.notna()]
        stats.append(dict(
            world=name,
            years=f"{worlds[name].index.min():%Y}–{worlds[name].index.max():%Y}",
            n=len(e), n_hi=int((e.side == "高").sum()), n_lo=int((e.side == "低").sum()),
            n_resolved=len(resolvable), half_hits=len(hits),
            half_rate=(len(hits) / len(resolvable)) if len(resolvable) else np.nan,
            median_half_month=float(hits.half_month.median()) if len(hits) else np.nan,
            full_rate=(len(full_hits) / len(resolvable)) if len(resolvable) else np.nan,
            median_adverse=float(resolvable.adverse.median()) if len(resolvable) else np.nan,
            sim_half_mean=float(resolvable.sim_half.mean()) if len(resolvable) else np.nan,
            n_pending=int(e.truncated.sum() - e[e.truncated].half_month.notna().sum()),
        ))
    st = pd.DataFrame(stats)
    ra = ev[~ev.truncated | ev.half_month.notna()]
    ha = ra[ra.half_month.notna()]
    st.loc[len(st)] = dict(
        world="全部（合并池）", years="1986–2026", n=len(ev),
        n_hi=int((ev.side == "高").sum()), n_lo=int((ev.side == "低").sum()),
        n_resolved=len(ra), half_hits=len(ha),
        half_rate=len(ha) / len(ra),
        median_half_month=float(ha.half_month.median()),
        full_rate=float(ra.full_month.notna().mean()),
        median_adverse=float(ra.adverse.median()),
        sim_half_mean=float(ra.sim_half.mean()),
        n_pending=int(ev.truncated.sum() - ev[ev.truncated].half_month.notna().sum()),
    )
    st.to_csv(DATA / "world_stats.csv", index=False, float_format="%.4f")
    print()
    print("=== 世界统计 ===")
    print(st.to_string(index=False))
    print()

    lines = ["# 01 比值回归 · 结果摘要", ""]
    lines.append(st.to_string(index=False))
    lines.append("")
    lines.append("## 事件明细")
    lines.append("")
    lines.append(ev.to_string(index=False))
    (DATA / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("已保存: data/events.csv, data/world_stats.csv, data/summary.md")


    # ===== 图 1：五个世界 =====
    fig, axes = plt.subplots(3, 2, figsize=(12.5, 10.5))
    axes = axes.flatten()
    for k, (name, s) in enumerate(worlds.items()):
        ax = axes[k]
        ax.plot(s.index, s.values, lw=1.1, color="#2c3e50")
        e = ev[ev.world == name]
        for _, r in e.iterrows():
            ax.scatter([r["date"]], [r["level"]], marker="v" if r.side == "高" else "^",
                       s=42, color=C_HI if r.side == "高" else C_LO, zorder=5)
        ax.set_yscale("log")
        ax.margins(y=0.12)
        nh = int((e.side == "高").sum()); nl = int((e.side == "低").sum())
        ax.set_title(f"{name}（事件 {len(e)}：高 {nh} / 低 {nl}）")
    for k in range(len(worlds), len(axes)):
        axes[k].axis("off")
    fig.suptitle("五个平行世界的比值史与极端事件（下三角=极端高，上三角=极端低）", y=0.995)
    fig.tight_layout()
    fig.savefig(FIG / "fig1_worlds.png", bbox_inches="tight")
    plt.close(fig)

    # ===== 图 2：事件结果条带 =====
    order = list(worlds.keys())[::-1]
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.4))
    rng = np.random.default_rng(3)
    for ax, col in ((axes[0], "half_month"), (axes[1], "adverse")):
        for yi, name in enumerate(order):
            e = ev[ev.world == name]
            for _, r in e.iterrows():
                c = C_HI if r.side == "高" else C_LO
                dy = 0.14 if r.side == "高" else -0.14
                if col == "half_month":
                    if np.isnan(r["half_month"]):
                        x = 24.4
                        mk = "s" if r.truncated else "x"
                        if r.truncated:
                            ax.scatter([x], [yi + dy], marker=mk, facecolors="none",
                                       edgecolors=c, s=38, zorder=6)
                        else:
                            ax.scatter([x], [yi + dy], marker=mk, color=c, s=38, zorder=6)
                    else:
                        ax.scatter([r["half_month"]], [yi + dy], marker="o", color=c, s=38, zorder=6)
                else:
                    x = r["adverse"] * 100
                    ax.scatter([x], [yi + dy + rng.uniform(-0.04, 0.04)], marker="o",
                               color=c, s=32, alpha=0.85)
        if col == "half_month":
            ax.axvline(12, color=C_G, lw=1, ls="--")
            ax.axvline(24, color=C_G, lw=1, ls="--")
            ax.set_xlim(0, 27)
            ax.set_xlabel("半程回归用时（月）；x = 期内未回归，空心方块 = 仍在观察期")
        else:
            ax.axvline(0, color=C_G, lw=1, ls="--")
            ax.set_xlabel("回归前最大反向偏移（%）")
        ax.set_yticks(range(len(order)), order)
    axes[1].annotate("2020 金油比·WTI：先恶化 +222%", xy=(222, 3.14), xytext=(95, 4.18),
                     fontsize=9, color=C_HI,
                     arrowprops=dict(arrowstyle="-", color=C_HI, lw=0.8))
    fig.suptitle("事件结果条带：红 = 极端高 / 蓝 = 极端低", y=1.0)
    fig.tight_layout()
    fig.savefig(FIG / "fig2_outcomes.png", bbox_inches="tight")
    plt.close(fig)

    # ===== 图 3：实际 vs 随机基准 =====
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    names = list(worlds.keys())
    x = np.arange(len(names))
    actual = [float(st.loc[st.world == n, "half_rate"].iloc[0]) for n in names]
    simv = [float(st.loc[st.world == n, "sim_half_mean"].iloc[0]) for n in names]
    ax.bar(x - 0.19, actual, width=0.36, color="#c0392b", alpha=0.88, label="极端事件后（实际）")
    ax.bar(x + 0.19, simv, width=0.36, color="#95a5a6", alpha=0.9, label="随机基准（块自助 1000 条路径）")
    for xi in range(len(names)):
        ax.annotate(f"{actual[xi]:.0%}", xy=(xi - 0.19, actual[xi]), ha="center", va="bottom", fontsize=9)
        ax.annotate(f"{simv[xi]:.0%}", xy=(xi + 0.19, simv[xi]), ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x, names)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("24 个月半程回归概率")
    ax.set_title("极端之后 vs 随机游走：回归概率对比")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "fig3_vs_random.png", bbox_inches="tight")
    plt.close(fig)
    print("图已保存：figures/fig1_worlds.png / fig2_outcomes.png / fig3_vs_random.png")


if __name__ == "__main__":
    main()
