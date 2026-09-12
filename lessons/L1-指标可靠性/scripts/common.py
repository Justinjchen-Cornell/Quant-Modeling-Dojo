# -*- coding: utf-8 -*-
"""L1 公共工具：路径 / 样式 / 数据加载 / 出图。

约定：
- matplotlib 缓存固定到课程目录（须先于 import matplotlib 设置）
- 所有图输出到 outputs/，PNG + PDF 双格式，300dpi
"""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]          # lessons/L1-指标可靠性
DATA = ROOT / "data"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))  # 必须在 import matplotlib 之前

import pandas as pd  # noqa: E402
import matplotlib    # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

C_MAIN, C_RED, C_AMBER, C_GREEN, C_GREY = "#2c3e50", "#c0392b", "#d68910", "#1e8449", "#7f8c8d"


def setup_style():
    plt.rcParams.update({
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "PingFang SC", "Noto Sans CJK SC", "Arial"],
        "axes.unicode_minus": False,
        "figure.dpi": 110,
        "savefig.dpi": 300,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.6,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
    })


def load_gor():
    """加载月度 GOR 数据（必要时现场重算 GOR 列）"""
    df = pd.read_csv(DATA / "gor_monthly.csv", parse_dates=["date"]).set_index("date").sort_index()
    if "gor_brent" not in df.columns:
        df["gor_brent"] = df["gold"] / df["brent"]
    if "gor_wti" not in df.columns:
        df["gor_wti"] = df["gold"] / df["wti"]
    return df


def save(fig, name):
    """PNG + PDF 双格式输出"""
    for ext in ("png", "pdf"):
        p = OUT / f"{name}.{ext}"
        fig.savefig(p, bbox_inches="tight")
        print(f"  已保存: {p.relative_to(ROOT.parent)}")
    plt.close(fig)
