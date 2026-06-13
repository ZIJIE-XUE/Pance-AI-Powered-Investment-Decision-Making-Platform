"""Common sidebar navigation component."""

import streamlit as st
from pathlib import Path


# ── Page definitions ───────────────────────────────────────────────────────

WORKFLOW_STEPS = [
    ("01_home",               "🏠 基本信息",     "user"),
    ("02_risk_assessment",    "🎯 风险测评",     "risk_profile"),
    ("03_portfolio",          "📊 投资组合",     "portfolio"),
    ("04_simulation",         "🔮 蒙特卡洛",     "simulation"),
    ("05_ai_advisor",         "🤖 AI 分析",      "advisor_response"),
    ("06_report",             "📄 报告下载",     "report_metadata"),
]

FLAGSHIP = [
    ("12_temperature_dca", "🌡️ 智能温度定投"),
]

DASHBOARD = [
    ("08_market_dashboard",   "📊 市场仪表盘"),
    ("09_etf_comparison",     "📈 ETF对比"),
    ("11_market_thermometer", "🌡️ 市场温度计"),
]

TOOLS = [
    ("07_dca_calculator",         "💰 定投计算器"),
    ("10_investment_glossary",    "📚 投资术语百科"),
]


def _latest_page():
    """Find the latest completed step to highlight the active page."""
    for i, (_, _, key) in enumerate(reversed(WORKFLOW_STEPS)):
        if st.session_state.get(key) is not None:
            return len(WORKFLOW_STEPS) - i
    return 1  # Default to first step


def render_sidebar():
    """Render the common sidebar with navigation and progress."""
    # Hide Streamlit's default page nav — injected here so it runs on every page
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] { display: none; }
            [data-testid="stSidebarNavItems"] { display: none; }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        # ── Logo & Brand ───────────────────────────────────────────────────
        logo_path = Path(__file__).parent.parent.parent.parent / "assets" / "磐策logo.jpg"
        _, col_logo, _ = st.columns([0.05, 0.9, 0.05])
        with col_logo:
            st.image(str(logo_path), use_container_width=True)

        st.markdown(
            "<h2 style='margin-bottom:0'>磐策 <span style='font-size:0.6em;color:#888'>PánCè</span></h2>"
            "<p style='color:#888;font-size:0.8em;margin-top:0'>稳如磐石 · 策定乾坤</p>",
            unsafe_allow_html=True,
        )

        # ── User ───────────────────────────────────────────────────────────
        if st.session_state.get("user"):
            user = st.session_state.user
            name = user.get("display_name") or "投资者"
            email = user.get("email", "")
            markets = user.get("preferred_markets", "")
            markets_html = f"<br><small style='color:#888'>🌍 {markets}</small>" if markets else ""
            html = (
                f"<div style='padding:8px 12px;border-radius:8px;background:#f0f4ff;margin:8px 0'>"
                f"<strong>👤 {name}</strong><br>"
                f"<small style='color:#888'>📧 {email}</small>"
                f"{markets_html}"
                f"</div>"
            )
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("👈 请先填写基本信息")

        st.markdown("---")

        # ── Module 0: Temperature DCA (Flagship) ──────────────────────────
        st.markdown("""
            <div style="background:linear-gradient(135deg, #FF6D00, #E65100);
                        padding:12px 16px;
                        border-radius:10px;
                        margin-bottom:6px;
                        box-shadow:0 2px 10px rgba(230,81,0,0.2)">
                <div style="display:flex;align-items:center;justify-content:space-between">
                    <span style="color:#fff;font-weight:700;font-size:1em">🌡️ 温度定投系统</span>
                    <span style="background:rgba(255,255,255,0.25);color:#fff;font-size:0.65em;
                                 padding:2px 8px;border-radius:10px;font-weight:600;
                                 letter-spacing:0.5px">旗舰</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        for page_file, label in FLAGSHIP:
            st.page_link(
                f"pages/{page_file}.py",
                label=label,
                use_container_width=True,
            )

        st.markdown("---")

        # ── Module 1: Workflow ─────────────────────────────────────────────
        st.markdown("#### 🎯 风险测评及投资建议")

        # Progress bar
        completed_count = sum(
            1 for _, _, key in WORKFLOW_STEPS
            if st.session_state.get(key) is not None
        )
        total = len(WORKFLOW_STEPS)
        st.progress(completed_count / total, text=f"{completed_count}/{total} 已完成")

        # Step links
        for page_file, label, key in WORKFLOW_STEPS:
            done = st.session_state.get(key) is not None
            icon = "✅" if done else "○"
            st.page_link(
                f"pages/{page_file}.py",
                label=f"{icon}  {label}",
                disabled=False,
                use_container_width=True,
            )

        st.markdown("---")

        # ── Module 2: Market Dashboard ─────────────────────────────────────
        st.markdown("#### 📊 市场仪表盘")

        for page_file, label in DASHBOARD:
            st.page_link(
                f"pages/{page_file}.py",
                label=label,
                use_container_width=True,
            )

        st.markdown("---")

        # ── Module 3: Tools ────────────────────────────────────────────────
        st.markdown("#### 🛠️ 独立工具")

        for page_file, label in TOOLS:
            st.page_link(
                f"pages/{page_file}.py",
                label=label,
                use_container_width=True,
            )

        st.markdown("---")

        # ── Help ───────────────────────────────────────────────────────────
        with st.expander("ℹ️ 使用说明"):
            st.markdown(
                """
                **🎯 风险测评及投资建议**
                1. 填写基本信息 → 选择意向市场
                2. 完成12题风险测评问卷
                3. 查看AI优化的资产配置
                4. 运行Monte Carlo收益模拟
                5. 获取AI投资分析建议
                6. 下载PDF专业投资报告

                **📊 市场仪表盘**
                - 实时查看各大指数行情和走势图
                - 行业板块涨跌热力图
                - 宏观指标（黄金、原油、国债收益率、汇率、VIX）
                - ETF涨跌排行
                - 数据每5分钟缓存，点击刷新按钮获取最新

                **🌡️ 温度定投系统（旗舰功能）**
                - 基于市场估值温度动态调整每月定投金额
                - 历史数据回测验证，三种策略对比（温度定投 vs 普通定投 vs 一次性买入）
                - 实时温度 + 当前投资建议

                **🛠️ 独立工具**
                - 定投计算器：随时可用，无需前置步骤
                - 投资术语百科：中英双语投资知识库，随时查阅金融术语

                **💡 提示**
                所有数据在会话期间保存，
                刷新页面后需要重新开始。
                """
            )

        # ── Footer ─────────────────────────────────────────────────────────
        st.markdown("---")
        st.caption("© 2026 磐策 PánCè")
        st.caption("投资有风险 · 入市需谨慎")
