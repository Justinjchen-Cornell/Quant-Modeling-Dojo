# -*- coding: utf-8 -*-
"""抓取/刷新 L1 数据：金价 + 布伦特/WTI（月度）。

数据源（公开、免密钥）：
- 金价：datahub.io 月度金价（LBMA，1833 年起，月均值）
- 油价：FRED CSV（DCOILBRENTEU / DCOILWTICO，1986 年起），日频 → 月均值

输出：data/gor_monthly.csv（date, gold, brent, wti, gor_brent, gor_wti）
口径：全部为"月均值"；只保留已结束的月份（不含当月进行中数据）。
用法：python scripts/fetch_data.py
"""
import sys
import io
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "gor_monthly.csv"

GOLD_URL = "https://datahub.io/core/gold-prices/r/monthly.csv"
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"


def gold_datahub() -> pd.Series:
    """datahub.io 月度金价（LBMA）"""
    r = requests.get(GOLD_URL, timeout=60)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = ["date", "gold"]
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m") + pd.offsets.MonthEnd(0)
    return df.dropna().set_index("date")["gold"].astype(float)


def gold_yahoo_chunked() -> pd.Series:
    """备用：Yahoo GC=F 分段日线合成月线（Yahoo range=max 会返回残缺数据，必须分段）"""
    import datetime as dt
    frames = []
    for a, b in (("2000-01-01", "2012-01-01"), ("2012-01-01", "2030-01-01")):
        r = requests.get(
            "https://query1.finance.yahoo.com/v8/finance/chart/GC=F",
            params={"period1": int(dt.datetime.fromisoformat(a).timestamp()),
                    "period2": int(dt.datetime.fromisoformat(b).timestamp()),
                    "interval": "1d"},
            headers={"User-Agent": "Mozilla/5.0"}, timeout=30,
        )
        r.raise_for_status()
        j = r.json()["chart"]["result"][0]
        s = pd.Series(j["indicators"]["quote"][0]["close"],
                      index=pd.to_datetime(j["timestamp"], unit="s"))
        frames.append(s.dropna())
    s = pd.concat(frames)
    s.name = "gold"
    return s.resample("ME").mean()


def gold_akshare() -> pd.Series:
    """备用 2：akshare COMEX 黄金日线（2016 年起）"""
    import akshare as ak
    d = ak.futures_foreign_hist(symbol="GC")
    s = pd.Series(d["close"].values, index=pd.to_datetime(d["date"]), name="gold")
    return s.resample("ME").mean()


def fred_monthly_mean(sid: str) -> pd.Series:
    """FRED 日频 → 月均值"""
    r = requests.get(FRED_URL.format(sid=sid), timeout=30)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    s = df.dropna().set_index("date")["value"].resample("ME").mean()
    s.name = sid
    return s


def main() -> int:
    print("[1/3] 金价（datahub / LBMA）……")
    gold = None
    for name, fn in (("datahub", gold_datahub), ("Yahoo 分段", gold_yahoo_chunked), ("akshare", gold_akshare)):
        try:
            gold = fn()
            print(f"      {name} 成功：{len(gold)} 个月（{gold.index.min():%Y-%m} → {gold.index.max():%Y-%m}）")
            break
        except Exception as e:  # noqa: BLE001
            print(f"      {name} 失败：{type(e).__name__} {str(e)[:80]}")
    if gold is None:
        print("金价数据源全部失败，保留现有 CSV 不覆盖。")
        return 1

    print("[2/3] FRED：布伦特 + WTI 油价（月均值）……")
    brent = fred_monthly_mean("DCOILBRENTEU").rename("brent")
    wti = fred_monthly_mean("DCOILWTICO").rename("wti")

    df = pd.concat([gold, brent, wti], axis=1).dropna()
    # 只保留已结束的月份（去掉进行中的当月）
    now_month = pd.Timestamp.now().to_period("M")
    df = df[df.index.to_period("M") < now_month]
    df = df.reset_index()
    df = df.rename(columns={df.columns[0]: "date"})
    df["gor_brent"] = df["gold"] / df["brent"]
    df["gor_wti"] = df["gold"] / df["wti"]
    df = df[["date", "gold", "brent", "wti", "gor_brent", "gor_wti"]]

    print(f"[3/3] 保存：{OUT}")
    df.to_csv(OUT, index=False, float_format="%.4f")
    print(f"      共 {len(df)} 行（{df['date'].min():%Y-%m} → {df['date'].max():%Y-%m}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
