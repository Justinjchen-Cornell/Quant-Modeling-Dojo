# 延伸研究 03 · 事前注册 —— 先写规则，再看数据

> 「路径③ · 事前注册」：处理研究者自己——挑数据、事后编故事、只报赢的。

## 产出

- **报告（PDF，4 页）**：`报告-事前注册-先写规则再看数据.pdf`（脚本自动生成）
- **首张实卡（待签）**：`cards/注册卡-2026-09-17-GOR.md`（预测栏留白；填完 `git commit` 即冻结）
- 工具：`templates/注册卡模板.md`、`cards/台账.md`（尝试台账，已回填 8 行）
- 图：`figures/fig1_selection.png`、`fig2_walkforward.png`、`fig3_sparsity.png`
- 数据：`data/demo1_selection.csv`、`data/demo2_walkforward.csv`、`data/sparsity.csv`

## 关键结论（详见报告）

- 演示一（随机世界 × 400）：**40% 的"发现"能过 t>2**；同一规则样本外 t 归零（−0.09）、50% 变负、49% 无触发；
- 演示二（真实数据"发现→前向"）：阈值随时代漂移（30→32→46，贴着当时历史水位）；样本内 +126% 的"最优"前向只剩 +13%；前向大多 0–1 次触发；
- 开发中自查抓住一次**前视偏差**并修正——③ 存在的理由；
- 四件套：注册卡 / 前向检验 / 尝试台账 / 规则版本化（commit 即签署）。

## 复现

```bash
python scripts/analyze.py       # 两场演示 → data/ + figures/
python scripts/make_card.py     # 生成注册卡 → cards/
python scripts/build_report.py  # 生成 report.typ 并编译 PDF
```
