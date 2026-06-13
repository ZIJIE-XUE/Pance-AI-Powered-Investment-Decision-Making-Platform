"""磐策 PánCè - Streamlit Main Application Entry Point.

Multi-page app with global session state management.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from src.ui.components.sidebar import render_sidebar
from src.utils.logging_config import setup_logging

# Page configuration
st.set_page_config(
    page_title="磐策 PánCè - AI 智能投顾",
    page_icon="⛰️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": (
            "# 磐策 PánCè\n"
            "智能投资顾问系统 v1.0\n\n"
            "AI驱动的资产配置和投资分析平台。\n\n"
            "⚠️ 投资有风险，本系统仅供学习和参考。"
        ),
    },
)


def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "db_initialized": False,
        "user": None,
        "questionnaire": None,
        "risk_profile": None,
        "portfolio": None,
        "simulation": None,
        "advisor_response": None,
        "report_metadata": None,
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def _ensure_database():
    """Create database tables if they don't exist. Called on every app startup."""
    from src.db.database import init_db_sync
    init_db_sync()


# ── CSS ──────────────────────────────────────────────────────────────────────

def _inject_css():
    st.markdown("""
    <style>
        .landing-hero {
            background: linear-gradient(135deg, #1a237e 0%, #283593 45%, #E65100 100%);
            border-radius: 16px;
            padding: 40px 44px;
            margin-bottom: 28px;
            color: #fff;
        }
        .landing-hero h1 {
            color: #fff;
            font-size: 2.2em;
            margin: 0 0 4px 0;
            letter-spacing: 1px;
        }
        .landing-hero .subtitle {
            font-size: 1.1em;
            opacity: 0.85;
            margin: 0 0 6px 0;
            font-weight: 400;
        }
        .landing-hero .tagline {
            font-size: 0.85em;
            opacity: 0.6;
            letter-spacing: 4px;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 14px;
            margin-bottom: 28px;
        }
        .feature-card {
            padding: 18px 14px;
            border-radius: 12px;
            text-align: center;
            border: 1.5px solid #e0e0e0;
            background: #fafafa;
            transition: transform 0.15s, box-shadow 0.15s;
        }
        .feature-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        .feature-card.flagship {
            background: linear-gradient(135deg, #FFF8E1, #FFF3E0);
            border: 2px solid #E65100;
        }
        .badge-flagship {
            display: inline-block;
            font-size: 0.6em;
            background: #E65100;
            color: #fff;
            padding: 2px 10px;
            border-radius: 10px;
            font-weight: 600;
            letter-spacing: 1px;
        }
        .landing-steps {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 22px 28px;
            margin-bottom: 20px;
        }
        .landing-steps ol {
            margin: 0;
            padding-left: 18px;
        }
        .landing-steps li {
            margin-bottom: 4px;
            font-size: 0.92em;
            line-height: 1.7;
        }
        @media (max-width: 900px) {
            .feature-grid { grid-template-columns: 1fr 1fr; }
        }
    </style>
    """, unsafe_allow_html=True)


# ── New user landing ─────────────────────────────────────────────────────────

def _render_hero():
    """Brand hero banner."""
    st.markdown(
        '<div class="landing-hero">'
        '<h1>⛰️ 磐策 PánCè</h1>'
        '<p class="subtitle">AI 智能投资决策平台</p>'
        '<p class="tagline">稳如磐石 · 策定乾坤</p>'
        '</div>',
        unsafe_allow_html=True,
    )


def _render_features():
    """Feature highlight cards — flagship first."""
    features = [
        {
            "icon": "🌡️",
            "title": "智能温度定投",
            "desc": "市场冷时多投 · 热时少投<br>回测验证，数据驱动决策",
            "flagship": True,
        },
        {
            "icon": "🎯",
            "title": "风险测评",
            "desc": "12题科学问卷<br>5级风险 · 组合优化",
            "flagship": False,
        },
        {
            "icon": "📊",
            "title": "市场仪表盘",
            "desc": "实时行情 · 板块热力<br>ETF对比 · 市场温度计",
            "flagship": False,
        },
        {
            "icon": "🔮",
            "title": "Monte Carlo",
            "desc": "万条路径模拟<br>AI 分析 · PDF 报告",
            "flagship": False,
        },
    ]

    cards_html = '<div class="feature-grid">'
    for f in features:
        cls = "feature-card flagship" if f["flagship"] else "feature-card"
        badge = ' <span class="badge-flagship">旗舰</span>' if f["flagship"] else ""
        cards_html += (
            f'<div class="{cls}">'
            f'<div style="font-size:1.8em;margin-bottom:6px">{f["icon"]}</div>'
            f'<div style="font-weight:600;font-size:0.92em;margin-bottom:6px">'
            f'{f["title"]}{badge}</div>'
            f'<div style="font-size:0.74em;color:#888;line-height:1.55">{f["desc"]}</div>'
            f'</div>'
        )
    cards_html += '</div>'

    st.markdown(cards_html, unsafe_allow_html=True)


def _render_quickstart():
    """Quick start guide."""
    st.markdown(
        '<div class="landing-steps">'
        '<h4 style="margin:0 0 10px 0">🚀 快速开始</h4>'
        '<ol>'
        '<li><b>🌡️ 智能温度定投</b> — 旗舰功能，可直接使用，无需前置步骤</li>'
        '<li>📝 填写基本信息 → 🎯 完成风险测评</li>'
        '<li>📊 查看 AI 优化的投资组合 → 🔮 运行 Monte Carlo 模拟</li>'
        '<li>🤖 获取 AI 深度分析 → 📄 下载 PDF 专业报告</li>'
        '</ol>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "👈 从左侧栏 🌡️ 温度定投系统 开始体验旗舰功能，"
        "或从 🎯 风险测评及投资建议 走完完整流程。"
    )


# ── Returning user guidance ──────────────────────────────────────────────────

def _render_next_step():
    """Show next step for users in the middle of the workflow."""
    if st.session_state.risk_profile is None:
        st.info("👉 下一步：完成风险测评问卷")
    elif st.session_state.portfolio is None:
        st.info("👉 下一步：生成投资组合配置")
    elif st.session_state.simulation is None:
        st.info("👉 下一步：运行 Monte Carlo 模拟")
    elif st.session_state.advisor_response is None:
        st.info("👉 下一步：获取 AI 投资建议")
    elif st.session_state.report_metadata is None:
        st.info("👉 下一步：下载 PDF 报告")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    """Main Streamlit app entry point."""
    setup_logging()
    _ensure_database()
    init_session_state()
    render_sidebar()
    _inject_css()

    if st.session_state.user is None:
        # New user — show full landing page
        _render_hero()
        _render_features()
        st.markdown("---")
        _render_quickstart()
    else:
        # Returning user — show progress and next step
        st.markdown(
            '<div class="landing-hero" style="padding:24px 32px">'
            f'<h1 style="font-size:1.2em;margin:0">👋 欢迎回来，{st.session_state.user.get("display_name") or "投资者"}</h1>'
            '</div>',
            unsafe_allow_html=True,
        )
        _render_next_step()


if __name__ == "__main__":
    main()
