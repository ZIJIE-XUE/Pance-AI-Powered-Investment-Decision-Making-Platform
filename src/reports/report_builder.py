"""Report builder - orchestrates the assembly of a complete investment report PDF.

Coordinates chart rendering, PDF generation, and file output.
"""

import io
import uuid
from datetime import datetime
from pathlib import Path

from src.reports.chart_renderer import (
    render_pie_chart,
    render_fan_chart,
    render_histogram,
)
from src.reports.pdf_generator import PDFGenerator
from src.utils.exceptions import ReportGenerationError
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ReportBuilder:
    """Builds a complete AI Robo Advisor investment report PDF."""

    def __init__(self, output_dir: Path | None = None):
        if output_dir is None:
            output_dir = Path("reports_output")
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_report(
        self,
        user_info: dict,
        risk_profile: dict,
        portfolio: dict,
        simulation: dict,
        advisor_response: dict | None = None,
    ) -> str:
        """Assemble and generate a complete PDF investment report.

        Args:
            user_info: User profile data.
            risk_profile: Risk assessment result.
            portfolio: Portfolio optimization result.
            simulation: Monte Carlo simulation result.
            advisor_response: AI advisor analysis (optional).

        Returns:
            Path to the generated PDF file.

        Raises:
            ReportGenerationError: If report generation fails.
        """
        try:
            # Generate charts
            logger.info("rendering_charts")

            pie_buf = render_pie_chart(portfolio["allocations"])
            fan_buf = render_fan_chart(simulation)
            hist_buf = render_histogram(simulation)

            # Generate PDF
            report_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"investment_report_{timestamp}_{report_id}.pdf"
            output_path = str(self.output_dir / filename)

            logger.info("building_pdf", path=output_path)

            pdf = PDFGenerator(output_path)

            # Assemble all report sections
            pdf.add_cover_page(user_info)
            pdf.add_executive_summary(risk_profile, portfolio, simulation)
            pdf.add_risk_summary(risk_profile)
            pdf.add_portfolio_section(portfolio, pie_buf)
            pdf.add_simulation_section(simulation, fan_buf, hist_buf)
            pdf.add_advisor_section(advisor_response)
            pdf.add_financial_plan(user_info, portfolio, simulation)
            pdf.add_glossary()
            pdf.add_disclaimer()

            # Build the PDF
            pdf.build()

            # Clean up chart buffers
            pie_buf.close()
            fan_buf.close()
            hist_buf.close()

            logger.info("report_generated", path=output_path)

            return output_path

        except Exception as e:
            logger.error("report_generation_failed", error=str(e))
            raise ReportGenerationError(f"报告生成失败: {str(e)}")
