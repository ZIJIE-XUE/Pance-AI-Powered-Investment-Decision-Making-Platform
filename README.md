# 🤖 AI Robo Advisor - 智能投资顾问系统

AI 驱动的智能投顾（Robo Advisor）系统，集成现代投资组合理论、Monte Carlo 模拟和 Claude AI 大语言模型。

## ✨ 核心功能

| 功能 | 描述 |
|------|------|
| 🎯 **风险测评** | 12题科学问卷，5级风险等级（保守型→激进型） |
| 📊 **组合优化** | 基于现代投资组合理论，覆盖股票ETF/债券ETF/黄金ETF |
| 🔮 **Monte Carlo** | 10,000条路径模拟未来5/10/20年收益分布 |
| 🤖 **AI 分析** | Claude AI 深度解读配置理由、风险和市场情景 |
| 📄 **PDF 报告** | 一键生成包含完整图表的专业投资报告 |

## 🚀 快速开始

### 前置条件

- Python 3.11+
- [Anthropic API Key](https://console.anthropic.com/) (用于 AI 分析功能)

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

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 ANTHROPIC_API_KEY

# 5. 启动应用
streamlit run src/ui/app.py
```

### Docker 部署

```bash
# 开发环境（SQLite + 热重载）
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up

# 生产环境（PostgreSQL + Redis）
docker compose -f docker/docker-compose.yml up -d
```

## 📖 使用流程

1. **首页** → 填写年龄、收入、资产、投资目标
2. **风险测评** → 完成12题问卷，获取风险等级
3. **组合配置** → 查看AI优化的资产配置方案
4. **Monte Carlo** → 选择投资期限，运行收益模拟
5. **AI 分析** → 获取 Claude AI 的深度投资分析
6. **报告下载** → 下载 PDF 专业投资报告

## 🏗️ 项目架构

```
ai-robo-advisor/
├── config/              # 配置和 Prompt 模板
│   ├── settings.py      # Pydantic 集中配置
│   ├── prompts/         # AI Agent prompt 模板
│   └── risk_weights.yaml # 风险问卷和评分权重
├── src/
│   ├── agents/          # AI Agent 架构
│   │   ├── advisor_agent.py   # 投资顾问 Agent
│   │   ├── claude_client.py   # Claude API 封装
│   │   └── prompt_manager.py  # Prompt 管理
│   ├── db/              # 数据库层 (SQLAlchemy + Repository)
│   ├── engine/          # 纯计算引擎
│   │   ├── risk_engine.py     # 风险评分
│   │   ├── optimizer.py       # 组合优化
│   │   ├── monte_carlo.py     # GBM 模拟
│   │   └── metrics.py         # 金融指标
│   ├── models/          # Pydantic 数据模型
│   ├── reports/         # PDF 报告生成 (ReportLab + Plotly)
│   ├── services/        # 业务逻辑编排层
│   └── ui/              # Streamlit 前端
│       ├── app.py       # 应用入口
│       ├── pages/       # 6个功能页面
│       └── components/  # 可复用组件
├── tests/               # 单元测试 + 集成测试
├── docker/              # Docker 配置
└── .github/workflows/   # CI/CD
```

## 🔑 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | *必填* |
| `CLAUDE_MODEL` | Claude 模型 | `claude-sonnet-4-6` |
| `DATABASE_URL` | 数据库连接 | `sqlite+aiosqlite:///...` |
| `REDIS_URL` | Redis 连接 (可选) | `None` |
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

© 2026 AI Robo Advisor. Built with ❤️ by Jason & Claude.
