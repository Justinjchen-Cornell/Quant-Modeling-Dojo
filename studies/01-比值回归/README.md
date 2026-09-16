# 延伸研究 01 · 比值型估值指标的均值回归

> 「路径① · 跨体制样本」第一步：把「金油比 45」抽象成现象类，在 5 个平行世界中收集 55 个极端事件。

## 产出

- **报告（PDF，6 页）**：`报告-比值型指标均值回归研究.pdf`（由脚本自动生成）
- 图：`figures/fig1_worlds.png`、`fig2_outcomes.png`、`fig3_vs_random.png`
- 数据：`data/events.csv`（55 事件明细）、`data/world_stats.csv`（分世界统计）

## 关键结论（详见报告）

- 合并池 55 事件：**半程回归 64.7%** vs 随机基准 52.1%（+13pp）——现象存在，但只是中等强度的倾向；
- 命中事件中位 **6 个月**；完全回归仅 37.2%；**约 1/3 未回归**（多为「体制重定价」）；
- 「先恶化」是主要成本：2020 金油比 +84%（WTI 口径 **+222%**）才折返；
- 对 GOR 45 的校准：≈ 65% 命中 / 中位 6 个月 / 1/3 失败 / 尾部先恶化 2–3 倍。

## 复现

```bash
python scripts/fetch_data.py    # 抓取银/铜/信用利差（金、油复用 L1 数据）
python scripts/analyze.py       # 事件研究 → data/ + figures/
python scripts/build_report.py  # 生成 report.typ 并编译 PDF
```

## 数据源与口径

见报告第 2 节（先定后验声明在内）。数据源：FRED / datahub.io / Yahoo，全部免密钥。
