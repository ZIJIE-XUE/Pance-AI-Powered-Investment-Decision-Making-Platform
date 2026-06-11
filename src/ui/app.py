"""AI Robo Advisor - Streamlit Main Application Entry Point.

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
    page_title="AI Robo Advisor - 智能投顾",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": (
            "# AI Robo Advisor\n"
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


def main():
    """Main Streamlit app entry point."""
    # Setup logging
    setup_logging()

    # Ensure database tables exist BEFORE any page tries to use them
    _ensure_database()

    # Initialize session state
    init_session_state()

    # Render sidebar
    render_sidebar()

    # Welcome message for new users
    if st.session_state.user is None:
        st.markdown(
            """
            # 🤖 欢迎使用 AI Robo Advisor

            ### 您的 AI 驱动智能投资顾问

            AI Robo Advisor 是一个集成了现代投资组合理论、Monte Carlo 模拟和
            AI 大语言模型的智能投资顾问系统。

            ### 🚀 快速开始

            请按以下步骤操作：

            1. **📝 填写基本信息** → 告诉我们您的年龄、收入、资产和投资目标
            2. **🎯 完成风险测评** → 通过12个问题评估您的风险承受能力
            3. **📊 查看投资组合** → 获得基于风险等级的优化资产配置
            4. **🔮 运行 Monte Carlo 模拟** → 预测不同投资期限的收益分布
            5. **🤖 获取 AI 分析** → 智能引擎深度解读您的投资方案
            6. **📄 下载 PDF 报告** → 获取专业投资分析报告

            ### 📊 系统功能

            | 功能 | 说明 |
            |------|------|
            | 🎯 风险测评 | 12题科学问卷，精准评估风险等级 |
            | 📊 组合优化 | 基于现代投资组合理论，覆盖股票/债券/黄金ETF |
            | 🔮 Monte Carlo | 10,000条路径模拟未来5/10/20年收益 |
            | 🤖 AI 分析 | 智能引擎深度分析配置理由和风险 |
            | 📄 专业报告 | 一键生成包含图表的PDF投资报告 |

            ---
            👈 **请从侧边栏或下方开始填写您的个人信息。**
            """
        )
    else:
        # Show next step guidance
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


if __name__ == "__main__":
    main()
