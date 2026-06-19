"""Common sidebar navigation component — card-style like homepage feature grid."""

import streamlit as st
from pathlib import Path

from src.ui.i18n import t, get_lang, set_lang, toggle_lang, _


# ── Page definitions ───────────────────────────────────────────────────────

WORKFLOW_STEPS = [
    ("01_home",               "基本信息",     "📝", "填写个人档案与意向市场",     "user"),
    ("02_risk_assessment",    "风险测评",     "🎯", "12题科学问卷 · 5级风险",   "risk_profile"),
    ("03_portfolio",          "投资组合",     "📊", "AI优化 · 资产配置方案",     "portfolio"),
    ("04_simulation",         "蒙特卡洛",     "🔮", "万条路径 · 收益模拟",      "simulation"),
    ("05_ai_advisor",         "AI 分析",      "🤖", "深度解读 · 操作建议",      "advisor_response"),
    ("06_report",             "报告下载",     "📄", "PDF专业报告导出",          "report_metadata"),
]

FLAGSHIP = [
    ("12_temperature_dca", "🌡️", "智能温度定投", "市场冷时多投 · 热时少投"),
]

DASHBOARD = [
    ("08_market_dashboard",   "📊", "市场仪表盘",   "实时行情 · 板块热力"),
    ("09_etf_comparison",     "📈", "ETF对比",      "全市场ETF排行筛选"),
    ("11_market_thermometer", "🌡️", "市场温度计",   "估值分位 · 买卖信号"),
]

TOOLS = [
    ("07_dca_calculator",     "💰", "定投计算器",   "复利测算 · 目标规划"),
    ("10_investment_glossary", "📚", "投资术语百科", "中英双语 · 随时查阅"),
]


def _latest_step_index():
    """Find the latest completed workflow step."""
    for i, (_, _, _, _, key) in enumerate(reversed(WORKFLOW_STEPS)):
        if st.session_state.get(key) is not None:
            return len(WORKFLOW_STEPS) - 1 - i
    return -1  # None completed


def render_sidebar():
    """Render card-style sidebar navigation matching homepage aesthetic."""

    # ── Inject sidebar CSS ─────────────────────────────────────────────
    st.markdown("""
        <style>
            /* Hide Streamlit default nav */
            [data-testid="stSidebarNav"] { display: none; }
            [data-testid="stSidebarNavItems"] { display: none; }

            /* Card styling for page links */
            .sb-card {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 10px 12px;
                margin: 3px 0;
                border-radius: 10px;
                background: #fafafa;
                border: 1.5px solid #e8e8e8;
                transition: all 0.15s;
                cursor: pointer;
                text-decoration: none;
                color: inherit;
            }
            .sb-card:hover {
                background: #f0f4ff;
                border-color: #4285f4;
                transform: translateX(2px);
            }
            .sb-card .sb-icon {
                font-size: 1.35em;
                flex-shrink: 0;
                width: 34px;
                text-align: center;
            }
            .sb-card .sb-body {
                flex: 1;
                min-width: 0;
            }
            .sb-card .sb-title {
                font-weight: 600;
                font-size: 0.88em;
                line-height: 1.3;
            }
            .sb-card .sb-desc {
                font-size: 0.7em;
                color: #999;
                line-height: 1.35;
            }
            .sb-card.active {
                background: #e8f0fe;
                border-color: #4285f4;
                box-shadow: 0 1px 4px rgba(66,133,244,0.12);
            }
            .sb-card.done {
                background: #f0faf0;
                border-color: #a5d6a7;
            }
            .sb-card.done .sb-title::before {
                content: "✅ ";
            }

            /* Flagship card */
            .sb-card.flagship {
                background: linear-gradient(135deg, #FFF8E1, #FFF3E0);
                border: 2px solid #E65100;
            }
            .sb-card.flagship:hover {
                background: linear-gradient(135deg, #FFF3E0, #FFE0B2);
                border-color: #BF360C;
            }
            .sb-badge {
                display: inline-block;
                font-size: 0.55em;
                background: #E65100;
                color: #fff;
                padding: 1px 8px;
                border-radius: 8px;
                font-weight: 600;
                letter-spacing: 0.5px;
                vertical-align: middle;
                margin-left: 4px;
            }

            /* Section header */
            .sb-section-title {
                font-size: 0.78em;
                font-weight: 700;
                color: #555;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                margin: 14px 0 6px 2px;
            }

            /* Language toggle */
            .lang-toggle {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 6px 10px;
                margin: 8px 0;
                background: #f5f5f5;
                border-radius: 8px;
                font-size: 0.82em;
            }
            .lang-toggle span {
                color: #666;
            }
        </style>
    """, unsafe_allow_html=True)

    # ── Helper: render a single nav card ───────────────────────────────
    def _nav_card(page_file, icon, title, desc, active=False, done=False, flagship=False):
        """Render one card-style page link."""
        classes = ["sb-card"]
        if flagship:
            classes.append("flagship")
        if active:
            classes.append("active")
        if done:
            classes.append("done")

        badge_html = f' <span class="sb-badge">{t("旗舰")}</span>' if flagship else ""

        html = (
            f'<a class="{" ".join(classes)}" href="/{page_file}" target="_self">'
            f'<span class="sb-icon">{icon}</span>'
            f'<span class="sb-body">'
            f'<span class="sb-title">{t(title)}{badge_html}</span>'
            f'<br><span class="sb-desc">{t(desc)}</span>'
            f'</span>'
            f'</a>'
        )
        st.markdown(html, unsafe_allow_html=True)

    # ── Sidebar body ───────────────────────────────────────────────────
    with st.sidebar:
        # Logo & Brand
        logo_path = Path(__file__).parent.parent.parent.parent / "assets" / "磐策logo.jpg"
        _, col_logo, _ = st.columns([0.05, 0.9, 0.05])
        with col_logo:
            st.image(str(logo_path), use_container_width=True)

        st.markdown(
            "<h2 style='margin-bottom:0'>磐策 "
            "<span style='font-size:0.6em;color:#888'>PánCè</span></h2>"
            f"<p style='color:#888;font-size:0.8em;margin-top:0'>{t('稳如磐石 · 策定乾坤')}</p>",
            unsafe_allow_html=True,
        )

        # ── Language switcher ──────────────────────────────────────────
        lang = get_lang()
        new_lang = st.selectbox(
            "🌐",
            options=["zh", "en"],
            format_func=lambda x: "🇨🇳 中文" if x == "zh" else "🇺🇸 English",
            index=0 if lang == "zh" else 1,
            key="lang_selector",
            label_visibility="collapsed",
        )
        if new_lang != lang:
            set_lang(new_lang)
            st.rerun()

        # User info
        if st.session_state.get("user"):
            user = st.session_state.user
            name = user.get("display_name") or "投资者"
            email = user.get("email", "")
            markets = user.get("preferred_markets", "")
            markets_html = f"<br><small style='color:#888'>🌍 {markets}</small>" if markets else ""
            st.markdown(
                f"<div style='padding:8px 12px;border-radius:8px;background:#f0f4ff;margin:8px 0'>"
                f"<strong>👤 {name}</strong><br>"
                f"<small style='color:#888'>📧 {email}</small>"
                f"{markets_html}"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.markdown("---")

        # ── Section 1: Flagship ────────────────────────────────────────
        st.markdown(f'<div class="sb-section-title">{t("🌡️ 旗舰功能")}</div>',
                    unsafe_allow_html=True)
        for page_file, icon, title, desc in FLAGSHIP:
            _nav_card(page_file, icon, title, desc, flagship=True)

        st.markdown("---")

        # ── Section 2: Workflow ────────────────────────────────────────
        st.markdown(f'<div class="sb-section-title">{t("🎯 风险测评及投资建议")}</div>',
                    unsafe_allow_html=True)

        completed_count = sum(
            1 for _, _, _, _, key in WORKFLOW_STEPS
            if st.session_state.get(key) is not None
        )
        total = len(WORKFLOW_STEPS)
        st.progress(completed_count / total,
                    text=f"⏳ {completed_count}/{total} {t('已完成') if get_lang() == 'en' else '已完成'}")

        latest_idx = _latest_step_index()
        for i, (page_file, title, icon, desc, key) in enumerate(WORKFLOW_STEPS):
            done = st.session_state.get(key) is not None
            active = (i == latest_idx + 1)  # next step to do
            _nav_card(page_file, icon, title, desc, done=done, active=active)

        st.markdown("---")

        # ── Section 3: Dashboard ───────────────────────────────────────
        st.markdown(f'<div class="sb-section-title">{t("📊 市场仪表盘")}</div>',
                    unsafe_allow_html=True)
        for page_file, icon, title, desc in DASHBOARD:
            _nav_card(page_file, icon, title, desc)

        st.markdown("---")

        # ── Section 4: Tools ───────────────────────────────────────────
        st.markdown(f'<div class="sb-section-title">{t("🛠️ 独立工具")}</div>',
                    unsafe_allow_html=True)
        for page_file, icon, title, desc in TOOLS:
            _nav_card(page_file, icon, title, desc)

        st.markdown("---")

        # ── Help ───────────────────────────────────────────────────────
        with st.expander(t("ℹ️ 使用说明")):
            st.markdown(
                f"""
                {t("**🎯 风险测评及投资建议**")}
                {t("1. 填写基本信息 → 选择意向市场")}
                {t("2. 完成12题风险测评问卷")}
                {t("3. 查看AI优化的资产配置")}
                {t("4. 运行Monte Carlo收益模拟")}
                {t("5. 获取AI投资分析建议")}
                {t("6. 下载PDF专业投资报告")}

                {t("**📊 市场仪表盘**")}
                {t("- 实时查看各大指数行情和走势图")}
                {t("- 行业板块涨跌热力图")}
                {t("- 宏观指标（黄金、原油、国债收益率、汇率、VIX）")}
                {t("- ETF涨跌排行")}
                {t("- 数据每5分钟缓存，点击刷新按钮获取最新")}

                {t("**🌡️ 温度定投系统（旗舰功能）**")}
                {t("- 基于市场估值温度动态调整每月定投金额")}
                {t("- 历史数据回测验证，三种策略对比")}
                {t("- 实时温度 + 当前投资建议")}

                {t("**🛠️ 独立工具**")}
                {t("- 定投计算器：随时可用，无需前置步骤")}
                {t("- 投资术语百科：中英双语投资知识库")}

                {t("**💡 提示**")}
                {t("所有数据在会话期间保存，\n刷新页面后需要重新开始。")}
                """
            )

        # Footer
        st.markdown("---")
        st.caption("© 2026 磐策 PánCè")
        st.caption(t("投资有风险 · 入市需谨慎"))
