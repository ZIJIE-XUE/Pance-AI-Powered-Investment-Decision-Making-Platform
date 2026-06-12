"""Home page - User information input.

Collects age, income, assets, investment horizon, and goals.
"""

import asyncio
from datetime import datetime

import streamlit as st

from src.db.database import async_session_factory
from src.db.models import User
from src.ui.components.sidebar import render_sidebar
from src.utils.validators import (
    validate_age,
    validate_income,
    validate_asset_size,
    validate_horizon_years,
)


async def _create_or_get_user(user_data: dict) -> User:
    """Create a new user or return existing one with the same email."""
    from sqlalchemy import select

    session = async_session_factory()
    try:
        # Check if user with this email already exists
        result = await session.execute(
            select(User).where(User.email == user_data["email"])
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            # Update existing user's info
            existing.display_name = user_data.get("display_name", "")
            existing.age = user_data["age"]
            existing.income = user_data["income"]
            existing.asset_size = user_data["asset_size"]
            existing.investment_horizon = user_data["investment_horizon"]
            existing.investment_goal = user_data.get("investment_goal", "")
            existing.preferred_markets = user_data.get("preferred_markets", "")
            await session.flush()
            await session.refresh(existing)
            await session.commit()
            return existing

        # Create new user
        user = User(
            email=user_data["email"],
            display_name=user_data.get("display_name", ""),
            age=user_data["age"],
            income=user_data["income"],
            asset_size=user_data["asset_size"],
            investment_horizon=user_data["investment_horizon"],
            investment_goal=user_data.get("investment_goal", ""),
            preferred_markets=user_data.get("preferred_markets", ""),
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
        await session.commit()
        return user
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def show():
    """Display the home page with user info form."""
    render_sidebar()
    st.title("🏠 基本信息")
    st.markdown("### 智能投资顾问 - 个人信息")

    # Database is initialized by app.py on startup — no need to re-init here

    # If user already exists, show summary
    if st.session_state.get("user") is not None:
        user = st.session_state.user
        st.success("✅ 基本信息已填写")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("年龄", user.get("age"))
            st.metric("年收入", f"¥{user.get('income', 0):,.0f}")
        with col2:
            st.metric("资产规模", f"¥{user.get('asset_size', 0):,.0f}")
            st.metric("投资期限", f"{user.get('investment_horizon', 0)}年")
        with col3:
            st.metric("投资目标", user.get("investment_goal", "未指定"))
            markets = user.get("preferred_markets", "A股,港股,美股")
            if markets:
                st.metric("意向市场", markets)

        if st.button("🔄 修改信息"):
            st.session_state.user = None
            st.rerun()
        return

    # Input form
    with st.form("user_info_form"):
        st.markdown("请填写以下信息，帮助我们为您量身定制投资方案。")

        col1, col2 = st.columns(2)

        with col1:
            email = st.text_input(
                "邮箱 *",
                placeholder="your@email.com",
                help="用于识别您的投资档案",
            )
            age = st.number_input(
                "年龄 *",
                min_value=18,
                max_value=120,
                value=30,
                step=1,
            )
            income = st.number_input(
                "年收入 (¥) *",
                min_value=0.0,
                value=200_000.0,
                step=10_000.0,
                format="%.0f",
                help="税后年收入",
            )

        with col2:
            display_name = st.text_input(
                "显示名称",
                placeholder="您的称呼（可选）",
            )
            asset_size = st.number_input(
                "可投资资产规模 (¥) *",
                min_value=0.0,
                value=500_000.0,
                step=10_000.0,
                format="%.0f",
                help="您计划用于投资的资金总额",
            )
            investment_horizon = st.selectbox(
                "投资期限 *",
                options=[5, 10, 20],
                format_func=lambda x: f"{x}年",
                help="您计划持有投资的时间长度",
            )

        investment_goal = st.text_area(
            "投资目标",
            placeholder="例如：为退休储蓄、购房首付、子女教育基金...",
            help="描述您的投资目标，这将帮助AI更好地理解您的需求",
        )

        st.markdown("---")
        st.markdown("### 🌍 意向投资市场")
        st.caption("选择您希望投资的市场，后续组合优化将仅使用选中市场的股票类ETF（债券、黄金、现金不受此限制）")

        preferred_markets = st.multiselect(
            "意向市场",
            options=["A股", "港股", "美股", "韩国"],
            default=["A股", "港股", "美股"],
            help="可多选。投资组合中的股票类资产将只从您选择的市场中挑选",
        )

        st.markdown("---")

        submitted = st.form_submit_button(
            "💾 保存信息并开始测评",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            # Validate inputs
            errors = []
            if not email or "@" not in email:
                errors.append("请输入有效的邮箱地址")

            try:
                validate_age(age)
            except Exception as e:
                errors.append(str(e))

            try:
                validate_income(income)
            except Exception as e:
                errors.append(str(e))

            try:
                validate_asset_size(asset_size)
            except Exception as e:
                errors.append(str(e))

            try:
                validate_horizon_years(investment_horizon)
            except Exception as e:
                errors.append(str(e))

            if errors:
                for error in errors:
                    st.error(error)
                return

            # Create user
            try:
                preferred_markets_str = ",".join(preferred_markets) if preferred_markets else "A股,港股,美股"

                user = asyncio.run(
                    _create_or_get_user({
                        "email": email,
                        "display_name": display_name,
                        "age": age,
                        "income": income,
                        "asset_size": asset_size,
                        "investment_horizon": investment_horizon,
                        "investment_goal": investment_goal,
                        "preferred_markets": preferred_markets_str,
                    })
                )

                st.session_state.user = {
                    "id": str(user.id),
                    "email": user.email,
                    "display_name": user.display_name,
                    "age": user.age,
                    "income": user.income,
                    "asset_size": user.asset_size,
                    "investment_horizon": user.investment_horizon,
                    "investment_goal": user.investment_goal,
                    "preferred_markets": user.preferred_markets or "A股,港股,美股",
                }

                st.success("✅ 信息保存成功！请前往下一步进行风险测评。")
                st.rerun()

            except Exception as e:
                st.error(f"保存失败：{str(e)}")


if __name__ == "__main__":
    show()
