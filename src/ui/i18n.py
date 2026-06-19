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

    # ── Sidebar: help text ─────────────────────────────────────────────────
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
