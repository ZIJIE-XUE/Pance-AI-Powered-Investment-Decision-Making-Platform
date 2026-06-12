# ⛰️ 磐策 PánCè — AI 智能投资顾问

> 稳如磐石 · 策定乾坤

AI 驱动的智能投顾（Robo Advisor）系统。集成现代投资组合理论、Monte Carlo 模拟和本地 AI 分析引擎，覆盖 A股 / 港股 / 美股 / 韩国四大市场。

---

## ✨ 核心功能

| 功能 | 描述 |
|------|------|
| 🎯 **风险测评** | 12题科学问卷，5级风险等级（保守型→激进型） |
| 🌍 **多市场覆盖** | A股 / 港股 / 美股 / 韩国，可自由选择意向市场 |
| 📊 **组合优化** | 两级优化：风险等级定大类权重 → PyPortfolioOpt 优选 ETF |
| 🔮 **Monte Carlo** | GBM 模型 10,000 条路径，模拟 5/10/20 年收益分布 |
| 🤖 **AI 分析** | 本地规则引擎，即时生成配置理由、风险识别、市场情景、投资建议 |
| 📄 **PDF 报告** | 7 章节专业报告，中文完美渲染，含饼图/扇形图/直方图 |

## 🚀 快速开始

### 前置条件

- Python 3.11+
- **无需任何 API Key** — AI 分析完全本地运行

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

> 💡 美股 ETF 数据需要能访问 Yahoo Finance；A股/港股/跨境 ETF 通过 AKShare 直接获取，无需 VPN。

### Docker 部署

```bash
# 开发环境（SQLite + 热重载）
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up

# 生产环境（PostgreSQL + Redis）
docker compose -f docker/docker-compose.yml up -d
```

## 📖 使用流程

1. **🏠 首页** → 填写基本信息 + 选择意向投资市场
2. **🎯 风险测评** → 完成12题问卷，获取风险等级
3. **📊 组合配置** → 查看 AI 优化的资产配置方案
4. **🔮 Monte Carlo** → 选择投资期限，运行收益模拟
5. **🤖 AI 分析** → 获取本地 AI 引擎的深度投资分析
6. **📄 报告下载** → 下载 PDF 专业投资报告

## 🏗️ 项目架构

```
ai-robo-advisor/
├── config/               # 配置和 Prompt 模板
│   ├── settings.py       # Pydantic 集中配置
│   ├── prompts/          # AI Agent prompt 模板
│   └── risk_weights.yaml # 风险问卷 + 评分权重 + 24只多市场ETF
├── assets/               # Logo 和静态资源
├── src/
│   ├── agents/           # AI Agent 层
│   │   ├── advisor_agent.py    # 投资顾问 Agent（本地引擎）
│   │   ├── base_agent.py       # Agent 抽象基类
│   │   ├── claude_client.py    # Claude API 封装（可选）
│   │   └── prompt_manager.py   # Prompt 模板管理
│   ├── db/               # 数据库层 (SQLAlchemy + Repository)
│   ├── engine/           # 纯计算引擎
│   │   ├── risk_engine.py      # 风险评分
│   │   ├── optimizer.py        # 两级组合优化
│   │   ├── monte_carlo.py      # GBM Monte Carlo 模拟
│   │   ├── metrics.py          # 金融指标计算
│   │   ├── data_provider.py    # 多市场数据层 (AKShare + Yahoo)
│   │   └── local_advisor_engine.py  # 本地 AI 分析引擎
│   ├── models/           # Pydantic 数据模型
│   ├── reports/          # PDF 报告生成 (ReportLab + Plotly)
│   ├── services/         # 业务逻辑编排层
│   └── ui/               # Streamlit 前端
│       ├── app.py        # 应用入口
│       ├── pages/        # 6 个功能页面
│       └── components/   # 可复用组件（侧边栏、问卷、图表）
├── tests/                # 单元测试（41个）
├── docker/               # Docker 配置
└── .github/workflows/    # CI/CD
```

## 🌍 数据源

| 市场 | 股票 ETF 数量 | 数据源 | 需要 VPN |
|------|:-----------:|--------|:--------:|
| 🇨🇳 A股 | 3 | AKShare（东方财富） | ❌ |
| 🇭🇰 港股 | 3 | AKShare（东方财富） | ❌ |
| 🇺🇸 美股（跨境） | 2 | AKShare（东方财富） | ❌ |
| 🇺🇸 美股（直接） | 5 | Yahoo Finance | ✅ |
| 🇰🇷 韩国 | 1 | Yahoo Finance | ✅ |
| 📜 债券 | 6 | AKShare + Yahoo | 部分 |
| 🥇 黄金 | 3 | AKShare + Yahoo | 部分 |
| 🏠 地产 | 1 | Yahoo Finance | ✅ |

> **国内无 VPN 可用 16 只 ETF**（A股 + 港股 + 跨境 + A股债券/黄金），覆盖完整的股债金大类资产配置。

## 🔑 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ANTHROPIC_API_KEY` | Anthropic API 密钥（可选，AI分析已本地化） | *空* |
| `CLAUDE_MODEL` | Claude 模型（可选） | `claude-sonnet-4-6` |
| `DATABASE_URL` | 数据库连接 | `sqlite+aiosqlite:///...` |
| `REDIS_URL` | Redis 连接（可选） | `None` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 带覆盖率报告
pytest tests/ -v --cov=src --cov-report=html

# 仅运行单元测试
pytest tests/unit/ -v
```

## ⚠️ 免责声明

本系统仅供学习和研究目的。所有投资分析和建议仅供参考，**不构成任何形式的投资建议**。投资有风险，过往表现不代表未来收益。在做出任何投资决策前，请咨询持牌专业投资顾问。

## 📄 License

MIT License

---

© 2026 磐策 PánCè. Built by Jason & Claude.
