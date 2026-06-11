"""Report Download page.

Generates and provides download for the professional PDF investment report.
"""

import asyncio
import os

import streamlit as st

from src.services.report_service import ReportService
from src.db.database import async_session_factory


async def _generate_report(user_info, risk_profile, portfolio, simulation, advisor_response):
    """Generate PDF report."""
    session = async_session_factory()
    try:
        service = ReportService(session)
        result = await service.generate(
            user_info=user_info,
            risk_profile=risk_profile,
            portfolio=portfolio,
            simulation=simulation,
            advisor_response=advisor_response,
        )
        await session.commit()
        return result
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def show():
    """Display the report generation and download page."""
    st.title("📄 投资报告下载")

    # Check prerequisites
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning("⚠️ 请先在首页填写基本信息")
        return

    if "risk_profile" not in st.session_state or st.session_state.risk_profile is None:
        st.warning("⚠️ 请先完成风险测评")
        return

    if "portfolio" not in st.session_state or st.session_state.portfolio is None:
        st.warning("⚠️ 请先完成投资组合优化")
        return

    if "simulation" not in st.session_state or st.session_state.simulation is None:
        st.warning("⚠️ 请先完成 Monte Carlo 模拟")
        return

    # Display what's included
    st.markdown("## 📋 报告包含内容")
    st.markdown(
        """
        生成的PDF报告包含以下章节：

        1. **封面** - 用户信息、生成日期
        2. **风险测评结果** - 风险等级、评分、各维度分析
        3. **投资组合配置** - 持仓明细表、资产配置饼图、关键指标
        4. **Monte Carlo 模拟** - 收益路径扇形图、终值分布直方图、风险统计
        5. **AI 投资顾问分析** - 组合概述、配置理由、风险分析、市场情景、投资建议
        6. **风险提示与免责声明**

        *注意：PDF 生成包含完整的图表和分析，适合打印和分享。*
        """
    )

    st.markdown("---")

    # Show AI advisor status
    has_advisor = st.session_state.get("advisor_response") is not None
    if not has_advisor:
        st.info("💡 提示：您尚未生成 AI 分析。PDF 报告将不包含 AI 投资顾问分析部分。")

    # Generate report button
    if st.button("📥 生成 PDF 报告", type="primary", use_container_width=True):
        with st.spinner("正在生成专业PDF报告...（包含图表和分析）"):
            try:
                report = asyncio.run(
                    _generate_report(
                        user_info=st.session_state.user,
                        risk_profile=st.session_state.risk_profile,
                        portfolio=st.session_state.portfolio,
                        simulation=st.session_state.simulation,
                        advisor_response=st.session_state.get("advisor_response"),
                    )
                )

                st.session_state.report_metadata = {
                    "id": str(report.id) if report.id else None,
                    "status": report.status.value,
                    "pdf_path": report.pdf_path,
                    "file_size_bytes": report.file_size_bytes,
                }

                st.success(f"✅ 报告生成完成！")

            except Exception as e:
                st.error(f"报告生成失败：{str(e)}")

    # Download section
    if st.session_state.get("report_metadata") is not None:
        report_meta = st.session_state.report_metadata
        pdf_path = report_meta.get("pdf_path")

        if pdf_path and os.path.exists(pdf_path):
            st.markdown("---")
            st.markdown("## 📥 下载报告")

            file_size_mb = (report_meta.get("file_size_bytes", 0) or 0) / (1024 * 1024)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("文件大小", f"{file_size_mb:.2f} MB")
            with col2:
                st.metric("状态", "✅ 已生成")

            # Read and provide download
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            st.download_button(
                label="📥 下载 PDF 报告",
                data=pdf_bytes,
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.error("报告文件未找到，请重新生成。")


if __name__ == "__main__":
    show()
