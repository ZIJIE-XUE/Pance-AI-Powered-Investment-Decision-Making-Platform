"""I18n: Chinese-English translation via a flat dictionary + t() helper.

Usage:
    from src.ui.i18n import t, _
    t("基本信息")          # → "基本信息" if zh, "Basic Info" if en
    _("基本信息")          # → same as t(), shorthand for inline use
"""

import streamlit as st

# ── Translation dictionary ──────────────────────────────────────────────────
# Keys are Chinese text; values are dicts with "en" key.
# Empty dict or missing "en" → falls back to the Chinese key itself.

TRANSLATIONS = {

    # =====================================================================
    # SECTION: Sidebar
    # =====================================================================

    # ── Sidebar: section headers ───────────────────────────────────────────
    "🌡️ 旗舰功能":                       {"en": "🌡️ Flagship"},
    "🎯 风险测评及投资建议":              {"en": "🎯 Workflow"},
    "📊 市场仪表盘":                      {"en": "📊 Dashboard"},
    "🛠️ 独立工具":                       {"en": "🛠️ Tools"},
    "ℹ️ 使用说明":                       {"en": "ℹ️ Help"},
    "👈 请先填写基本信息":                {"en": "👈 Fill in your info first"},

    # ── Sidebar: workflow steps ────────────────────────────────────────────
    "基本信息":                           {"en": "Basic Info"},
    "填写个人档案与意向市场":             {"en": "Profile & market preferences"},
    "风险测评":                           {"en": "Risk Assessment"},
    "12题科学问卷 · 5级风险":            {"en": "12-question quiz · 5 levels"},
    "投资组合":                           {"en": "Portfolio"},
    "AI优化 · 资产配置方案":              {"en": "AI-optimized allocation"},
    "蒙特卡洛":                           {"en": "Monte Carlo"},
    "万条路径 · 收益模拟":                {"en": "10K paths · projection"},
    "AI 分析":                            {"en": "AI Analysis"},
    "深度解读 · 操作建议":                {"en": "Deep dive · recommendations"},
    "报告下载":                           {"en": "Report"},
    "PDF专业报告导出":                    {"en": "PDF professional report"},

    # ── Sidebar: flagship ──────────────────────────────────────────────────
    "智能温度定投":                       {"en": "Temperature DCA"},
    "市场冷时多投 · 热时少投":           {"en": "Buy more when cold, less when hot"},

    # ── Sidebar: dashboard ─────────────────────────────────────────────────
    "市场仪表盘":                         {"en": "Market Dashboard"},
    "实时行情 · 板块热力":                {"en": "Live quotes · sector heatmap"},
    "ETF对比":                            {"en": "ETF Comparison"},
    "全市场ETF排行筛选":                  {"en": "ETF rankings & filters"},
    "市场温度计":                         {"en": "Market Thermometer"},
    "估值分位 · 买卖信号":                {"en": "Valuation percentile · signals"},

    # ── Sidebar: tools ─────────────────────────────────────────────────────
    "定投计算器":                         {"en": "DCA Calculator"},
    "复利测算 · 目标规划":                {"en": "Compound calc · goal planning"},
    "投资术语百科":                       {"en": "Investment Glossary"},
    "中英双语 · 随时查阅":                {"en": "Bilingual · always accessible"},

    # ── Sidebar: misc ──────────────────────────────────────────────────────
    "已完成":                              {"en": "done"},
    "进入 →":                              {"en": "Go →"},

    # ── Sidebar: other ─────────────────────────────────────────────────────
    "稳如磐石 · 策定乾坤":                {"en": "Steady as a Rock · Strategic Foresight"},
    "投资有风险 · 入市需谨慎":            {"en": "Investing involves risk. Trade cautiously."},

    "未指定":                               {"en": "Not specified"},
    "投资者":                               {"en": "Investor"},
    "⚠️ 请先在首页填写基本信息":            {"en": "⚠️ Please fill in your basic info on the home page first"},

    # =====================================================================
    # SECTION: 00_landing.py (Homepage)
    # =====================================================================

    # ── Homepage: hero ─────────────────────────────────────────────────────
    "AI 智能投资决策平台":                 {"en": "AI-Powered Investment Platform"},
    "👋 欢迎回来，":                       {"en": "👋 Welcome back, "},

    # ── Homepage: feature cards ────────────────────────────────────────────
    "市场冷时多投 · 热时少投<br>回测验证，数据驱动决策": {
        "en": "Buy more when cold, less when hot<br>Backtest-verified, data-driven"
    },
    "12题科学问卷<br>5级风险 · 组合优化":  {"en": "12-question quiz<br>5 risk levels · optimization"},
    "实时行情 · 板块热力<br>ETF对比 · 市场温度计": {
        "en": "Live quotes · sector heatmap<br>ETF compare · market thermometer"
    },
    "万条路径模拟<br>AI 分析 · PDF 报告":  {"en": "10K paths simulation<br>AI analysis · PDF report"},
    "旗舰":                                {"en": "Flagship"},

    # ── Homepage: quick start ──────────────────────────────────────────────
    "🚀 快速开始":                         {"en": "🚀 Quick Start"},
    "🌡️ 智能温度定投 — 旗舰功能，可直接使用，无需前置步骤": {
        "en": "🌡️ Temperature DCA — flagship feature, ready to use"
    },
    "📝 填写基本信息 → 🎯 完成风险测评":   {"en": "📝 Fill basic info → 🎯 Complete risk assessment"},
    "📊 查看 AI 优化的投资组合 → 🔮 运行 Monte Carlo 模拟": {
        "en": "📊 View AI portfolio → 🔮 Run Monte Carlo"
    },
    "🤖 获取 AI 深度分析 → 📄 下载 PDF 专业报告": {
        "en": "🤖 Get AI analysis → 📄 Download PDF report"
    },
    "👈 从左侧栏 🌡️ 温度定投系统 开始体验旗舰功能，"
    "或从 🎯 风险测评及投资建议 走完完整流程。": {
        "en": "👈 Start with 🌡️ Temperature DCA in the sidebar, "
             "or go through 🎯 Workflow for the full experience."
    },

    # ── Homepage: returning user ───────────────────────────────────────────
    "👉 下一步：完成风险测评问卷":          {"en": "👉 Next: Complete the risk assessment"},
    "👉 下一步：生成投资组合配置":          {"en": "👉 Next: Generate your portfolio"},
    "👉 下一步：运行 Monte Carlo 模拟":     {"en": "👉 Next: Run Monte Carlo simulation"},
    "👉 下一步：获取 AI 投资建议":          {"en": "👉 Next: Get AI investment advice"},
    "👉 下一步：下载 PDF 报告":             {"en": "👉 Next: Download the PDF report"},

    # =====================================================================
    # SECTION: 01_home.py (Basic Info / Profile)
    # =====================================================================

    "🏠 基本信息":                           {"en": "🏠 Basic Info"},
    "### 智能投资顾问 - 个人信息":           {"en": "### AI Investment Advisor - Personal Info"},
    "✅ 基本信息已填写":                     {"en": "✅ Basic info saved"},
    "年龄":                                  {"en": "Age"},
    "年收入":                                {"en": "Annual Income"},
    "资产规模":                              {"en": "Asset Size"},
    "投资期限":                              {"en": "Investment Horizon"},
    "投资目标":                              {"en": "Investment Goal"},
    "意向市场":                              {"en": "Target Markets"},
    "🔄 修改信息":                           {"en": "🔄 Edit Info"},
    "👉 下一步：风险测评":                   {"en": "👉 Next: Risk Assessment"},
    "请填写以下信息，帮助我们为您量身定制投资方案。": {
        "en": "Please fill in the information below to help us tailor your investment plan."
    },
    "邮箱 *":                                {"en": "Email *"},
    "your@email.com":                        {"en": "your@email.com"},
    "用于识别您的投资档案":                  {"en": "Used to identify your investment profile"},
    "年龄 *":                                {"en": "Age *"},
    "年收入 (¥) *":                          {"en": "Annual Income (¥) *"},
    "可投资资产规模 (¥) *":                  {"en": "Investable Assets (¥) *"},
    "税后年收入":                            {"en": "After-tax annual income"},
    "您计划用于投资的资金总额":              {"en": "Total funds you plan to invest"},
    "显示名称":                              {"en": "Display Name"},
    "您的称呼（可选）":                      {"en": "Your name (optional)"},
    "投资期限 *":                            {"en": "Investment Horizon *"},
    "您计划持有投资的时间长度":              {"en": "How long you plan to hold your investments"},
    "例如：为退休储蓄、购房首付、子女教育基金...": {
        "en": "e.g., Retirement savings, home down payment, education fund..."
    },
    "描述您的投资目标，这将帮助AI更好地理解您的需求": {
        "en": "Describe your investment goals; this helps the AI better understand your needs"
    },
    "### 🌍 意向投资市场":                    {"en": "### 🌍 Target Markets"},
    "选择您希望投资的市场，后续组合优化将仅使用选中市场的股票类ETF（债券、黄金、现金不受此限制）": {
        "en": "Select the markets you wish to invest in. Portfolio optimization will only use equity ETFs from selected markets (bonds, gold, and cash are not restricted)."
    },
    "A股":                                   {"en": "A-Shares"},
    "港股":                                  {"en": "HK Stocks"},
    "美股":                                  {"en": "US Stocks"},
    "韩国":                                  {"en": "Korea"},
    "可多选。投资组合中的股票类资产将只从您选择的市场中挑选": {
        "en": "Multi-select. Equity assets in your portfolio will only be drawn from selected markets."
    },
    "💾 保存信息并开始测评":                  {"en": "💾 Save & Start Assessment"},
    "请输入有效的邮箱地址":                   {"en": "Please enter a valid email address"},
    "✅ 信息保存成功！请前往下一步进行风险测评。": {
        "en": "✅ Info saved! Please proceed to the risk assessment."
    },
    "保存失败：":                             {"en": "Save failed: "},

    # =====================================================================
    # SECTION: 02_risk_assessment.py
    # =====================================================================

    "🎯 风险承受能力测评":                    {"en": "🎯 Risk Tolerance Assessment"},
    "⚠️ 请先在首页填写您的基本信息":          {"en": "⚠️ Please fill in your basic info on the home page first"},
    "前往首页":                               {"en": "Go to Home"},
    "✅ 测评已完成！":                        {"en": "✅ Assessment complete!"},
    "**风险等级：**":                          {"en": "**Risk Level:** "},
    "（评分：":                               {"en": " (Score: "},
    "🔄 重新测评":                            {"en": "🔄 Retake Assessment"},
    "👉 下一步：投资组合":                     {"en": "👉 Next: Portfolio"},
    "📊 提交测评":                            {"en": "📊 Submit Assessment"},
    "已完成 ":                                {"en": " completed"},
    " 题":                                    {"en": " of "},
    "正在分析您的风险承受能力...":            {"en": "Analyzing your risk tolerance..."},
    "✅ 测评完成！":                           {"en": "✅ Assessment complete!"},
    "测评提交失败：":                          {"en": "Assessment submission failed: "},

    # ── 02_risk_assessment: questionnaire ──────────────────────────────────
    "投资者风险承受能力测评":                  {"en": "Investor Risk Tolerance Assessment"},
    "请回答以下问题，我们将根据您的回答评估您的风险承受能力等级。": {
        "en": "Please answer the following questions. We will assess your risk tolerance level based on your responses."
    },
    "⏰ 投资期限":                             {"en": "⏰ Investment Horizon"},
    "💰 财务状况":                             {"en": "💰 Financial Situation"},
    "🎯 风险承受":                             {"en": "🎯 Risk Tolerance"},
    "📈 投资偏好":                             {"en": "📈 Investment Preference"},
    "📚 知识与经验":                           {"en": "📚 Knowledge & Experience"},

    # ── 02_risk_assessment: questions ──────────────────────────────────────
    "您的年龄范围是？":                        {"en": "What is your age range?"},
    "您计划的投资期限是？":                    {"en": "What is your planned investment horizon?"},
    "您的年收入水平（人民币）？":              {"en": "What is your annual income level (RMB)?"},
    "您的可投资资产占总资产的比例？":          {"en": "What percentage of your total assets is investable?"},
    "如果市场下跌20%，您会怎么做？":           {"en": "If the market drops 20%, what would you do?"},
    "您能接受的最大年度亏损是多少？":          {"en": "What is the maximum annual loss you can accept?"},
    "您更看重投资的哪个方面？":                {"en": "Which aspect of investing do you value most?"},
    "您对投资产品的了解程度？":                {"en": "How familiar are you with investment products?"},
    "您是否有稳定的应急储备金（3-6个月开支）？": {"en": "Do you have a stable emergency fund (3-6 months of expenses)?"},
    "您期望的年化投资回报率是？":              {"en": "What annualized return do you expect?"},
    "当您的投资组合价值波动时，您的感受是？":  {"en": "How do you feel when your portfolio value fluctuates?"},
    "您的投资经验年限？":                      {"en": "How many years of investment experience do you have?"},

    # ── 02_risk_assessment: Q1 options (age) ───────────────────────────────
    "60岁以上":                                {"en": "Over 60"},
    "50-60岁":                                 {"en": "50-60"},
    "40-50岁":                                 {"en": "40-50"},
    "30-40岁":                                 {"en": "30-40"},
    "30岁以下":                                {"en": "Under 30"},

    # ── 02_risk_assessment: Q2 options (horizon) ───────────────────────────
    "1年以内":                                 {"en": "Under 1 year"},
    "1-3年":                                   {"en": "1-3 years"},
    "3-5年":                                   {"en": "3-5 years"},
    "5-10年":                                  {"en": "5-10 years"},
    "10年以上":                                {"en": "Over 10 years"},

    # ── 02_risk_assessment: Q3 options (income) ────────────────────────────
    "10万以下":                                {"en": "Under 100K"},
    "10-30万":                                 {"en": "100K-300K"},
    "30-60万":                                 {"en": "300K-600K"},
    "60-100万":                                {"en": "600K-1M"},
    "100万以上":                               {"en": "Over 1M"},

    # ── 02_risk_assessment: Q4 options (ratio) ─────────────────────────────
    "10%以下":                                 {"en": "Under 10%"},
    "10%-25%":                                 {"en": "10%-25%"},
    "25%-50%":                                 {"en": "25%-50%"},
    "50%-75%":                                 {"en": "50%-75%"},
    "75%以上":                                 {"en": "Over 75%"},

    # ── 02_risk_assessment: Q5 options (drop) ──────────────────────────────
    "立即卖出所有投资":                        {"en": "Sell all investments immediately"},
    "卖出一部分减少损失":                      {"en": "Sell part to reduce losses"},
    "观望等待市场稳定":                        {"en": "Wait and observe until market stabilizes"},
    "继续持有不做变动":                        {"en": "Hold and make no changes"},
    "逢低加仓买入更多":                        {"en": "Buy more at lower prices"},

    # ── 02_risk_assessment: Q6 options (loss) ──────────────────────────────
    "不能接受任何亏损":                        {"en": "Cannot accept any loss"},
    "5%以内":                                  {"en": "Within 5%"},
    "5%-15%":                                  {"en": "5%-15%"},
    "15%-25%":                                 {"en": "15%-25%"},
    "25%以上":                                 {"en": "Over 25%"},

    # ── 02_risk_assessment: Q7 options (priority) ──────────────────────────
    "本金绝对安全":                            {"en": "Absolute principal safety"},
    "稳定现金流入":                            {"en": "Stable cash flow"},
    "兼顾收益和增长":                          {"en": "Balance of income and growth"},
    "长期资本增值":                            {"en": "Long-term capital appreciation"},
    "最大化回报":                              {"en": "Maximize returns"},

    # ── 02_risk_assessment: Q8 options (knowledge) ─────────────────────────
    "完全不了解":                              {"en": "No knowledge at all"},
    "了解基础产品（存款、理财）":              {"en": "Know basic products (deposits, wealth mgmt)"},
    "了解基金和债券":                          {"en": "Know funds and bonds"},
    "了解股票和ETF":                           {"en": "Know stocks and ETFs"},
    "专业投资者水平":                          {"en": "Professional investor level"},

    # ── 02_risk_assessment: Q9 options (emergency) ─────────────────────────
    "没有":                                    {"en": "None"},
    "有1-2个月":                               {"en": "1-2 months"},
    "有2-3个月":                               {"en": "2-3 months"},
    "有3-6个月":                               {"en": "3-6 months"},
    "超过6个月":                               {"en": "Over 6 months"},

    # ── 02_risk_assessment: Q10 options (return) ───────────────────────────
    "跑赢通胀即可（3%-5%）":                   {"en": "Beat inflation (3%-5%)"},
    "5%-8%":                                   {"en": "5%-8%"},
    "8%-12%":                                  {"en": "8%-12%"},
    "12%-15%":                                 {"en": "12%-15%"},
    "15%以上":                                 {"en": "Over 15%"},

    # ── 02_risk_assessment: Q11 options (feeling) ──────────────────────────
    "非常焦虑，无法入睡":                      {"en": "Very anxious, can't sleep"},
    "比较担心，经常查看":                      {"en": "Quite worried, check frequently"},
    "有些紧张但可以接受":                      {"en": "Somewhat nervous but acceptable"},
    "认为这是正常的市场波动":                  {"en": "View it as normal market volatility"},
    "完全不受影响":                            {"en": "Completely unaffected"},

    # ── 02_risk_assessment: Q12 options (experience) ───────────────────────
    "无任何投资经验":                          {"en": "No investment experience"},
    "1年以下":                                 {"en": "Under 1 year"},
    "1-3年":                                   {"en": "1-3 years"},
    "3-7年":                                   {"en": "3-7 years"},
    "7年以上":                                 {"en": "Over 7 years"},

    # ── 02_risk_assessment: risk levels ────────────────────────────────────
    "保守型":                                  {"en": "Conservative"},
    "稳健型":                                  {"en": "Moderate"},
    "平衡型":                                  {"en": "Balanced"},
    "成长型":                                  {"en": "Growth"},
    "激进型":                                  {"en": "Aggressive"},

    # ── 02_risk_assessment: risk descriptions ──────────────────────────────
	"以资本保值为首要目标，接受极低风险。适合短期投资或无法承受损失的投资者。": {
	    "en": "Primary goal is capital preservation with very low risk tolerance. Suitable for short-term investors or those who cannot bear losses."
	},
	"以稳定收益为主，追求适度增长。适合风险承受能力较低的保守投资者。": {
	    "en": "Focus on stable returns with moderate growth. Suitable for conservative investors with low risk tolerance."
	},
	"在增长和收益之间寻求平衡。适合有一定风险承受能力的中期投资者。": {
	    "en": "Seek balance between growth and income. Suitable for medium-term investors with moderate risk tolerance."
	},
	"追求长期资本增值，愿意接受较高波动。适合长期投资且风险承受能力较强的投资者。": {
	    "en": "Pursue long-term capital appreciation, accepting higher volatility. Suitable for long-term investors with strong risk tolerance."
	},
	"最大化长期回报，接受高波动和较大回撤。适合风险承受能力极强的长期投资者。": {
	    "en": "Maximize long-term returns, accepting high volatility and large drawdowns. Suitable for long-term investors with very strong risk tolerance."
	},

    # ── 02_risk_assessment: result display ─────────────────────────────────
    "## 测评结果":                             {"en": "## Assessment Result"},
    "风险承受能力评分":                        {"en": "Risk Tolerance Score"},
    "风险等级解读：":                          {"en": "Risk Level Interpretation:"},
    "### 各维度得分明细":                      {"en": "### Dimension Score Breakdown"},
    "投资期限":                                {"en": "Investment Horizon"},
    "财务状况":                                {"en": "Financial Situation"},
    "风险承受":                                {"en": "Risk Tolerance"},
    "投资偏好":                                {"en": "Investment Preference"},
    "知识经验":                                {"en": "Knowledge & Experience"},

    # =====================================================================
    # SECTION: 03_portfolio.py
    # =====================================================================

    "📊 投资组合配置":                         {"en": "📊 Portfolio Allocation"},
    "⚠️ 请先完成风险测评":                     {"en": "⚠️ Please complete the risk assessment first"},
    "前往风险测评":                            {"en": "Go to Risk Assessment"},
    "🎯 您的风险等级：":                       {"en": "🎯 Your Risk Level: "},
    "  | 评分：":                              {"en": "  | Score: "},
    "🔄 重新优化":                             {"en": "🔄 Re-optimize"},
    "👉 下一步：Monte Carlo 模拟":             {"en": "👉 Next: Monte Carlo"},
    "🚀 生成投资组合":                          {"en": "🚀 Generate Portfolio"},
    "正在进行投资组合优化...（获取市场数据可能需要1-2分钟）": {
        "en": "Running portfolio optimization... (fetching market data may take 1-2 minutes)"
    },
    "✅ 投资组合生成完成！":                   {"en": "✅ Portfolio generated!"},
    "优化失败：":                              {"en": "Optimization failed: "},
    "预期年化收益":                            {"en": "Expected Annual Return"},
    "年化波动率":                              {"en": "Annual Volatility"},
    "夏普比率":                                {"en": "Sharpe Ratio"},
    "最大回撤":                                {"en": "Max Drawdown"},
    "Sharpe Ratio > 1 为良好，> 2 为优秀":    {"en": "Sharpe Ratio > 1 is good, > 2 is excellent"},
    "### 资产配置比例":                         {"en": "### Asset Allocation"},
    "**资产类别图例**":                         {"en": "**Asset Class Legend**"},
    "🟥 股票":                                 {"en": "🟥 Equities"},
    "🟦 债券":                                 {"en": "🟦 Bonds"},
    "🟩 黄金":                                 {"en": "🟩 Gold"},
    "🟧 地产":                                 {"en": "🟧 Real Estate"},
    "### 持仓明细":                             {"en": "### Holdings Detail"},
    "代码":                                    {"en": "Ticker"},
    "名称":                                    {"en": "Name"},
    "资产类别":                                {"en": "Asset Class"},
    "配置比例":                                {"en": "Allocation"},
    "预期收益":                                {"en": "Expected Return"},
    "年化波动":                                {"en": "Ann. Volatility"},
    "### 大类资产汇总":                         {"en": "### Asset Class Summary"},
    "股票":                                    {"en": "Equities"},
    "债券":                                    {"en": "Bonds"},
    "黄金":                                    {"en": "Gold"},
    "地产":                                    {"en": "Real Estate"},
    "现金":                                    {"en": "Cash"},

    # =====================================================================
    # SECTION: 04_simulation.py
    # =====================================================================

    "🔮 Monte Carlo 模拟":                     {"en": "🔮 Monte Carlo Simulation"},
    "⚠️ 请先完成投资组合优化":                  {"en": "⚠️ Please complete portfolio optimization first"},
    "前往组合优化":                             {"en": "Go to Portfolio"},
    "初始投资金额 (¥)":                        {"en": "Initial Investment (¥)"},
    "选择模拟的时间跨度":                       {"en": "Select the simulation time horizon"},
    "模拟路径数":                               {"en": "Simulation Paths"},
    "路径越多越精确，但计算时间更长":           {"en": "More paths = more accurate but slower"},
    "🔮 运行 Monte Carlo 模拟":                 {"en": "🔮 Run Monte Carlo"},
    "正在模拟 {num_paths:,} 条收益路径...（可能需要10-30秒）": {
        "en": "Simulating {num_paths:,} return paths... (may take 10-30 seconds)"
    },
    "✅ 模拟完成！":                            {"en": "✅ Simulation complete!"},
    "模拟失败：":                               {"en": "Simulation failed: "},
    "🔄 重新模拟":                               {"en": "🔄 Re-run Simulation"},
    "👉 下一步：AI 分析":                       {"en": "👉 Next: AI Analysis"},
    "初始投资":                                  {"en": "Initial Investment"},
    "预期终值（中位数）":                       {"en": "Median Final Value"},
    "悲观情景 (P5)":                             {"en": "Pessimistic (P5)"},
    "乐观情景 (P95)":                            {"en": "Optimistic (P95)"},
    "盈利概率":                                  {"en": "Profit Probability"},
    "### 📈 收益路径扇形图":                     {"en": "### 📈 Return Path Fan Chart"},
    "### 📊 终值概率分布":                       {"en": "### 📊 Final Value Distribution"},
    "### 📋 逐年预测":                           {"en": "### 📋 Yearly Projections"},
    "无分布数据":                                {"en": "No distribution data"},
    "年份":                                      {"en": "Year"},
    "悲观(P10)":                                 {"en": "Pessimistic (P10)"},
    "保守(P25)":                                 {"en": "Conservative (P25)"},
    "中位(P50)":                                 {"en": "Median (P50)"},
    "乐观(P75)":                                 {"en": "Optimistic (P75)"},
    "激进(P90)":                                 {"en": "Aggressive (P90)"},

    # =====================================================================
    # SECTION: 05_ai_advisor.py
    # =====================================================================

    "🤖 AI 投资顾问分析":                        {"en": "🤖 AI Advisor Analysis"},
    "⚠️ 请先完成 Monte Carlo 模拟":             {"en": "⚠️ Please complete the Monte Carlo simulation first"},
    "🔄 重新分析":                               {"en": "🔄 Re-analyze"},
    "👉 下一步：下载报告":                       {"en": "👉 Next: Download Report"},
    "### 📋 AI 投资分析内容":                    {"en": "### 📋 AI Analysis Content"},
    "点击下方按钮，AI 将为您生成：":             {"en": "Click the button below and AI will generate:"},
    "- 🎯 投资组合概述与配置理由":               {"en": "- 🎯 Portfolio overview & allocation rationale"},
    "- ⚠️ 主要风险识别与分析":                   {"en": "- ⚠️ Key risk identification & analysis"},
    "- 📈 不同市场情景下的表现预测":             {"en": "- 📈 Performance projections across market scenarios"},
    "- 💡 具体可操作的投资建议":                 {"en": "- 💡 Concrete, actionable investment recommendations"},
    "- 🛡️ 风险提示":                             {"en": "- 🛡️ Risk disclaimers"},
    "*本地 AI 引擎，无需联网，即时生成分析结果。*": {
        "en": "*Local AI engine. No internet needed. Instant analysis.*"
    },
    "🤖 生成 AI 分析":                           {"en": "🤖 Generate AI Analysis"},
    "AI 正在分析您的投资组合...":                {"en": "AI is analyzing your portfolio..."},
    "✅ AI 分析生成完成！":                       {"en": "✅ AI analysis complete!"},
    "AI 分析生成失败：":                          {"en": "AI analysis failed: "},
    "💡 提示：请确认前面的步骤（风险测评、组合优化、模拟）均已完成。": {
        "en": "💡 Tip: Please confirm all previous steps (risk assessment, portfolio, simulation) are complete."
    },
    "## 📝 投资组合概述":                         {"en": "## 📝 Portfolio Overview"},
    "## 🎯 配置理由":                             {"en": "## 🎯 Allocation Rationale"},
    "## ⚠️ 主要风险分析":                         {"en": "## ⚠️ Key Risk Analysis"},
    "## 📈 市场情景分析":                          {"en": "## 📈 Market Scenario Analysis"},
    "## 💡 投资建议":                              {"en": "## 💡 Investment Recommendations"},
    "🔴 高风险":                                   {"en": "🔴 High Risk"},
    "🟡 中风险":                                   {"en": "🟡 Medium Risk"},
    "🟢 低风险":                                   {"en": "🟢 Low Risk"},
    "**风险描述**":                                {"en": "**Risk Description**"},
    "**缓解建议**":                                {"en": "**Mitigation**"},
    "无特定建议":                                  {"en": "No specific advice"},
    "牛市":                                        {"en": "Bull Market"},
    "熊市":                                        {"en": "Bear Market"},
    "震荡市":                                      {"en": "Sideways Market"},
    "**发生概率：**":                              {"en": "**Probability:** "},
    "**组合影响：**":                              {"en": "**Portfolio Impact:** "},
    "投资有风险，过往表现不代表未来收益。本报告仅供参考，不构成投资建议。": {
        "en": "Investing involves risk. Past performance does not guarantee future results. This report is for reference only and does not constitute investment advice."
    },

    # =====================================================================
    # SECTION: 06_report.py
    # =====================================================================

    "📄 投资报告下载":                             {"en": "📄 Report Download"},
    "## 📋 报告包含内容":                          {"en": "## 📋 Report Contents"},
    "生成的PDF报告包含以下章节：":                 {"en": "The generated PDF report includes the following sections:"},
    "1. **封面** - 用户信息、生成日期":            {"en": "1. **Cover** - User info, generation date"},
    "2. **风险测评结果** - 风险等级、评分、各维度分析": {
        "en": "2. **Risk Assessment Results** - Risk level, score, dimensional analysis"
    },
    "3. **投资组合配置** - 持仓明细表、资产配置饼图、关键指标": {
        "en": "3. **Portfolio Allocation** - Holdings table, allocation pie chart, key metrics"
    },
    "4. **Monte Carlo 模拟** - 收益路径扇形图、终值分布直方图、风险统计": {
        "en": "4. **Monte Carlo Simulation** - Return fan chart, final value histogram, risk stats"
    },
    "5. **AI 投资顾问分析** - 组合概述、配置理由、风险分析、市场情景、投资建议": {
        "en": "5. **AI Advisor Analysis** - Portfolio overview, allocation rationale, risk analysis, scenarios, recommendations"
    },
    "6. **风险提示与免责声明**":                   {"en": "6. **Risk Warnings & Disclaimer**"},
    "*注意：PDF 生成包含完整的图表和分析，适合打印和分享。*": {
        "en": "*Note: PDF includes complete charts and analysis, suitable for printing and sharing.*"
    },
    "💡 提示：您尚未生成 AI 分析。PDF 报告将不包含 AI 投资顾问分析部分。": {
        "en": "💡 Tip: You haven't generated AI analysis yet. The PDF will not include the AI advisor section."
    },
    "📥 生成 PDF 报告":                            {"en": "📥 Generate PDF Report"},
    "正在生成专业PDF报告...（包含图表和分析）":   {"en": "Generating professional PDF report... (including charts and analysis)"},
    "✅ 报告生成完成！":                           {"en": "✅ Report generated!"},
    "报告生成失败：":                              {"en": "Report generation failed: "},
    "## 📥 下载报告":                              {"en": "## 📥 Download Report"},
    "文件大小":                                    {"en": "File Size"},
    "状态":                                        {"en": "Status"},
    "✅ 已生成":                                   {"en": "✅ Generated"},
    "📥 下载 PDF 报告":                            {"en": "📥 Download PDF Report"},
    "报告文件未找到，请重新生成。":                 {"en": "Report file not found. Please regenerate."},

    # =====================================================================
    # SECTION: 07_dca_calculator.py
    # =====================================================================

    "💰 定投计算器":                               {"en": "💰 DCA Calculator"},
    "计算每月定额投资的未来收益，或反推达成目标所需的每月投入。": {
        "en": "Calculate future returns of regular monthly investments, or work backward to find the monthly amount needed to reach a goal."
    },
    "投资年限":                                    {"en": "Investment Period"},
    "预期年化收益率":                              {"en": "Expected Annual Return"},
    "计划持续定投的年数":                          {"en": "Years you plan to continue DCA"},
    "预期的年均投资回报率（参考：沪深300长期约8-10%，债券约3-5%，上限50%用于极端情景测试）": {
        "en": "Expected annual return (ref: CSI 300 ~8-10% long-term, bonds ~3-5%. Max 50% for extreme scenario testing)"
    },
    "计算模式":                                    {"en": "Calculation Mode"},
    "📈 正算：我每月投X，将来能有多少？":          {"en": "📈 Forward: If I invest X/month, how much will I have?"},
    "🎯 反算：我想攒到Y，每月要投多少？":          {"en": "🎯 Reverse: To reach Y, how much per month?"},
    "目标金额 (¥)":                                {"en": "Target Amount (¥)"},
    "你希望到期时攒到的总金额":                    {"en": "The total amount you want to accumulate by the end"},
    "每月定投金额 (¥)":                            {"en": "Monthly Investment (¥)"},
    "你计划每个月固定投入的金额":                  {"en": "The amount you plan to invest each month"},
    "📊 开始计算":                                 {"en": "📊 Calculate"},
    "### 📈 定投收益预测":                          {"en": "### 📈 DCA Return Projection"},
    "每月投入":                                    {"en": "Monthly Investment"},
    "累计投入":                                    {"en": "Total Invested"},
    "投资收益":                                    {"en": "Investment Return"},
    "年后终值":                                    {"en": "-Year Final Value"},
    "### 🎯 定投目标规划":                          {"en": "### 🎯 DCA Goal Planning"},
    "目标金额":                                    {"en": "Target Amount"},
    "每月需投入":                                  {"en": "Required Monthly"},
    "差额":                                        {"en": "Difference"},
    "基于预期收益率反算的每月最低定投额":          {"en": "Minimum monthly DCA amount based on expected return"},
    "刚好达标 ✅":                                 {"en": "Exactly on target ✅"},
    "略有不足":                                    {"en": "Slightly short"},
    "超额完成 🎉":                                 {"en": "Exceeding target 🎉"},
    "目标金额太小或期限太长，每月投入几乎为零。请调整参数。": {
        "en": "Target too small or horizon too long; required monthly amount is near zero. Please adjust parameters."
    },
    "累计本金":                                    {"en": "Total Principal"},
    "资产增长曲线":                                {"en": "Asset Growth Curve"},
    "总资产":                                      {"en": "Total Assets"},
    "### 📋 逐年明细":                              {"en": "### 📋 Yearly Breakdown"},
    "当年投入":                                    {"en": "Annual Investment"},
    "累计收益":                                    {"en": "Cumulative Return"},
    "收益占比":                                    {"en": "Return Share"},

    # =====================================================================
    # SECTION: 08_market_dashboard.py
    # =====================================================================

    "📊 市场仪表盘":                               {"en": "📊 Market Dashboard"},
    "实时市场数据概览 · 数据来源：AKShare & Yahoo Finance": {
        "en": "Real-time market data overview · Sources: AKShare & Yahoo Finance"
    },
    "🔄 刷新行情":                                 {"en": "🔄 Refresh Quotes"},
    "立即更新指数价格和宏观指标（走势图和ETF涨跌榜每小时更新一次）": {
        "en": "Update index prices and macro indicators immediately (charts and ETF rankings update hourly)"
    },
    "🕐 行情更新于 ":                              {"en": "🕐 Quotes updated at "},
    "### 🏛️ 主要指数":                             {"en": "### 🏛️ Major Indices"},
    "📡 指数数据暂不可用，请点击刷新按钮重试":     {"en": "📡 Index data temporarily unavailable. Click refresh to retry."},
    "数据获取失败":                                {"en": "Data fetch failed"},
    "### 🏭 行业板块表现":                          {"en": "### 🏭 Sector Performance"},
    "切换市场":                                    {"en": "Switch Market"},
    "📡 行业板块数据暂不可用":                     {"en": "📡 Sector data temporarily unavailable"},
    "📡 行业数据格式异常，请稍后重试":             {"en": "📡 Sector data format error. Please retry later."},
    "全部板块":                                    {"en": "All Sectors"},
    "涨跌幅 %":                                    {"en": "Change %"},
    "📋 查看全部行业排名":                          {"en": "📋 View All Sector Rankings"},
    "板块名称":                                    {"en": "Sector Name"},
    "涨跌幅 (%)":                                  {"en": "Change (%)"},
    "最新价":                                      {"en": "Latest Price"},
    "成交量":                                      {"en": "Volume"},
    "### 🌍 宏观指标":                             {"en": "### 🌍 Macro Indicators"},
    "📡 宏观数据暂不可用":                         {"en": "📡 Macro data temporarily unavailable"},
    "加载失败":                                    {"en": "Load failed"},
    "### 📈 ETF 涨跌榜":                           {"en": "### 📈 ETF Rankings"},
    "基于5日累计收益排名":                         {"en": "Ranked by 5-day cumulative return"},
    "📡 ETF 数据暂不可用":                         {"en": "📡 ETF data temporarily unavailable"},
    "#### 🔴 涨幅榜":                              {"en": "#### 🔴 Top Gainers"},
    "#### 🟢 跌幅榜":                              {"en": "#### 🟢 Top Losers"},
    "暂无上涨ETF":                                 {"en": "No ETFs with gains"},
    "暂无下跌ETF":                                 {"en": "No ETFs with losses"},
    "⚠️ 数据仅供参考，不构成投资建议。指数和ETF价格可能存在15-30分钟延迟。数据来源：Yahoo Finance（实时行情）、AKShare（走势图及ETF数据）。点击「刷新行情」仅更新价格数据；走势图和ETF涨跌榜每小时自动更新。": {
        "en": "⚠️ Data is for reference only, not investment advice. Index and ETF prices may be delayed 15-30 minutes. Sources: Yahoo Finance (live quotes), AKShare (charts & ETF data). 'Refresh Quotes' only updates prices; charts and ETF rankings update hourly."
    },
    "⚡ 正在获取实时行情...（约2-3秒）":           {"en": "⚡ Fetching live quotes... (~2-3 seconds)"},
    "📈 正在加载走势图和ETF数据...（首次约10-15秒，后续从缓存秒出）": {
        "en": "📈 Loading charts and ETF data... (~10-15s first load, instant from cache thereafter)"
    },

    # =====================================================================
    # SECTION: 09_etf_comparison.py
    # =====================================================================

    "📈 ETF 对比工具":                             {"en": "📈 ETF Comparison"},
    "选两只 ETF，一眼看出谁更强 —— 红色突出优胜方": {
        "en": "Pick two ETFs and instantly see which is stronger — winner highlighted in red"
    },
    "ETF A":                                       {"en": "ETF A"},
    "ETF B":                                       {"en": "ETF B"},
    "周期":                                         {"en": "Period"},
    "1年":                                          {"en": "1 Year"},
    "3年":                                          {"en": "3 Years"},
    "5年":                                          {"en": "5 Years"},
    "10年":                                         {"en": "10 Years"},
    "20年":                                         {"en": "20 Years"},
    "📊 开始对比":                                  {"en": "📊 Compare"},
    "请选择两只不同的 ETF 进行对比":                {"en": "Please select two different ETFs to compare"},
    "正在对比 ":                                    {"en": "Comparing "},
    " vs ":                                         {"en": " vs "},
    "对比周期：":                                   {"en": "Period: "},
    "📉 更多分析图表":                              {"en": "📉 More Analysis Charts"},
    "### 📋 可选 ETF 一览":                         {"en": "### 📋 Available ETFs"},
    "从下表中选择两只 ETF，点击「开始对比」进行分析": {
        "en": "Select two ETFs from the table below and click 'Compare' to analyze"
    },
    "最新价格":                                     {"en": "Latest Price"},
    "累计收益":                                     {"en": "Cumulative Return"},
    "年化收益":                                     {"en": "Annualized Return"},
    "年化波动率":                                   {"en": "Annualized Volatility"},
    "最大回撤":                                     {"en": "Max Drawdown"},
    "Calmar比率":                                   {"en": "Calmar Ratio"},
    "1个月收益":                                    {"en": "1-Month Return"},
    "3个月收益":                                    {"en": "3-Month Return"},
    "6个月收益":                                    {"en": "6-Month Return"},
    "1年收益":                                      {"en": "1-Year Return"},
    "最佳月份":                                     {"en": "Best Month"},
    "最差月份":                                     {"en": "Worst Month"},
    "正收益月份占比":                               {"en": "% Positive Months"},
    "### 指标对比":                                 {"en": "### Metric Comparison"},
    "🔴 红色 = 更优 —— 绿色 = 较劣":               {"en": "🔴 Red = Better —— Green = Worse"},
    "### 🔗 相关性":                                {"en": "### 🔗 Correlation"},
    "判定系数 R²":                                  {"en": "R² Coefficient"},
    "共同上涨":                                     {"en": "Up Together"},
    "共同下跌":                                     {"en": "Down Together"},
    "相关程度":                                     {"en": "Correlation Level"},
    "高度相关":                                     {"en": "Highly Correlated"},
    "中度相关":                                     {"en": "Moderately Correlated"},
    "低度相关":                                     {"en": "Weakly Correlated"},
    "#### 📉 回撤曲线":                             {"en": "#### 📉 Drawdown Curves"},
    "#### 🟣 60日滚动相关性":                       {"en": "#### 🟣 60-Day Rolling Correlation"},
    "#### 📊 日收益分布":                           {"en": "#### 📊 Daily Return Distribution"},
    "数据不足（至少需要20个交易日）":               {"en": "Insufficient data (minimum 20 trading days)"},
    "两只 ETF 数据均获取失败，请稍后重试":          {"en": "Failed to fetch data for both ETFs. Please retry later."},
    " 数据获取失败":                                {"en": " data fetch failed"},
    "数据不足以绘制走势图":                         {"en": "Insufficient data to plot chart"},

    # =====================================================================
    # SECTION: 10_investment_glossary.py
    # =====================================================================

    "📚 投资术语百科":                             {"en": "📚 Investment Glossary"},
    "🔍 搜索术语":                                 {"en": "🔍 Search Terms"},
    "输入中文或英文关键词搜索…":                   {"en": "Search by Chinese or English keyword…"},
    "类别筛选":                                    {"en": "Filter by Category"},
    "📂 全部":                                     {"en": "📂 All"},
    "入门":                                        {"en": "Beginner"},
    "进阶":                                        {"en": "Intermediate"},
    "高级":                                        {"en": "Advanced"},
    "相关术语：":                                  {"en": "Related: "},
    "📭 没有找到匹配的术语，试试更换关键词或类别筛选。": {
        "en": "📭 No matching terms found. Try a different keyword or category filter."
    },
    "📚 投资术语百科 — 磐策 PánCè 知识库。内容仅供参考学习，不构成投资建议。": {
        "en": "📚 Investment Glossary — 磐策 PánCè Knowledge Base. For educational reference only, not investment advice."
    },

    # ── Glossary category names (from YAML) ──────────────────────────────
    "基础概念":                              {"en": "Basic Concepts"},
    "股票市场":                              {"en": "Stock Market"},
    "基金与ETF":                             {"en": "Funds & ETFs"},
    "债券与固收":                            {"en": "Bonds & Fixed Income"},
    "风险管理":                              {"en": "Risk Management"},
    "财务指标":                              {"en": "Financial Metrics"},
    "宏观经济":                              {"en": "Macroeconomics"},
    "投资策略":                              {"en": "Investment Strategy"},
    "全部":                                  {"en": "All"},

    # =====================================================================
    # SECTION: 11_market_thermometer.py
    # =====================================================================

    "🌡️ 市场温度计":                               {"en": "🌡️ Market Thermometer"},
    "综合 PE 估值 + 价格偏离均线，判断当前 A 股市场冷热 · 数据每天自动更新 · PE 来源：中证指数官网 · 覆盖上证50 / 沪深300 / 中证500 / 中证1000": {
        "en": "Combines PE valuation + price deviation from MA to gauge A-share market temperature. Auto-updates daily. PE source: CSIndex. Covers SSE 50 / CSI 300 / CSI 500 / CSI 1000."
    },
    "### 📊 指数估值温度":                           {"en": "### 📊 Index Valuation Temperature"},
    "数据暂不可用":                                  {"en": "Data temporarily unavailable"},
    "PE(TTM)":                                       {"en": "PE (TTM)"},
    "偏离200日均线":                                 {"en": "Deviation from 200MA"},
    "仅PE估值":                                      {"en": "PE Valuation Only"},
    "### 📈 PE 估值走势":                            {"en": "### 📈 PE Valuation Trend"},
    "📡 PE 历史数据暂不可用（中证指数官网仅提供近20个交易日数据）": {
        "en": "📡 PE history unavailable (CSIndex only provides ~20 trading days of data)"
    },
    "选择指数":                                      {"en": "Select Index"},
    "📡 该指数 PE 历史数据暂不可用":                 {"en": "📡 PE history unavailable for this index"},
    "📡 PE 数据点不足，无法绘制走势图":              {"en": "📡 Insufficient PE data points to plot trend"},
    "💡 PE数据来自中证指数官网，每日盘后更新。走势图展示近20个交易日。": {
        "en": "💡 PE data from CSIndex, updated daily after market close. Chart shows ~20 trading days."
    },
    "### 📊 价格偏离均线":                           {"en": "### 📊 Price vs MA Deviation"},
    "📡 价格数据暂不可用":                           {"en": "📡 Price data temporarily unavailable"},
    "📡 该指数价格数据暂不可用":                     {"en": "📡 Price data unavailable for this index"},
    "收盘价":                                        {"en": "Close Price"},
    "200日均线":                                     {"en": "200-Day MA"},
    "当前偏离200日均线: ":                           {"en": "Current deviation from 200MA: "},
    " · 价格高于均线 → 可能偏热 · 价格低于均线 → 可能偏冷": {
        "en": " · Price above MA → potentially overvalued · Price below MA → potentially undervalued"
    },
    "### 📊 A 股综合温度":                           {"en": "### 📊 A-Share Composite Temperature"},
    "📡 综合温度数据暂不可用":                       {"en": "📡 Composite temperature data temporarily unavailable"},
    "温度构成：PE估值（权重60%）+ 价格偏离200日均线（权重40%）": {
        "en": "Temperature formula: PE valuation (60%) + Price deviation from 200MA (40%)"
    },
    "🌡️ 市场温度计 — 磐策 PánCè · 温度 = PE估值(60%) + 价格偏离200日均线(40%) · PE数据来源：中证指数官网 csindex.com.cn · 仅供参考，不构成投资建议。 · 数据更新于 ": {
        "en": "🌡️ Market Thermometer — 磐策 PánCè · Temperature = PE (60%) + Price vs 200MA deviation (40%) · PE source: csindex.com.cn · For reference only, not investment advice. · Updated: "
    },
    "🌡️ 正在计算市场温度...（首次约 5-10 秒，后续秒出）": {
        "en": "🌡️ Computing market temperature... (~5-10s first load, instant thereafter)"
    },
    "🧊 0°":                                        {"en": "🧊 0°"},
    "💥 100°":                                      {"en": "💥 100°"},

    # ── 11_market_thermometer: index info ─────────────────────────────────
    "大盘蓝筹":                                 {"en": "Large-cap Blue Chip"},
    "核心基准":                                 {"en": "Core Benchmark"},
    "中盘成长":                                 {"en": "Mid-cap Growth"},
    "小盘风向标":                               {"en": "Small-cap Bellwether"},
    "🧊 极度低估":                              {"en": "🧊 Deep Undervalue"},
    "❄️ 偏低":                                  {"en": "❄️ Cool"},
    "🌡️ 适中":                                  {"en": "🌡️ Moderate"},
    "🔥 偏贵":                                  {"en": "🔥 Expensive"},
    "💥 高估":                                  {"en": "💥 Overvalued"},
    "估值处于历史底部区域，可积极加仓":         {"en": "Valuation at historical bottom. Consider aggressive buying."},
    "估值低于正常水平，可适当多投":             {"en": "Valuation below normal. Consider increasing investments."},
    "估值处于合理区间，维持正常定投":           {"en": "Valuation in reasonable range. Maintain regular DCA."},
    "估值高于正常水平，建议减少定投金额":       {"en": "Valuation above normal. Consider reducing DCA amount."},
    "估值处于历史高位，建议暂停定投并考虑减仓": {"en": "Valuation at historical high. Consider pausing DCA and reducing positions."},
    "维持正常定投":                             {"en": "Maintain regular DCA"},

    # =====================================================================
    # SECTION: 12_temperature_dca.py
    # =====================================================================

    "🌡️ 智能温度定投":                               {"en": "🌡️ Temperature DCA"},
    "基于市场估值温度动态调整每期定投金额 · 市场冷时多投，热时少投 · 回测验证，数据驱动决策": {
        "en": "Dynamically adjusts DCA amount based on market valuation temperature. Buy more when cold, less when hot. Backtest-verified, data-driven."
    },
    "### ⚙️ 策略配置":                               {"en": "### ⚙️ Strategy Configuration"},
    "基准指数":                                      {"en": "Benchmark Index"},
    "沪深300":                                       {"en": "CSI 300"},
    "上证50":                                        {"en": "SSE 50"},
    "中证500":                                       {"en": "CSI 500"},
    "中证1000":                                      {"en": "CSI 1000"},
    "回测基准指数，沪深300最能代表A股整体走势":     {"en": "Backtest benchmark. CSI 300 best represents the overall A-share market."},
    "回测年限":                                      {"en": "Backtest Period"},
    "回测历史年数。年限越长，穿越的牛熊周期越多，结论越可靠": {
        "en": "Years of history to backtest. Longer periods cover more bull/bear cycles for more reliable conclusions."
    },
    "基准月投 (¥)":                                  {"en": "Monthly Investment (¥)"},
    "温度适中(40-60°C)时的标准月投金额。市场冷热时按倍率自动调整": {
        "en": "Standard monthly amount when temperature is moderate (40-60°C). Automatically adjusted by multiplier in hot/cold markets."
    },
    "温度策略":                                      {"en": "Strategy"},
    "积极=低温重仓高位空仓 · 适中=均衡加减 · 保守=温和微调": {
        "en": "Aggressive = heavy when cold, empty when hot · Moderate = balanced · Conservative = gentle tweaks"
    },
    "📐 温度→倍率映射 · ":                           {"en": "📐 Temperature → Multiplier · "},
    "型 · ":                                          {"en": " · "},
    "🧊 极度低估<br>0–20°C":                          {"en": "🧊 Deep Undervalue<br>0–20°C"},
    "❄️ 偏低<br>20–40°C":                            {"en": "❄️ Cool<br>20–40°C"},
    "🌡️ 适中<br>40–60°C":                            {"en": "🌡️ Moderate<br>40–60°C"},
    "🔥 偏贵<br>60–80°C":                            {"en": "🔥 Expensive<br>60–80°C"},
    "💥 高估<br>80–100°C":                           {"en": "💥 Overvalued<br>80–100°C"},
    "### 📈 回测资产曲线对比":                         {"en": "### 📈 Backtest Equity Curves"},
    "🌡️ 温度定投":                                   {"en": "🌡️ Temp DCA"},
    "📋 普通定投":                                   {"en": "📋 Regular DCA"},
    "💰 一次性买入":                                 {"en": "💰 Lump Sum"},
    "累计投入":                                      {"en": "Total Invested"},
    "市场温度":                                      {"en": "Market Temperature"},
    "### 📊 策略对比分析":                             {"en": "### 📊 Strategy Comparison"},
    "#### 核心指标":                                  {"en": "#### Key Metrics"},
    "年化收益 CAGR":                                  {"en": "CAGR"},
    "#### 🔍 为什么温度定投呈现这个结果？":           {"en": "#### 🔍 Why does Temperature DCA perform this way?"},
    "🧊 低温区间 (0-40°C)":                          {"en": "🧊 Cold Zone (0-40°C)"},
    "🔥 高温区间 (60-100°C)":                         {"en": "🔥 Hot Zone (60-100°C)"},
    "💰 现金池动态":                                  {"en": "💰 Cash Pool Dynamics"},
    "额外加仓（低位多买）":                           {"en": "Extra buying (accumulate at lows)"},
    "暂扣少投（高位避风险）":                         {"en": "Reduced buying (avoid risk at highs)"},
    "最高积存金额":                                   {"en": "Max cash reserve"},
    "### 📋 温度定投逐年明细":                          {"en": "### 📋 Yearly Breakdown"},
    "数据不足以生成逐年明细":                          {"en": "Insufficient data for yearly breakdown"},
    "当年投入":                                       {"en": "Annual Investment"},
    "年末市值":                                       {"en": "Year-End Value"},
    "平均温度":                                       {"en": "Avg Temperature"},
    "平均倍率":                                       {"en": "Avg Multiplier"},
    "### 🔬 信号验证：温度能否预测未来收益？":        {"en": "### 🔬 Signal Validation: Does temperature predict future returns?"},
    "如果温度信号有效，低温应该对应未来较高的收益（负相关）。这是整个温度定投策略的实证基础。": {
        "en": "If the temperature signal is valid, lower temperatures should correspond to higher future returns (negative correlation). This is the empirical foundation of the entire strategy."
    },
    "正在运行信号验证...（首次约 5-10 秒）":         {"en": "Running signal validation... (~5-10s first time)"},
    "⚠️ 信号验证暂不可用：":                          {"en": "⚠️ Signal validation unavailable: "},
    "✅ 统计显著":                                    {"en": "✅ Statistically Significant"},
    "⚠️ 不显著":                                     {"en": "⚠️ Not Significant"},
    "#### 📊 相关分析":                               {"en": "#### 📊 Correlation Analysis"},
    "p 值":                                           {"en": "p-value"},
    "R²":                                             {"en": "R²"},
    "显著性":                                         {"en": "Significance"},
    "样本量":                                         {"en": "Sample Size"},
    "#### 温度分桶：各区间未来收益对比":              {"en": "#### Temperature Buckets: Forward Returns by Zone"},
    "极度低估":                                       {"en": "Deep Undervalue"},
    "偏低":                                           {"en": "Cool"},
    "适中":                                           {"en": "Moderate"},
    "偏贵":                                           {"en": "Expensive"},
    "高估":                                           {"en": "Overvalued"},
    "平均未来12月收益":                               {"en": "Avg Forward 12M Return"},
    "正收益率":                                       {"en": "Positive Return Rate"},
    "### 📊 市场环境分解：什么情况下温度定投有效？":  {"en": "### 📊 Regime Decomposition: When does Temperature DCA work?"},
    "市场环境数据不足以进行分解分析":                 {"en": "Insufficient data for regime decomposition"},
    "🐂 牛市":                                       {"en": "🐂 Bull"},
    "🐻 熊市":                                       {"en": "🐻 Bear"},
    "📊 震荡":                                       {"en": "📊 Sideways"},
    "本期无此环境":                                   {"en": "No data for this regime"},
    "🌡️ 温度":                                      {"en": "🌡️ Temp DCA"},
    "📋 普通":                                       {"en": "📋 Regular"},
    "💰 一次性":                                     {"en": "💰 Lump Sum"},
    "### 🚶 Walk-Forward 样本外检验":                 {"en": "### 🚶 Walk-Forward Out-of-Sample Validation"},
    "正在运行 Walk-Forward 检验...（":                {"en": "Running Walk-Forward validation... ("},
    "年训练 → ":                                      {"en": "yr training → "},
    "年测试，首次约 20-30 秒）":                      {"en": "yr testing, ~20-30s first time)"},
    "⚠️ Walk-Forward 检验暂不可用：":                 {"en": "⚠️ Walk-Forward validation unavailable: "},
    "🔧 训练窗 · ":                                  {"en": "🔧 Training Window · "},
    "👁️ 测试窗 · ":                                  {"en": "👁️ Test Window · "},
    "（样本外）":                                     {"en": " (Out-of-Sample)"},
    "网格搜索":                                       {"en": "Grid Search"},
    "超额":                                           {"en": "Excess"},
    "夏普":                                           {"en": "Sharpe"},
    "参数锁定，未接触":                               {"en": "Params locked, unseen data"},
    "只看一遍":                                       {"en": "One look only"},
    "#### 📊 参数优化网格":                           {"en": "#### 📊 Parameter Grid Search"},
    "激进":                                           {"en": "Aggressive"},
    "PE 权重":                                        {"en": "PE Weight"},
    "### 🧠 行为金融视角：为什么温度定投理论上应该有效？": {
        "en": "### 🧠 Behavioral Finance: Why should Temperature DCA work in theory?"
    },
    "### 🌡️ 实时市场温度 · 当前建议":                {"en": "### 🌡️ Live Market Temperature · Current Advice"},
    "正在获取当前市场温度...":                        {"en": "Fetching current market temperature..."},
    "📡 实时温度数据暂不可用，请稍后刷新":            {"en": "📡 Live temperature data unavailable. Please refresh."},
    " 当前温度":                                      {"en": " Current Temperature"},
    " 实时温度暂不可用":                              {"en": " Live temperature unavailable"},
    "📐 ":                                            {"en": "📐 "},
    "型策略 · 当前决策":                              {"en": " Strategy · Current Decision"},
    "基准月投":                                       {"en": "Monthly Base"},
    "温度倍率":                                       {"en": "Temperature Multiplier"},
    "建议月投":                                       {"en": "Suggested Monthly"},
    "🌡️ 智能温度定投 — 磐策 PánCè 旗舰功能 · 回测区间: ": {
        "en": "🌡️ Temperature DCA — 磐策 PánCè Flagship · Backtest: "
    },
    " 至 ":                                           {"en": " to "},
    " · 共 ":                                         {"en": " · "},
    " 个月 · 温度信号: ":                             {"en": " months · Signal: "},
    " · 数据源: ":                                    {"en": " · Source: "},
    " · 数据更新于 ":                                 {"en": " · Updated: "},
    " · 历史回测不代表未来收益，仅供参考":           {"en": " · Past backtest results do not guarantee future returns. For reference only."},
    "📡 **数据覆盖说明**：":                          {"en": "📡 **Data Coverage Note**: "},
    "支持的指数: ":                                   {"en": "Supported indices: "},
    "🔥 积极":                                       {"en": "🔥 Aggressive"},
    "⚖️ 适中":                                       {"en": "⚖️ Moderate"},
    "🛡️ 保守":                                       {"en": "🛡️ Conservative"},
    "回测年限太短，无法进行有意义的 Walk-Forward 检验（至少需要2年训练 + 1年测试）。请增加回测年限。": {
        "en": "Backtest period too short for meaningful Walk-Forward validation (need ≥2 years training + 1 year testing). Please increase the backtest period."
    },

    # ── 12_temperature_dca: mechanism analysis ──────────────────────────────
    "共 {cold_months} 个月 · 估值偏低":              {"en": "{cold_months} months · undervalued"},
    "共 {hot_months} 个月 · 估值偏高":               {"en": "{hot_months} months · overvalued"},
    "峰值日期 {peak_d}":                             {"en": "Peak date {peak_d}"},

    # ── 12_temperature_dca: signal validation ───────────────────────────────
    "回归线 (r={r:.3f})":                            {"en": "Regression (r={r:.3f})"},
    "月度数据点":                                     {"en": "Monthly data points"},
    "⚠️ 信号验证暂不可用：{error}":                  {"en": "⚠️ Signal validation unavailable: {error}"},
    "正收益率 {rate}% · n={n}":                       {"en": "Pos return rate {rate}% · n={n}"},
    "{n} 个月":                                       {"en": "{n} months"},

    # ── 12_temperature_dca: regime decomposition ────────────────────────────
    "{months} 个月 · 平均温度 {avg_temp:.0f}°C":     {"en": "{months} months · avg temp {avg_temp:.0f}°C"},
    "💡 <b>核心认知</b>：没有任何策略在所有市场中都最优。温度定投的价值定位是——用牛市中的相对落后，换取熊市和震荡市中的显著优势。这是一个明确、可预期的 trade-off，而非策略缺陷。": {
        "en": "💡 <b>Key insight</b>: No strategy outperforms in all market regimes. Temperature DCA's value proposition is trading relative underperformance in bull markets for significant advantages in bear and sideways markets. This is a conscious trade-off, not a strategy flaw."
    },

    # ── 12_temperature_dca: walk-forward ────────────────────────────────────
    "网格搜索 {n} 种组合，最优：PE {pw:.0%} + {label}": {
        "en": "Grid searched {n} combos, best: PE {pw:.0%} + {label}"
    },
    "个月":                                          {"en": " months"},
    "温度":                                           {"en": "Temp"},
    "普通":                                           {"en": "Regular"},
    "超额":                                           {"en": "Excess"},
    "夏普":                                           {"en": "Sharpe"},
    "变动":                                           {"en": "Change"},
    "年":                                             {"en": "yr"},
    "个月 · 参数锁定，未接触":                       {"en": " months · params locked, unseen"},
    "只看一遍":                                       {"en": "One look only"},
    "💡 <b>方法论</b>：Walk-Forward 是量化策略验证的黄金标准。训练窗内可自由探索参数，测试窗只看一次。若样本外仍然有效，则策略不是过拟合的产物——这正是学术论文和机构级策略验收的核心方法。": {
        "en": "💡 <b>Methodology</b>: Walk-Forward is the gold standard for quant strategy validation. Parameters are explored freely in the training window; the test window is examined only once. If the strategy still works out-of-sample, it is not a product of overfitting — this is the core validation method used in academic papers and institutional strategy evaluation."
    },
    "⚠️ Walk-Forward 检验暂不可用：{error}":         {"en": "⚠️ Walk-Forward validation unavailable: {error}"},

    # ── 12_temperature_dca: behavioral finance ──────────────────────────────
    "低估区间 (0-40°C)":                              {"en": "Undervalued Zone (0-40°C)"},
    "损失厌恶 (Loss Aversion)":                       {"en": "Loss Aversion"},
    "市场恐慌时，投资者因害怕继续亏损而不敢买入。温度定投通过**自动加仓到 1.25–2.0 倍**，用规则强制逆情绪操作，克服'该买不敢买'的心理障碍。": {
        "en": "During market panic, investors fear further losses and hesitate to buy. Temperature DCA forces contrarian action by **auto-increasing to 1.25–2.0x**, overcoming the 'too scared to buy' psychological barrier."
    },
    "高估区间 (60-100°C)":                            {"en": "Overvalued Zone (60-100°C)"},
    "羊群效应 (Herd Behavior)":                       {"en": "Herd Behavior"},
    "市场狂热时，投资者容易追涨杀跌。温度定投通过**强制少投至 0–0.75 倍**，在高位自动刹车，避免'别人都在买所以我也买'的从众陷阱。": {
        "en": "During market euphoria, investors tend to chase rallies and panic-sell. Temperature DCA **forces reduced buying to 0–0.75x**, applying automatic brakes at highs and avoiding the 'everyone is buying so I will too' herding trap."
    },
    "适中区间 (40-60°C)":                             {"en": "Moderate Zone (40-60°C)"},
    "锚定效应 (Anchoring)":                           {"en": "Anchoring"},
    "投资者容易被近期价格'锚定'，在正常波动中过度反应。温度定投在估值合理时**维持基准定投**，不被短期价格波动所锚定，保持纪律性投资节奏。": {
        "en": "Investors tend to be 'anchored' by recent prices and overreact to normal fluctuations. Temperature DCA **maintains the base DCA amount** when valuations are reasonable, staying disciplined and unswayed by short-term price movements."
    },
    "克服：":                                         {"en": "Overcomes: "},
    "💡 <b>学术定位</b>：温度定投本质上是一种<b>规则化的行为金融干预工具</b>。它不依赖市场预测能力，而是通过系统性地抵消投资者的认知偏差来创造价值。这一视角将系统从\"一个 Python 回测工具\"提升为\"有行为金融学理论根基的量化决策系统\"——这正是 BA/FinTech 研究生项目最看重的思维深度。": {
        "en": "💡 <b>Academic positioning</b>: Temperature DCA is fundamentally a <b>rule-based behavioral finance intervention tool</b>. It does not rely on market forecasting ability; instead, it creates value by systematically counteracting investors' cognitive biases. This perspective elevates the system from 'a Python backtesting tool' to 'a quantitative decision system grounded in behavioral finance theory' — precisely the depth of thinking that BA/FinTech graduate programs value most."
    },

    # ── 12_temperature_dca: real-time suggestion ────────────────────────────
    "当前温度":                                       {"en": "Current Temperature"},
    "{idx_name} 实时温度暂不可用":                    {"en": "{idx_name} live temperature unavailable"},
    "型策略 · 当前决策":                              {"en": " Strategy · Current Decision"},
    "💰 本月存入现金池 <b>¥{saved:,.0f}</b>（温度偏高，暂扣）": {
        "en": "💰 Set aside <b>¥{saved:,.0f}</b> into cash pool this month (elevated temperature, deferred)"
    },
    "等温度回落至60°C以下，现金池自动释放加仓":     {"en": "When temperature drops below 60°C, cash pool auto-releases for buying"},
    "🚀 从现金池额外投入 <b>¥{extra:,.0f}</b>（温度偏低，加仓买入）": {
        "en": "🚀 Deploy extra <b>¥{extra:,.0f}</b> from cash pool (low temperature, buying opportunity)"
    },
    "累计现金池余额":                                 {"en": "Cumulative Cash Pool Balance"},

    # ── 12_temperature_dca: footer ──────────────────────────────────────────
    "🌡️ 智能温度定投 — 磐策 PánCè 旗舰功能 · 回测区间: {start} 至 {end} · 共 {n} 个月 · 温度信号: {signal} · 数据源: {source} · 数据更新于 {ts} · 历史回测不代表未来收益，仅供参考": {
        "en": "🌡️ Temperature DCA — 磐策 PánCè Flagship · Backtest: {start} to {end} · {n} months · Signal: {signal} · Source: {source} · Updated: {ts} · Past backtest results do not guarantee future returns. For reference only."
    },
    "PE估值(60%) + MA偏离(40%)":                     {"en": "PE (60%) + MA Dev (40%)"},
    "MA偏离(100%)":                                   {"en": "MA Dev (100%)"},
    "📡 **数据覆盖说明**：{note}":                    {"en": "📡 **Data Coverage Note**: {note}"},

    # ── 12_temperature_dca: misc ────────────────────────────────────────────
    "支持的指数: {indices}":                          {"en": "Supported indices: {indices}"},
    "🔄 正在运行历史回测...（首次约 5-10 秒，后续秒出）": {
        "en": "🔄 Running historical backtest... (~5-10s first time, instant thereafter)"
    },
    "PE权重=%{x}<br>策略=%{y}<br>夏普=%{z:.2f}<extra></extra>": {
        "en": "PE Weight=%{x}<br>Strategy=%{y}<br>Sharpe=%{z:.2f}<extra></extra>"
    },

    # ── 12_temperature_dca: hovertemplates ──────────────────────────────────
    "%{x|%Y-%m}<br>温度定投: ¥%{y:,.0f}<extra></extra>": {
        "en": "%{x|%Y-%m}<br>Temp DCA: ¥%{y:,.0f}<extra></extra>"
    },
    "%{x|%Y-%m}<br>普通定投: ¥%{y:,.0f}<extra></extra>": {
        "en": "%{x|%Y-%m}<br>Regular DCA: ¥%{y:,.0f}<extra></extra>"
    },
    "%{x|%Y-%m}<br>一次性: ¥%{y:,.0f}<extra></extra>": {
        "en": "%{x|%Y-%m}<br>Lump Sum: ¥%{y:,.0f}<extra></extra>"
    },
    "%{x|%Y-%m}<br>累计投入: ¥%{y:,.0f}<extra></extra>": {
        "en": "%{x|%Y-%m}<br>Total Invested: ¥%{y:,.0f}<extra></extra>"
    },
    "%{x|%Y-%m}<br>温度: %{y:.0f}°C<extra></extra>": {
        "en": "%{x|%Y-%m}<br>Temp: %{y:.0f}°C<extra></extra>"
    },
    "温度: %{x:.0f}°C<br>未来12月收益: %{y:.1f}%<extra></extra>": {
        "en": "Temp: %{x:.0f}°C<br>Fwd 12M Return: %{y:.1f}%<extra></extra>"
    },
    "温度: %{x:.0f}°C<br>预测收益: %{y:.1f}%<extra></extra>": {
        "en": "Temp: %{x:.0f}°C<br>Predicted Return: %{y:.1f}%<extra></extra>"
    },

    # =====================================================================
    # SECTION: Dynamic format strings (used across multiple pages)
    # =====================================================================

    "{x}年":                                         {"en": "{x} years"},

    # =====================================================================
    # SECTION: Dynamic glossary count strings
    # =====================================================================

    "中英双语投资百科，随时随地查阅金融术语 · 共收录 **{n}** 个术语": {
        "en": "Bilingual investment encyclopedia. Look up financial terms anytime. **{n}** terms total"
    },
    "找到 **{n}** / {total} 个术语": {
        "en": "Found **{n}** / {total} terms"
    },

    # =====================================================================
    # SECTION: Dynamic temperature composite string
    # =====================================================================

    "综合温度 **{pct:.0f}°C**": {
        "en": "Composite Temperature **{pct:.0f}°C**"
    },

    # =====================================================================
    # SECTION: Additional dynamic strings
    # =====================================================================
    "第{year}年":                            {"en": "Year {year}"},
    "{ratio}% 回报率":                       {"en": "{ratio}% return"},
    "第 %{x} 年<br>累计本金: ¥%{y:,.0f}<extra></extra>": {
        "en": "Yr %{x}<br>Cum. Principal: ¥%{y:,.0f}<extra></extra>"
    },
    "第 %{x} 年<br>累计总值: ¥%{y:,.0f}<extra></extra>": {
        "en": "Yr %{x}<br>Cum. Value: ¥%{y:,.0f}<extra></extra>"
    },
    "第 %{x} 年<br>总资产: ¥%{y:,.0f}<extra></extra>": {
        "en": "Yr %{x}<br>Total Assets: ¥%{y:,.0f}<extra></extra>"
    },
    "目标: ¥{target:,.0f}":                  {"en": "Target: ¥{target:,.0f}"},
    "年数":                                  {"en": "Years"},
    "金额 (¥)":                              {"en": "Amount (¥)"},
    "起点 = 100":                            {"en": "Start = 100"},
    "Pearson 相关系数":                      {"en": "Pearson Correlation"},
    "日收益率":                              {"en": "Daily Return"},
    "概率密度":                              {"en": "Probability Density"},
    "收盘":                                  {"en": "Close"},
    "综合温度":                              {"en": "Composite Temp"},
    "当前: {val:.1f}":                       {"en": "Current: {val:.1f}"},
    "市盈率 (PE)":                           {"en": "P/E Ratio"},
    "组合价值 (¥)":                          {"en": "Portfolio Value (¥)"},
    "组合终值 (¥)":                          {"en": "Final Portfolio Value (¥)"},
    "频次":                                  {"en": "Frequency"},
    "中位数 (P50)":                          {"en": "Median (P50)"},
    "P5 (悲观)":                             {"en": "P5 (Pessimistic)"},
    "P50 (中位)":                            {"en": "P50 (Median)"},
    "P95 (乐观)":                            {"en": "P95 (Optimistic)"},
    "终值分布":                              {"en": "Final Value Distribution"},
    "<b>%{label}</b><br>涨跌幅: %{customdata[0]:+.2f}%<br>最新价: %{customdata[1]:.2f}<extra></extra>": {
        "en": "<b>%{label}</b><br>Change: %{customdata[0]:+.2f}%<br>Price: %{customdata[1]:.2f}<extra></extra>"
    },
    "📡 {market}行业板块数据暂不可用":       {"en": "📡 {market} sector data temporarily unavailable"},

    # =====================================================================
    # SECTION: Sidebar: help text
    # =====================================================================
    "**🎯 风险测评及投资建议**":            {"en": "**🎯 Risk Assessment & Investment Advice**"},
    "1. 填写基本信息 → 选择意向市场":       {"en": "1. Fill in basic info → select markets"},
    "2. 完成12题风险测评问卷":              {"en": "2. Complete the 12-question risk quiz"},
    "3. 查看AI优化的资产配置":              {"en": "3. View AI-optimized asset allocation"},
    "4. 运行Monte Carlo收益模拟":           {"en": "4. Run Monte Carlo return simulation"},
    "5. 获取AI投资分析建议":                {"en": "5. Get AI investment analysis"},
    "6. 下载PDF专业投资报告":               {"en": "6. Download PDF professional report"},

    "**📊 市场仪表盘**":                    {"en": "**📊 Market Dashboard**"},
    "- 实时查看各大指数行情和走势图":       {"en": "- Real-time major index quotes & charts"},
    "- 行业板块涨跌热力图":                 {"en": "- Sector heatmap"},
    "- 宏观指标（黄金、原油、国债收益率、汇率、VIX）": {
        "en": "- Macro indicators (Gold, Crude Oil, Bond Yields, FX, VIX)"
    },
    "- ETF涨跌排行":                        {"en": "- ETF rankings"},
    "- 数据每5分钟缓存，点击刷新按钮获取最新": {
        "en": "- Data cached 5 min; click refresh for latest"
    },

    "**🌡️ 温度定投系统（旗舰功能）**":      {"en": "**🌡️ Temperature DCA System (Flagship)**"},
    "- 基于市场估值温度动态调整每月定投金额": {
        "en": "- Dynamically adjusts monthly DCA amount based on market valuation temperature"
    },
    "- 历史数据回测验证，三种策略对比":     {"en": "- Historical backtest with 3-strategy comparison"},
    "- 实时温度 + 当前投资建议":            {"en": "- Real-time temperature + investment advice"},

    "**🛠️ 独立工具**":                     {"en": "**🛠️ Standalone Tools**"},
    "- 定投计算器：随时可用，无需前置步骤": {"en": "- DCA Calculator: ready anytime, no prerequisites"},
    "- 投资术语百科：中英双语投资知识库":   {"en": "- Glossary: bilingual investment knowledge base"},

    "**💡 提示**":                          {"en": "**💡 Tips**"},
    "所有数据在会话期间保存，\n刷新页面后需要重新开始。": {
        "en": "All data is saved during the session.\nRefreshing the page will restart."
    },
	# -- Chart labels --
	"风险画像": {"en": "Risk Profile"},
	"风险评分": {"en": "Risk Score"},

	# ── ETF names (from risk_weights.yaml) ────────────────────────────
	"标普500指数ETF (SPY)": {"en": "S&P 500 ETF (SPY)"},
	"纳斯达克100 ETF (QQQ)": {"en": "Nasdaq 100 ETF (QQQ)"},
	"美国全市场ETF (VTI)": {"en": "US Total Market ETF (VTI)"},
	"全球除美股ETF (VXUS)": {"en": "Global ex-US ETF (VXUS)"},
	"罗素2000小盘股ETF (IWM)": {"en": "Russell 2000 ETF (IWM)"},
	"沪深300ETF": {"en": "CSI 300 ETF"},
	"中证500ETF": {"en": "CSI 500 ETF"},
	"创业板ETF": {"en": "ChiNext ETF"},
	"盈富基金 (恒生指数)": {"en": "Tracker Fund (Hang Seng)"},
	"恒生中国企业ETF": {"en": "HSCEI ETF"},
	"安硕恒生科技ETF": {"en": "iShares Hang Seng TECH ETF"},
	"iShares 韩国ETF (EWY)": {"en": "iShares Korea ETF (EWY)"},
	"标普500ETF (中国上市)": {"en": "S&P 500 ETF (CN)"},
	"纳斯达克100ETF (中国上市)": {"en": "Nasdaq 100 ETF (CN)"},
	"美国综合债券ETF (AGG)": {"en": "US Aggregate Bond ETF (AGG)"},
	"长期国债ETF (TLT)": {"en": "Long-Term Treasury ETF (TLT)"},
	"投资级公司债ETF (LQD)": {"en": "Investment Grade Corp Bond ETF (LQD)"},
	"通胀保护债券ETF (TIP)": {"en": "TIPS Bond ETF (TIP)"},
	"国债ETF": {"en": "Treasury Bond ETF"},
	"10年国债ETF": {"en": "10Y Treasury ETF"},
	"黄金ETF (GLD)": {"en": "Gold ETF (GLD)"},
	"iShares黄金信托 (IAU)": {"en": "iShares Gold Trust (IAU)"},
	"黄金ETF (华安黄金)": {"en": "Gold ETF (Huaan)"},
	"美国房地产ETF (VNQ)": {"en": "US Real Estate ETF (VNQ)"},
	"有色金属ETF": {"en": "Metals ETF"},
	"半导体ETF": {"en": "Semiconductor ETF"},
	"芯片ETF": {"en": "Chip ETF"},
	"新能源ETF": {"en": "New Energy ETF"},
	"医药ETF": {"en": "Healthcare ETF"},
	"证券ETF": {"en": "Securities ETF"},
	"银行ETF": {"en": "Bank ETF"},
	"军工ETF": {"en": "Defense ETF"},
	"消费ETF": {"en": "Consumer ETF"},
	"科技ETF": {"en": "Tech ETF"},
	"白酒ETF": {"en": "Liquor ETF"},
	"房地产ETF": {"en": "Real Estate ETF"},

	'\n        ### 📋 AI 投资分析内容\n\n        点击下方按钮，AI 将为您生成：\n        - 🎯 投资组合概述与配置理由\n        - ⚠️ 主要风险识别与分析\n        - 📈 不同市场情景下的表现预测\n        - 💡 具体可操作的投资建议\n        - 🛡️ 风险提示\n\n        *本地 AI 引擎，无需联网，即时生成分析结果。*\n        ': {
	    "en": '\n        ### 📋 AI Investment Analysis\n\n        Click the button below and AI will generate:\n        - 🎯 Portfolio overview & allocation rationale\n        - ⚠️ Key risk identification & analysis\n        - 📈 Performance projections across market scenarios\n        - 💡 Concrete, actionable investment recommendations\n        - 🛡️ Risk disclaimers\n\n        *Local AI engine. No internet needed. Instant analysis.*\n        '
	},
	'\n        生成的PDF报告包含以下章节：\n\n        1. **封面** - 用户信息、生成日期\n        2. **风险测评结果** - 风险等级、评分、各维度分析\n        3. **投资组合配置** - 持仓明细表、资产配置饼图、关键指标\n        4. **Monte Carlo 模拟** - 收益路径扇形图、终值分布直方图、风险统计\n        5. **AI 投资顾问分析** - 组合概述、配置理由、风险分析、市场情景、投资建议\n        6. **风险提示与免责声明**\n\n        *注意：PDF 生成包含完整的图表和分析，适合打印和分享。*\n        ': {
	    "en": '\n        The generated PDF report includes the following sections:\n\n        1. **Cover** - User information, date of generation\n        2. **Risk Assessment Results** - Risk level, score, dimensional analysis\n        3. **Portfolio Allocation** - Holdings table, allocation pie chart, key metrics\n        4. **Monte Carlo Simulation** - Return path fan chart, final value histogram, risk statistics\n        5. **AI Advisor Analysis** - Portfolio overview, allocation rationale, risk analysis, market scenarios, recommendations\n        6. **Risk Warnings & Disclaimer**\n\n        *Note: PDF includes complete charts and analysis, suitable for printing and sharing.*\n        '
	},
	# ── Market data names (indices + sectors from APIs) ────────
	"上证指数": {"en": "SSE Composite"},
	"深证成指": {"en": "SZSE Component"},
	"创业板指": {"en": "ChiNext Index"},
	"科创50": {"en": "STAR 50"},
	"纳斯达克综合": {"en": "NASDAQ Composite"},
	"道琼斯": {"en": "Dow Jones"},
	"道琼斯工业平均": {"en": "Dow Jones Industrial"},
	"日经225": {"en": "Nikkei 225"},
	"英国富时100": {"en": "FTSE 100"},
	"德国DAX": {"en": "DAX 30"},
	"法国CAC40": {"en": "CAC 40"},
	"韩国KOSPI": {"en": "KOSPI"},
	"印度NIFTY50": {"en": "NIFTY 50"},
	"富时中国A50": {"en": "FTSE China A50"},
	"电力": {"en": "Electric Power"},
	"非金属材料": {"en": "Non-Metallic Materials"},
	"钢铁": {"en": "Steel"},
	"煤炭": {"en": "Coal"},
	"汽车": {"en": "Automotive"},
	"食品饮料": {"en": "Food & Beverage"},
	"纺织": {"en": "Textiles"},
	"造纸": {"en": "Paper"},
	"化工": {"en": "Chemicals"},
	"建材": {"en": "Building Materials"},
	"机械": {"en": "Machinery"},
	"电子": {"en": "Electronics"},
	"计算机": {"en": "Computers"},
	"传媒": {"en": "Media"},
	"通信": {"en": "Telecom"},
	"农业": {"en": "Agriculture"},
	"公用事业": {"en": "Utilities"},
	"交通运输": {"en": "Transportation"},
	"旅游": {"en": "Tourism"},
	"家电": {"en": "Home Appliances"},
	"石油": {"en": "Oil"},
	"环保": {"en": "Environmental"},
	"保险": {"en": "Insurance"},
	# ── Additional index names ──
	"纳斯达克": {"en": "NASDAQ"},
	"道琼斯工业指数": {"en": "DJIA"},
	"恒生指数": {"en": "Hang Seng Index"},
	"恒生科技": {"en": "Hang Seng TECH"},
	# ── Sector names from AKShare ──
	"休闲服务": {"en": "Leisure Services"},
	"军工": {"en": "Defense"},
	"医药": {"en": "Healthcare"},
	"半导体": {"en": "Semiconductors"},
	"商业贸易": {"en": "Commercial Trade"},
	"国防军工": {"en": "National Defense"},
	"建筑装饰": {"en": "Construction & Decoration"},
	"房地产": {"en": "Real Estate"},
	"新能源": {"en": "New Energy"},
	"有色金属": {"en": "Non-Ferrous Metals"},
	"消费": {"en": "Consumer"},
	"电气设备": {"en": "Electrical Equipment"},
	"白酒": {"en": "Liquor"},
	"社会服务": {"en": "Social Services"},
	"科技": {"en": "Technology"},
	"纺织服装": {"en": "Textiles & Apparel"},
	"综合": {"en": "Conglomerates"},
	"芯片": {"en": "Chips"},
	"证券": {"en": "Securities"},
	"轻工制造": {"en": "Light Manufacturing"},
	"银行": {"en": "Banking"},
	# ── All A-share sector names from AKShare ──
	"IT服务": {"en": "IT Services"},
	"专用设备": {"en": "Specialized Equipment"},
	"中药": {"en": "Traditional Chinese Medicine"},
	"互联网电商": {"en": "Internet E-Commerce"},
	"元件": {"en": "Electronic Components"},
	"光伏设备": {"en": "PV Equipment"},
	"光学光电子": {"en": "Optoelectronics"},
	"公路铁路运输": {"en": "Road & Rail Transport"},
	"其他电子": {"en": "Other Electronics"},
	"其他电源设备": {"en": "Other Power Equipment"},
	"其他社会服务": {"en": "Other Social Services"},
	"养殖业": {"en": "Aquaculture"},
	"军工电子": {"en": "Defense Electronics"},
	"军工装备": {"en": "Defense Equipment"},
	"农产品加工": {"en": "Agricultural Processing"},
	"农化制品": {"en": "Agrochemical Products"},
	"包装印刷": {"en": "Packaging & Printing"},
	"化学制品": {"en": "Chemical Products"},
	"化学制药": {"en": "Chemical Pharmaceuticals"},
	"化学原料": {"en": "Chemical Raw Materials"},
	"化学纤维": {"en": "Chemical Fibers"},
	"医疗器械": {"en": "Medical Devices"},
	"医疗服务": {"en": "Medical Services"},
	"医药商业": {"en": "Pharmaceutical Commerce"},
	"厨卫电器": {"en": "Kitchen & Bath Appliances"},
	"塑料制品": {"en": "Plastic Products"},
	"多元金融": {"en": "Diversified Finance"},
	"家居用品": {"en": "Home Products"},
	"小家电": {"en": "Small Appliances"},
	"小金属": {"en": "Minor Metals"},
	"工业金属": {"en": "Industrial Metals"},
	"工程机械": {"en": "Engineering Machinery"},
	"建筑材料": {"en": "Building Materials"},
	"影视院线": {"en": "Film & Cinema"},
	"教育": {"en": "Education"},
	"文化传媒": {"en": "Culture & Media"},
	"旅游及酒店": {"en": "Tourism & Hotels"},
	"服装家纺": {"en": "Apparel & Home Textiles"},
	"机场航运": {"en": "Airport & Aviation"},
	"橡胶制品": {"en": "Rubber Products"},
	"汽车整车": {"en": "Automotive OEM"},
	"汽车服务及其他": {"en": "Auto Services & Others"},
	"汽车零部件": {"en": "Auto Parts"},
	"油气开采及服务": {"en": "Oil & Gas Extraction"},
	"消费电子": {"en": "Consumer Electronics"},
	"港口航运": {"en": "Port & Shipping"},
	"游戏": {"en": "Gaming"},
	"煤炭开采加工": {"en": "Coal Mining & Processing"},
	"燃气": {"en": "Natural Gas"},
	"物流": {"en": "Logistics"},
	"环保设备": {"en": "Environmental Equipment"},
	"环境治理": {"en": "Environmental Management"},
	"生物制品": {"en": "Biological Products"},
	"电子化学品": {"en": "Electronic Chemicals"},
	"电机": {"en": "Electric Motors"},
	"电池": {"en": "Batteries"},
	"电网设备": {"en": "Power Grid Equipment"},
	"白色家电": {"en": "White Goods"},
	"石油加工贸易": {"en": "Petroleum Processing & Trade"},
	"种植业与林业": {"en": "Farming & Forestry"},
	"纺织制造": {"en": "Textile Manufacturing"},
	"美容护理": {"en": "Beauty & Personal Care"},
	"能源金属": {"en": "Energy Metals"},
	"自动化设备": {"en": "Automation Equipment"},
	"计算机设备": {"en": "Computer Equipment"},
	"贵金属": {"en": "Precious Metals"},
	"贸易": {"en": "Trading"},
	"轨交设备": {"en": "Rail Transit Equipment"},
	"软件开发": {"en": "Software Development"},
	"通信服务": {"en": "Telecom Services"},
	"通信设备": {"en": "Telecom Equipment"},
	"通用设备": {"en": "General Equipment"},
	"金属新材料": {"en": "Advanced Metal Materials"},
	"零售": {"en": "Retail"},
	"风电设备": {"en": "Wind Power Equipment"},
	"食品加工制造": {"en": "Food Processing"},
	"饮料制造": {"en": "Beverage Manufacturing"},
	"黑色家电": {"en": "Black Goods"},
	# ── US/HK sector names ──
	"A50中国": {"en": "A50 China"},
	"医疗健康": {"en": "Healthcare"},
	"可选消费": {"en": "Consumer Discretionary"},
	"国企/H股": {"en": "SOE/H-Share"},
	"工业": {"en": "Industrials"},
	"必需消费": {"en": "Consumer Staples"},
	"恒生(基准)": {"en": "Hang Seng (Benchmark)"},
	"材料": {"en": "Materials"},
	"清洁能源": {"en": "Clean Energy"},
	"生物科技": {"en": "Biotech"},
	"能源": {"en": "Energy"},
	"金融": {"en": "Financials"},
}


def get_lang() -> str:
    """Return current language code: 'zh' or 'en'."""
    return st.session_state.get("lang", "zh")


def set_lang(lang: str):
    """Set language in session state."""
    st.session_state.lang = lang


def toggle_lang():
    """Toggle between zh and en."""
    current = get_lang()
    set_lang("en" if current == "zh" else "zh")


def t(text: str) -> str:
    """Translate a Chinese string to the current language.

    If the text is not found in the dictionary or the target language
    is zh, returns the original text unchanged.
    """
    lang = get_lang()
    if lang == "zh":
        return text
    entry = TRANSLATIONS.get(text)
    if entry:
        return entry.get("en", text)
    return text


# Shorthand alias for t()
_ = t
