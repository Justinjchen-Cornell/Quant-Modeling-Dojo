# -*- coding: utf-8 -*-
"""01 比值回归研究 · 数据抓取（银 / 铜 / HY 利差；金与油复用 L1 数据）。

输出（data/）：
  silver_monthly.csv  ← Yahoo SI=F（COMEX 银期货，分段日线→月均，2000+）
  copper_monthly.csv  ← FRED PCOPPUSDM（全球铜价，月频，1992+，美元/吨）
  credit_monthly.csv  ← FRED BAA10Y（穆迪 Baa - 10Y 国债利差，日频→月均，1986+）
                        （原计划 HY OAS 因 ICE 下载限制改用 Baa-10Y，同为信用利差）
依赖：lessons/L1-指标可靠性/data/（gor_monthly.csv、gor_long.csv）
"""
from pathlib import Path
import io
import datetime as dt

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]          # studies/01-比值回归
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
L1 = ROOT.parents[1] / "lessons" / "L1-指标可靠性" / "data"

FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd=1990-01-01"


def save_series(s: pd.Series, name: str):
    out = DATA / f"{name}_monthly.csv"
    df = s.reset_index()
    df.columns = ["date", name]
    df.to_csv(out, index=False, float_format="%.4f")
    print(f"     {name}: {len(s)} 个月（{s.index.min():%Y-%m} → {s.index.max():%Y-%m}）→ {out.name}")


def fred_series(sid: str, resample_mean: bool = False) -> pd.Series:
    r = requests.get(FRED.format(sid=sid), timeout=60)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    s = df.dropna().set_index("date")["value"]
    if resample_mean:
        s = s.resample("ME").mean()
    return s


def silver_yahoo() -> pd.Series:
    frames = []
    for a, b in (("2000-01-01", "2012-01-01"), ("2012-01-01", "2030-01-01")):
        r = requests.get(
            "https://query1.finance.yahoo.com/v8/finance/chart/SI=F",
            params={"period1": int(dt.datetime.fromisoformat(a).timestamp()),
                    "period2": int(dt.datetime.fromisoformat(b).timestamp()),
                    "interval": "1d"},
            headers={"User-Agent": "Mozilla/5.0"}, timeout=40,
        )
        r.raise_for_status()
        j = r.json()["chart"]["result"][0]
        s = pd.Series(j["indicators"]["quote"][0]["close"],
                      index=pd.to_datetime(j["timestamp"], unit="s")).dropna()
        frames.append(s)
    s = pd.concat(frames)
    s.name = "silver"
    return s.resample("ME").mean().dropna()


def main():
    assert (L1 / "gor_monthly.csv").exists(), "缺少 L1 数据：请先运行 lessons/L1-指标可靠性/scripts/fetch_data.py"
    print("[1/3] 银价（Yahoo SI=F，分段日线 → 月均）……")
    save_series(silver_yahoo(), "silver")
    print("[2/3] 铜价（FRED PCOPPUSDM，月频）……")
    save_series(fred_series("PCOPPUSDM"), "copper")
    print("[3/3] 信用利差（FRED BAA10Y，日频 → 月均，1986+）……")
    save_series(fred_series("BAA10Y", resample_mean=True), "credit")
    print("完成。")


if __name__ == "__main__":
    main()
