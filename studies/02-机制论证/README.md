# 延伸研究 02 · 机制论证 ——「暂时错价」还是「体制重定价」？

> 「路径② · 机制论证」：用因果链与恐慌签名，给「回归逻辑」装一个筛选器。

## 产出

- **报告（PDF，4 页）**：`报告-机制论证-暂时错价还是体制重定价.pdf`（脚本自动生成）
- 图：`figures/fig1_legs.png`、`fig2_vix.png`、`fig3_gold.png`
- 数据：`data/t1_legs.csv`、`data/t2_vix.csv`、`data/t3_results.csv`、`data/screener.csv`

## 关键结论（详见报告）

- **恐惧是分水岭**：恐慌组半程回归 82.6%（n=23）vs 平静组 47.8%（n=23，≈随机）——① 的 1/3 失败几乎全部来自平静组；
- 拆腿分类预测不了结局（63% vs 71%）——是语义工具，不是预测工具；
- 黄金重估：β 没变（−0.10 → −0.09），水位 +135%（实际 4411 vs 旧机制外推 1879）；
- **机制筛选器 v1.1**：拆腿 + 恐慌签名（一票必要条件）+ 油迫近 → 绿/黄/红；回放 2020（绿 ✓）/ 2014（黄 ✓）/ 2025-04（黄）/ 当前（红）。

## 复现

```bash
python scripts/fetch_data.py    # VIX / 实际利率（其余复用 01 与 L1）
python scripts/analyze.py       # 三项检验 + 筛选器 → data/ + figures/
python scripts/build_report.py  # 生成 report.typ 并编译 PDF
```

## 数据源与口径

见报告；数据源：FRED（VIXCLS、DFII10），免密钥。
