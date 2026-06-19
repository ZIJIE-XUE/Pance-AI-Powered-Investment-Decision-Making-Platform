# ⛰️ 磐策 PánCè — AI 智能投资决策平台

> **稳如磐石 · 策定乾坤** &nbsp;|&nbsp; *Steady as a Rock · Strategic Foresight*

AI 驱动的个人智能投顾（Robo Advisor）系统。核心创新：**将市场估值温度信号引入定投策略**——市场冷时多投、热时少投，经回测验证、样本外检验、行为金融学论证。

🌐 [pancealpha.tech](https://pancealpha.tech)（Render + Alibaba Cloud 域名）&nbsp;|&nbsp; 支持中英双语切换

---

## 🎯 项目定位

一个融合**量化金融、行为经济学与全栈工程**的 AI 投顾系统。五层分析框架（回测 → 信号验证 → Walk-Forward → 环境分解 → 行为金融）将策略评估从"跑个回测"深化为有方法论支撑的量化研究。

---

## 🌡️ 旗舰功能：智能温度定投

| 指标 | 🌡️ 温度定投 | 📋 普通定投 | 💰 一次性买入 |
|------|:----------:|:----------:|:----------:|
| 年化收益 | **19.3%** | 7.2% | 13.7% |
| 最大回撤 | **-0.9%** | -2.0% | -7.9% |
| 夏普比率 | **1.39** | 0.71 | 0.71 |

> 沪深300 · 3年回测 · 适中策略。温度定投比普通定投年化高 12 个百分点，回撤仅为一次性买入的 1/9。

**工作原理**：实时 PE 估值 + 200 日均线偏离 → 市场温度 0-100°C。低温多投（最高 2.0x）、适中正常、高温少投（最低 0x），资金在高低温区间自动调配。

**五层分析框架**：

| # | 层次 | 问题 | 方法 |
|:--:|------|------|------|
| 1 | 回测 | 策略有效吗？ | 三策略模拟 + 现金池动态 |
| 2 | 信号验证 | 温度能预测收益吗？ | Pearson r + 分桶回归 |
| 3 | Walk-Forward | 是过拟合吗？ | 训练窗网格搜索 → 样本外单次检验 |
| 4 | 环境分解 | 什么时候有效？ | 牛/熊/震荡市分别对比 |
| 5 | 行为金融 | 为什么有效？ | 克服损失厌恶、羊群效应、锚定效应 |

---

## ✨ 全部功能

| 模块 | 功能 |
|------|------|
| 🌡️ **温度定投** | 实时温度 · 动态倍率 · 回测对比 · 信号验证 · Walk-Forward · 环境分解 · 行为金融论证 |
| 🎯 **风险测评** | 12 题问卷 · 5 级风险 · 多市场覆盖（A股/港股/美股/韩国） |
| 📊 **组合优化** | 两级优化（风险权重 + PyPortfolioOpt 均值方差）· 36 只 ETF |
| 🔮 **Monte Carlo** | GBM 万条路径 · VaR/CVaR · 5/10/20 年收益分布 |
| 🤖 **AI 分析** | 本地引擎即时分析 · 配置理由 · 风险识别 · 市场情景 · 投资建议 |
| 📄 **PDF 报告** | 7 章专业报告 · Plotly 图表嵌入 |
| 📊 **市场仪表盘** | 实时行情 · 行业热力图 · 宏观指标 · ETF 涨跌榜 · ETF 对比工具 |
| 🌡️ **市场温度计** | 四大指数 PE 估值 + 均线偏离温度 |
| 💰 **定投计算器** | 正算（月投→终值）/ 反算（目标→月投） |
| 📚 **术语百科** | 75 个中英双语金融术语 · 搜索 + 分类筛选 |
| 🌐 **中英双语** | 全站 i18n · ~580 条翻译 · 一键切换 |

---

## 🛠️ 技术栈

| 层 | 技术 |
|------|------|
| **框架** | Streamlit（12 页 MPA） |
| **数据** | Pandas, NumPy, AKShare（新浪/中证/东方财富）, Yahoo Finance |
| **可视化** | Plotly（交互）, Matplotlib（报告） |
| **统计** | SciPy（Pearson r, 假设检验）, NumPy（线性回归） |
| **优化** | PyPortfolioOpt（均值-方差） |
| **数据库** | SQLAlchemy ORM + SQLite |
| **PDF** | ReportLab + Plotly 嵌入 |
| **配置** | Pydantic Settings + YAML |
| **i18n** | 自建翻译字典 ~580 条 |
| **部署** | Render PaaS + Alibaba Cloud DNS + Git Push 自动部署 |

**规模**：61 个 Python 文件 · 13,000+ 行 · 12 个页面 · 全部数据源免费

---

## 🏗️ 架构

```
pance/
├── config/                     # Pydantic 配置, YAML 策略权重, 术语库
├── src/
│   ├── engine/                 # 纯计算引擎（零 Streamlit 依赖）
│   │   ├── temperature_dca_engine.py  # 🌡️ 回测 + 信号验证 + Walk-Forward
│   │   ├── market_thermometer.py      # PE 估值 + 均线偏离温度
│   │   ├── optimizer.py               # 两级组合优化
│   │   ├── monte_carlo.py             # GBM Monte Carlo
│   │   ├── market_data.py             # 多源行情管线
│   │   └── data_provider.py           # 多市场 ETF 数据
│   ├── services/               # 业务逻辑编排
│   ├── reports/                # PDF 报告生成
│   └── ui/                     # Streamlit 前端
│       ├── i18n.py             # 中英双语翻译系统
│       ├── pages/              # 12 个功能页面
│       └── components/         # 卡片式侧边栏、图表、问卷
└── tests/                      # 单元测试
```

**设计原则**：计算（engine/）与展示（ui/）严格分离，所有金融计算可脱离 Streamlit 独立测试。

---

## ⚠️ 免责声明

本系统仅供学习和研究目的。所有投资分析仅供参考，**不构成投资建议**。历史回测不代表未来收益。投资有风险，入市需谨慎。

---

© 2026 磐策 PánCè · Built by **Jason (ZIJIE-XUE)**

---

---

# 🇬🇧 English

## ⛰️ PánCè — AI-Powered Investment Platform

> *Steady as a Rock · Strategic Foresight*

A full-stack AI Robo Advisor for individual investors. **Core innovation**: a Temperature-Driven DCA engine that dynamically adjusts monthly investments based on real-time market valuation signals — backed by backtesting, out-of-sample validation, and behavioral finance theory.

🌐 [pancealpha.tech](https://pancealpha.tech) (Render + Alibaba Cloud) &nbsp;|&nbsp; Bilingual CN/EN

---

## 🎯 Positioning

PánCè integrates **quantitative finance, behavioral economics, and full-stack engineering**. Its five-layer analytical framework (backtest → signal validation → walk-forward → regime decomposition → behavioral finance) elevates strategy evaluation from "running a backtest" to methodologically grounded quantitative research.

---

## 🌡️ Flagship: Temperature-Driven DCA

| Metric | 🌡️ Temp DCA | 📋 Regular DCA | 💰 Lump Sum |
|--------|:-----------:|:-------------:|:----------:|
| CAGR | **19.3%** | 7.2% | 13.7% |
| Max Drawdown | **-0.9%** | -2.0% | -7.9% |
| Sharpe Ratio | **1.39** | 0.71 | 0.71 |

> CSI 300 · 3-year backtest · moderate strategy. Temp DCA outperforms regular DCA by 12pp annually with 1/9 the drawdown of lump sum.

**How it works**: PE valuation + 200-day MA deviation → market temperature 0–100°C. Cold → 1.25–2.0× (buy more) · Fair → 1.0× · Hot → 0–0.75× (buy less). Surpluses from hot periods are automatically redeployed when markets cool.

**Five-Layer Framework**:

| # | Layer | Question | Method |
|:--:|--------|----------|--------|
| 1 | Backtest | Does it work historically? | 3-strategy simulation + cash pool |
| 2 | Signal Validation | Does temperature predict returns? | Pearson r + quintile regression |
| 3 | Walk-Forward | Is it overfitting? | Grid search → single OOS test |
| 4 | Regime Decomposition | When does it win/lose? | Bull/bear/sideways breakdown |
| 5 | Behavioral Finance | Why should it work? | Rules-based intervention against cognitive biases |

---

## ✨ Features

| Module | Details |
|--------|---------|
| 🌡️ **Temperature DCA** | Real-time temperature · dynamic multiplier · backtest · signal validation · walk-forward · regime decomposition · behavioral finance |
| 🎯 **Risk Assessment** | 12-question quiz · 5 risk levels · multi-market (CN/HK/US/KR) |
| 📊 **Portfolio Opt.** | Two-stage: risk weights + PyPortfolioOpt mean-variance · 36 ETFs |
| 🔮 **Monte Carlo** | 10K GBM paths · VaR/CVaR · 5/10/20-year projections |
| 🤖 **AI Analysis** | Local engine · allocation rationale · risk ID · market scenarios |
| 📄 **PDF Report** | 7-chapter professional report with Plotly charts |
| 📊 **Dashboard** | Live quotes · sector heatmap · macro indicators · ETF rankings · ETF comparison |
| 🌡️ **Thermometer** | PE valuation + MA deviation for 4 major A-share indices |
| 💰 **DCA Calculator** | Forward (invest → future value) / reverse (goal → monthly) |
| 📚 **Glossary** | 75 bilingual financial terms · search + category filter |
| 🌐 **i18n** | ~580 translations · one-click CN/EN toggle across all pages |

---

## 🛠️ Tech Stack

| Layer | Technologies |
|------|-------------|
| **Framework** | Streamlit (12-page MPA) |
| **Data** | Pandas, NumPy, AKShare, Yahoo Finance |
| **Visualization** | Plotly, Matplotlib |
| **Statistics** | SciPy, NumPy |
| **Optimization** | PyPortfolioOpt |
| **Database** | SQLAlchemy ORM + SQLite |
| **PDF** | ReportLab + Plotly embedding |
| **Config** | Pydantic + YAML |
| **i18n** | Custom dictionary (~580 entries) |
| **Deployment** | Render PaaS + Alibaba Cloud DNS + CI/CD |

**Scale**: 61 Python files · 13,000+ lines · 12 pages · 100% free data sources

---

## 🏗️ Architecture

```
pance/
├── config/                    # Pydantic settings, YAML weights, glossary
├── src/
│   ├── engine/                # Pure computation (zero Streamlit dependency)
│   │   ├── temperature_dca_engine.py  # 🌡️ Backtest + validation + walk-forward
│   │   ├── market_thermometer.py      # Temperature signal computation
│   │   ├── optimizer.py               # Two-stage portfolio optimization
│   │   ├── monte_carlo.py             # GBM Monte Carlo
│   │   └── market_data.py             # Multi-source data pipeline
│   ├── services/              # Business logic orchestration
│   └── ui/                    # Streamlit frontend
│       ├── i18n.py            # CN/EN translation system
│       ├── pages/             # 12 functional pages
│       └── components/        # Card sidebar, charts, questionnaire
└── tests/                     # Unit tests
```

**Design**: engine/ and ui/ are strictly separated. All financial computation is independently testable.

---

## ⚠️ Disclaimer

This system is for **educational and research purposes only**. All investment analysis is for reference only and **does not constitute investment advice**. Past performance does not guarantee future results.

---

Built by **Jason (ZIJIE-XUE)** · 2026
