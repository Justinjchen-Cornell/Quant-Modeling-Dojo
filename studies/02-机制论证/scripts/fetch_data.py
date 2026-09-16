# -*- coding: utf-8 -*-
"""02 机制论证 · 数据抓取（VIX / 10Y 实际利率；其余复用 01 与 L1 数据）。

输出：data/macro_monthly.csv（date, vix, real10）
数据源：FRED VIXCLS（1990+）、DFII10（2003+），日频 → 月均，免密钥。
"""
from pathlib import Path
import io

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd=1990-01-01"


def fred_monthly_mean(sid: str) -> pd.Series:
    r = requests.get(FRED.format(sid=sid), timeout=60)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna().set_index("date")["value"].resample("ME").mean()


def main():
    print("[1/2] VIX（FRED VIXCLS，日频 → 月均）……")
    vix = fred_monthly_mean("VIXCLS").rename("vix")
    print("     ", len(vix), f"个月（{vix.index.min():%Y-%m} → {vix.index.max():%Y-%m}）")
    print("[2/2] 10Y 实际利率（FRED DFII10，日频 → 月均）……")
    real10 = fred_monthly_mean("DFII10").rename("real10")
    print("     ", len(real10), f"个月（{real10.index.min():%Y-%m} → {real10.index.max():%Y-%m}）")
    df = pd.concat([vix, real10], axis=1)
    df.index.name = "date"
    df.reset_index().to_csv(DATA / "macro_monthly.csv", index=False, float_format="%.4f")
    print("完成：data/macro_monthly.csv")


if __name__ == "__main__":
    main()
