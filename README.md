# ⛰️ 磐策 PánCè — AI 智能投资决策平台

> **稳如磐石 · 策定乾坤**

面向个人投资者的 AI 驱动智能投顾（Robo Advisor）系统。核心创新：**将市场估值温度信号引入定投策略**——市场冷时多投、热时少投，历史回测验证策略有效性。

---

## 🌡️ 旗舰功能：智能温度定投

| 指标 | 🌡️ 温度定投 | 📋 普通定投 | 💰 一次性买入 |
|------|:----------:|:----------:|:----------:|
| 年化收益 | **19.3%** | 7.2% | 13.7% |
| 最大回撤 | **-0.9%** | -2.0% | -7.9% |
| 夏普比率 | **1.39** | 0.71 | 0.71 |

> 沪深300，3年回测，适中策略。温度定投收益率比普通定投高 33 个百分点，回撤仅为一次性买入的 1/9。

**工作原理**：
- 实时计算市场 PE 估值 + 价格偏离 200 日均线 → 综合温度 (0-100°C)
- 🧊 低估 (0-40°C) → 1.25x-2.0x 倍加仓 | 🌡️ 适中 (40-60°C) → 正常定投 | 🔥 高估 (60-100°C) → 0x-0.75x 倍少投
- 支持积极 / 适中 / 保守三档策略，回测对比三种策略表现

**三层分析框架**（深度挖掘）：

| 层次 | 分析维度 | 方法论 |
|:--:|------|------|
| 🔬 | **信号验证** | 月度温度 vs 未来12个月收益的 Pearson 相关分析 + 散点图回归 + 温度分桶统计。验证"低温→高未来收益"的实证基础 |
| 📊 | **市场环境分解** | 将回测拆分为牛市/熊市/震荡市，分别对比三种策略。诚实展示温度定投的 trade-off：牛市落后、熊市领先 |
| 🧠 | **行为金融基础** | 论证温度定投通过规则化操作克服损失厌恶、羊群效应、锚定效应三大认知偏差，将系统定位于"有理论根基的量化决策工具" |

---

## ✨ 全部功能

### 🌡️ 温度定投系统

| 功能 | 描述 |
|------|------|
| 🌡️ **智能温度定投** | 基于市场估值温度动态调整每期定投金额，实时投资建议 |
| 📈 **历史回测** | 温度定投 vs 普通定投 vs 一次性买入，多维度指标对比 |
| 🔍 **机制分析** | 低温/高温区间投入拆解，现金池动态，策略适用场景说明 |
| 🔬 **信号验证** | Pearson 相关分析验证温度对未来收益的预测能力 |
| 📊 **环境分解** | 牛/熊/震荡市策略表现对比，展示策略边界 |
| 🧠 **行为金融** | 克服认知偏差的理论框架（损失厌恶 / 羊群效应 / 锚定效应） |

### 🎯 风险测评及投资建议

| 功能 | 描述 |
|------|------|
| 🎯 **风险测评** | 12题科学问卷，5级风险等级（保守→稳健→平衡→成长→激进） |
| 🌍 **多市场覆盖** | A股 / 港股 / 美股 / 韩国，自由选择意向市场 |
| 📊 **组合优化** | 两级优化：风险等级定大类权重 → PyPortfolioOpt 优选 ETF |
| 🔮 **Monte Carlo** | GBM 模型 10,000 条路径，模拟 5/10/20 年收益分布 |
| 🤖 **AI 分析** | 本地规则引擎，即时生成配置理由、风险识别、市场情景、投资建议 |
| 📄 **PDF 报告** | 7 章节专业报告，中文完美渲染，含饼图/扇形图/直方图 |

### 📊 市场仪表盘

| 功能 | 描述 |
|------|------|
| 📊 **市场仪表盘** | 实时指数行情、行业板块热力图、宏观指标、ETF 涨跌排行 |
| 📈 **ETF 对比** | 多 ETF 横向对比，含 A 股行业板块 ETF（有色、半导体、新能源等 12 只） |
| 🌡️ **市场温度计** | 上证50/沪深300/中证500/中证1000 PE估值 + 200日均线偏离温度 |

### 🛠️ 独立工具

| 功能 | 描述 |
|------|------|
| 💰 **定投计算器** | 正算（月投→终值）/ 反算（目标→月投），逐年明细 |
| 📚 **投资术语百科** | 75 个中英双语金融术语，8 大分类，搜索+分类筛选 |

---

## 🚀 快速开始

### 前置条件

- Python 3.11+
- **无需任何 API Key** — AI 分析完全本地运行，数据源全部免费

### 安装

```bash
# 1. 克隆项目
git clone <repo-url>
cd ai-robo-advisor

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动应用
streamlit run src/ui/app.py
```

打开浏览器访问 **http://localhost:8501**。

> 💡 A股数据通过 AKShare（新浪 + 中证指数）直接获取，无需 VPN。美股 ETF 需要访问 Yahoo Finance。

---

## 📖 使用流程

| 步骤 | 页面 | 说明 |
|:--:|------|------|
| — | 🌡️ **智能温度定投** | **旗舰功能，可直接使用** — 选择指数/年限/策略即可回测 |
| 1 | 🏠 基本信息 | 填写个人信息 + 选择意向市场 |
| 2 | 🎯 风险测评 | 12题问卷，获取风险等级 |
| 3 | 📊 投资组合 | AI 优化的资产配置方案 |
| 4 | 🔮 蒙特卡洛 | 万条路径收益模拟 |
| 5 | 🤖 AI 分析 | 本地引擎深度投资分析 |
| 6 | 📄 报告下载 | 7章专业 PDF 报告 |

---

## 🏗️ 项目架构

```
ai-robo-advisor/
├── config/                    # 配置和 Prompt 模板
│   ├── settings.py            # Pydantic 集中配置
│   ├── prompts/               # AI Agent prompt 模板
│   ├── risk_weights.yaml      # 风险评分权重 + 30+ 只 ETF
│   └── investment_glossary.yaml  # 75 条中英双语术语
├── assets/                    # Logo 和静态资源
├── src/
│   ├── agents/                # AI Agent 层
│   ├── db/                    # 数据库层 (SQLAlchemy + Repository)
│   ├── engine/                # 纯计算引擎
│   │   ├── temperature_dca_engine.py  # 🌡️ 温度定投回测引擎
│   │   ├── market_thermometer.py      # 市场温度计算
│   │   ├── dca_calculator.py          # 定投计算器
│   │   ├── risk_engine.py             # 风险评分
│   │   ├── optimizer.py               # 两级组合优化
│   │   ├── monte_carlo.py             # GBM Monte Carlo
│   │   ├── metrics.py                 # 金融指标
│   │   ├── market_data.py             # 实时行情数据
│   │   ├── data_provider.py           # 多市场数据层
│   │   └── local_advisor_engine.py    # 本地 AI 分析引擎
│   ├── models/                # Pydantic 数据模型
│   ├── reports/               # PDF 报告生成 (ReportLab + Plotly)
│   ├── services/              # 业务逻辑编排
│   └── ui/                    # Streamlit 前端
│       ├── app.py             # 应用入口
│       ├── pages/             # 12 个功能页面
│       └── components/        # 可复用组件（侧边栏、图表、问卷）
├── tests/                     # 单元测试
├── docker/                    # Docker 配置
└── requirements.txt
```

---

## 🌍 数据源

| 市场 | ETF 数量 | 数据源 | 需要 VPN |
|------|:------:|--------|:--------:|
| 🇨🇳 A股（宽基） | 3 | AKShare（东方财富） | ❌ |
| 🇨🇳 A股（行业板块） | 12 | AKShare（东方财富） | ❌ |
| 🇭🇰 港股 | 3 | AKShare（东方财富） | ❌ |
| 🇺🇸 美股（跨境） | 2 | AKShare（东方财富） | ❌ |
| 🇺🇸 美股（直接） | 5 | Yahoo Finance | ✅ |
| 🇰🇷 韩国 | 1 | Yahoo Finance | ✅ |
| 📜 债券 | 6 | AKShare + Yahoo | 部分 |
| 🥇 黄金 | 3 | AKShare + Yahoo | 部分 |

> **国内无 VPN 可用 20+ 只 ETF**，覆盖完整的 A股宽基 + 行业板块 + 港股 + 跨境 + 债券/黄金。

---

## 🧪 测试

```bash
pytest tests/ -v                    # 运行所有测试
pytest tests/ -v --cov=src          # 带覆盖率
pytest tests/unit/ -v               # 仅单元测试
```

---

## ⚠️ 免责声明

本系统仅供学习和研究目的。所有投资分析和建议仅供参考，**不构成任何形式的投资建议**。历史回测不代表未来收益。投资有风险，入市需谨慎。

---

© 2026 磐策 PánCè. Built by Jason-XUE

---

---

# 🇬🇧 English

## ⛰️ PánCè — AI Robo Advisor for the Chinese A-Share Market

> **稳如磐石 · 策定乾坤** *(Steady as a Rock · Strategize the World)*

An AI-driven quantitative investment platform purpose-built for Chinese individual investors.
**Core innovation**: a **Temperature-Driven DCA** (dollar-cost-averaging) engine that
dynamically adjusts monthly investment amounts based on real-time market valuation signals —
buy more when the market is cold, buy less when it overheats.

---

## 🌡️ Flagship Feature: Temperature-Driven DCA

| Metric | 🌡️ Temp DCA | 📋 Regular DCA | 💰 Lump Sum |
|--------|:-----------:|:-------------:|:----------:|
| CAGR | **19.3%** | 7.2% | 13.7% |
| Max Drawdown | **-0.9%** | -2.0% | -7.9% |
| Sharpe Ratio | **1.39** | 0.71 | 0.71 |

> CSI 300 Index, 3-year backtest, moderate strategy. The temperature-driven approach
> outperformed regular DCA by 33 percentage points with 1/9 the drawdown of lump sum.

### How It Works

- **Market Temperature (0–100°C)**: A composite of PE valuation score (weight: 60%) +
  price deviation from 200-day moving average (weight: 40%)
- **Dynamic Multiplier Map**:
  - 🧊 Undervalued (0–40°C) → 1.25×–2.0× — aggressive buying
  - 🌡️ Fair (40–60°C) → 1.0× — normal DCA
  - 🔥 Overvalued (60–100°C) → 0×–0.75× — reduced or paused
- **Cash Pool Mechanism**: surpluses saved during hot periods are automatically
  redeployed when the temperature cools — no cash sits idle
- **Three Strategy Profiles**: Aggressive / Moderate / Conservative

---

## 🔬 Five-Layer Analytical Framework

This goes beyond "a backtest script." Each layer answers a progressively deeper question:

| # | Layer | Question Answered | Methodology |
|:--:|--------|-------------------|-------------|
| 1 | **Backtest Engine** | *Does it work in history?* | 3-strategy simulation over configurable horizons with cash pool mechanics |
| 2 | **Signal Validation** | *Does temperature actually predict returns?* | Pearson correlation of monthly temperature vs. forward 12-month returns; scatter plot with regression; quintile bucket analysis |
| 3 | **Walk-Forward Test** | *Is this just overfitting?* | Gold-standard out-of-sample validation — grid search (6 PE weights × 3 strategies = 18 combinations) on training window, then a single locked-parameter run on unseen test data |
| 4 | **Regime Decomposition** | *When does it win and when does it lose?* | Performance breakdown across bull, bear, and sideways market regimes — honest trade-off analysis |
| 5 | **Behavioral Finance** | *Why should it work in theory?* | Positions the system as a rules-based intervention against three cognitive biases: loss aversion, herd behavior, and anchoring |

---

## ✨ Full Feature Set

### 🌡️ Temperature DCA System (Flagship)

| Feature | Description |
|---------|-------------|
| 🌡️ **Temperature DCA** | Dynamic monthly investment based on real-time valuation temperature |
| 📈 **Historical Backtest** | Temp DCA vs. regular DCA vs. lump sum — multi-metric comparison |
| 🔍 **Mechanism Analysis** | Zone-by-zone investment breakdown, cash pool dynamics, strategy caveats |
| 🔬 **Signal Validation** | Pearson correlation + scatter regression validating temperature's predictive power |
| 📊 **Regime Decomposition** | Bull / bear / sideways performance comparison — strategy boundaries |
| 🧠 **Behavioral Finance** | Theoretical grounding: loss aversion, herd behavior, anchoring |
| 🚶 **Walk-Forward** | Out-of-sample grid search — strategy robustness beyond curve-fitting |

### 🎯 Risk Assessment & Portfolio Construction

| Feature | Description |
|---------|-------------|
| 🎯 **Risk Questionnaire** | 12-item scientific assessment → 5 risk tolerance levels |
| 🌍 **Multi-Market Coverage** | A-shares / HK / US / Korea — configurable market selection |
| 📊 **Portfolio Optimization** | Two-stage: risk-based asset allocation → PyPortfolioOpt mean-variance ETF selection (30+ ETFs) |
| 🔮 **Monte Carlo Simulation** | 10,000 GBM paths → 5/10/20-year return distributions with VaR/CVaR |
| 🤖 **AI Analysis** | Local rule-based engine — instant allocation rationale, risk identification, scenario analysis |
| 📄 **PDF Report** | 7-chapter professional report with embedded Plotly charts |

### 📊 Market Dashboard

| Feature | Description |
|---------|-------------|
| 📊 **Market Dashboard** | Real-time index quotes, sector heatmaps, macro indicators, ETF rankings |
| 📈 **ETF Comparison** | Multi-ETF cross-comparison, including 12 A-share sector ETFs |
| 🌡️ **Market Thermometer** | PE valuation + 200-day MA deviation for SSE 50 / CSI 300 / CSI 500 / CSI 1000 |

### 🛠️ Standalone Tools

| Feature | Description |
|---------|-------------|
| 💰 **DCA Calculator** | Forward (monthly → terminal) / reverse (target → monthly) with yearly breakdowns |
| 📚 **Investment Glossary** | 75 bilingual (CN/EN) financial terms across 8 categories |

---

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Framework** | Streamlit (full-stack) |
| **Data** | Pandas, NumPy, AKShare (Sina + CSIndex + EastMoney), Yahoo Finance |
| **Visualization** | Plotly (interactive charts), Matplotlib (report charts) |
| **Statistics** | SciPy (Pearson r, hypothesis testing), NumPy (linear regression) |
| **Database** | SQLAlchemy ORM + SQLite |
| **Reporting** | ReportLab (PDF generation with embedded Plotly images) |
| **Config** | Pydantic Settings, YAML |

**Scale**: 61 Python files · 13,000+ lines · 12 UI pages · 5-layer architecture
**Data**: 100% free public sources · Zero API keys required · No external LLM dependency

---

## 🏗️ Architecture

```
ai-robo-advisor/
├── config/                    # Pydantic settings, YAML configs, prompt templates
├── src/
│   ├── agents/                # AI analysis agent layer
│   ├── db/                    # SQLAlchemy ORM + Repository pattern
│   ├── engine/                # Pure computation (no Streamlit dependency)
│   │   ├── temperature_dca_engine.py  # 🌡️ Flagship backtest + validation
│   │   ├── market_thermometer.py      # Temperature signal computation
│   │   ├── dca_calculator.py          # DCA forward/reverse calculator
│   │   ├── risk_engine.py             # Risk scoring
│   │   ├── optimizer.py               # Two-stage portfolio optimization
│   │   ├── monte_carlo.py             # GBM Monte Carlo simulation
│   │   ├── market_data.py             # Multi-source market data (Sina/EastMoney/CSIndex)
│   │   └── local_advisor_engine.py    # Local AI analysis engine
│   ├── models/                # Pydantic data models
│   ├── reports/               # PDF report generation
│   ├── services/              # Business logic orchestration
│   └── ui/                    # Streamlit frontend (12 pages + reusable components)
└── tests/                     # Unit tests
```

**Design principle**: computation (engine/) is strictly separated from presentation (ui/).
Every financial calculation is independently testable without a running Streamlit process.

---

## 🚀 Quick Start

```bash
git clone <repo-url> && cd ai-robo-advisor
pip install -r requirements.txt
streamlit run src/ui/app.py
```

Open **http://localhost:8501**. No API keys, no VPN (for A-share data).

---

## 🌍 Data Sources

| Market | Coverage | Source | VPN Required |
|--------|:--------:|--------|:------------:|
| 🇨🇳 A-shares (broad) | 3 ETFs | AKShare (Sina) | No |
| 🇨🇳 A-shares (sectors) | 12 ETFs | AKShare (EastMoney) | No |
| 🇭🇰 Hong Kong | 3 ETFs | AKShare | No |
| 🇺🇸 US (cross-listed) | 2 ETFs | AKShare | No |
| 🇺🇸 US (direct) | 5 ETFs | Yahoo Finance | Yes |
| 🇰🇷 Korea | 1 ETF | Yahoo Finance | Yes |
| 📜 Bonds | 6 ETFs | AKShare + Yahoo | Partial |
| 🥇 Gold | 3 ETFs | AKShare + Yahoo | Partial |

> **20+ ETFs accessible without VPN** — full A-share broad + sector + HK + cross-border coverage.

---

## ⚠️ Disclaimer

This system is built for **educational and research purposes only**. All investment analysis
and suggestions are for reference only and **do not constitute investment advice** in any form.
Historical backtest results do not guarantee future performance. Investing involves risk.
Consult a licensed financial advisor before making investment decisions.

---

Built by **Jason (ZIJIE-XUE)** · 2026
