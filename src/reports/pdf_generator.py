"""PDF document generator using ReportLab.

Builds a professional investment report with:
- Cover page
- Executive summary
- Risk profile summary
- Portfolio allocation (table + pie chart)
- Performance metrics
- Monte Carlo simulation results (fan chart + histogram)
- AI advisor analysis
- Financial planning & recommendations
- Risk disclaimers

Supports Chinese fonts (SimHei on Windows, fallback to search).
"""

import io
import os
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    NextPageTemplate,
    PageBreak,
    HRFlowable,
)

# ── Chinese font registration ──────────────────────────────────────────

_cjk_font_name = None


def _find_cjk_font() -> str | None:
    """Find an available CJK (Chinese/Japanese/Korean) TTF font on the system."""
    search_paths = [
        # Windows
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/Deng.ttf",
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        # Linux
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    ]
    for path in search_paths:
        if os.path.exists(path):
            return path
    return None


def _register_cjk_font() -> str:
    """Register a CJK font and return its name. Falls back to Helvetica if none found."""
    global _cjk_font_name
    if _cjk_font_name is not None:
        return _cjk_font_name

    font_path = _find_cjk_font()
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont("CJKFont", font_path))
            _cjk_font_name = "CJKFont"
            return _cjk_font_name
        except Exception:
            pass

    # Fallback: use built-in Helvetica (no Chinese support, but won't crash)
    _cjk_font_name = "Helvetica"
    return _cjk_font_name


# ── PDF Generator ───────────────────────────────────────────────────────

class PDFGenerator:
    """Generates professional PDF investment reports using ReportLab."""

    def __init__(self, output_path: str):
        self.output_path = output_path
        self.width, self.height = A4
        self.font = _register_cjk_font()
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self.story = []

    def _cjk(self, base_style: str, **overrides) -> ParagraphStyle:
        """Create a ParagraphStyle using the CJK font."""
        parent = self.styles[base_style] if base_style in self.styles else self.styles["Normal"]
        kwargs = {"fontName": self.font, "parent": parent}
        kwargs.update(overrides)
        return ParagraphStyle(f"{base_style}_cjk_{id(kwargs)}", **kwargs)

    def _setup_styles(self):
        """Configure all paragraph styles with CJK font support."""
        font = self.font

        self.styles.add(ParagraphStyle(
            "CoverTitle", fontName=font, fontSize=28, leading=38,
            alignment=TA_CENTER, textColor=colors.HexColor("#1a237e"), spaceAfter=20,
        ))
        self.styles.add(ParagraphStyle(
            "CoverSubtitle", fontName=font, fontSize=14, leading=20,
            alignment=TA_CENTER, textColor=colors.HexColor("#555555"), spaceAfter=10,
        ))
        self.styles.add(ParagraphStyle(
            "SectionHeader", fontName=font, fontSize=18, leading=24,
            textColor=colors.HexColor("#1a237e"), spaceBefore=24, spaceAfter=12,
        ))
        self.styles.add(ParagraphStyle(
            "SubHeader", fontName=font, fontSize=13, leading=18,
            textColor=colors.HexColor("#333333"), spaceBefore=16, spaceAfter=8,
        ))
        self.styles.add(ParagraphStyle(
            "BodyTextCN", fontName=font, fontSize=10, leading=17,
            alignment=TA_JUSTIFY, spaceBefore=4, spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            "DisclaimerCN", fontName=font, fontSize=7.5, leading=11,
            textColor=colors.HexColor("#888888"), alignment=TA_JUSTIFY,
        ))
        self.styles.add(ParagraphStyle(
            "TableHeaderCN", fontName=font, fontSize=9, leading=12,
            textColor=colors.white, alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            "TableCellCN", fontName=font, fontSize=8.5, leading=12, alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            "HighlightBox", fontName=font, fontSize=10, leading=16,
            textColor=colors.HexColor("#1a237e"), alignment=TA_LEFT,
            backColor=colors.HexColor("#e8eaf6"),
            borderPadding=10, spaceBefore=10, spaceAfter=10,
        ))

    # ── Page sections ───────────────────────────────────────────────────

    def add_cover_page(self, user_info: dict):
        """Premium cover page."""
        self.story.append(Spacer(1, 60 * mm))
        self.story.append(Paragraph("AI Robo Advisor", self.styles["CoverTitle"]))
        self.story.append(Paragraph("智能投资顾问报告", self.styles["CoverTitle"]))
        self.story.append(Spacer(1, 8 * mm))

        # Decorative line
        self.story.append(HRFlowable(
            width="40%", thickness=2, color=colors.HexColor("#1a237e"),
            spaceBefore=5, spaceAfter=15,
        ))

        self.story.append(Paragraph(
            f"生成日期：{datetime.now().strftime('%Y年%m月%d日')}",
            self.styles["CoverSubtitle"],
        ))
        if user_info.get("display_name"):
            self.story.append(Paragraph(
                f"尊敬的 {user_info['display_name']} 女士/先生",
                self.styles["CoverSubtitle"],
            ))
        self.story.append(Spacer(1, 40 * mm))
        self.story.append(Paragraph(
            "本报告由AI自动生成，仅供学习参考 | 投资有风险，入市需谨慎",
            self.styles["DisclaimerCN"],
        ))
        self.story.append(NextPageTemplate("main"))
        self.story.append(PageBreak())

    def add_executive_summary(self, risk_profile: dict, portfolio: dict, simulation: dict):
        """Executive summary with key takeaways."""
        self.story.append(Paragraph("报告摘要", self.styles["SectionHeader"]))

        level = risk_profile.get("risk_level_label", "N/A")
        score = risk_profile.get("total_score", 0) * 100
        ret = portfolio.get("expected_return", 0) * 100
        vol = portfolio.get("volatility", 0) * 100
        sharpe = portfolio.get("sharpe_ratio", 0)
        prob = simulation.get("probability_positive", 0) * 100
        median_final = simulation.get("median_final_value", 0)
        initial = simulation.get("initial_amount", 1)
        total_ret = ((median_final / initial) - 1) * 100 if initial else 0

        summary = (
            f"根据您的风险测评结果，您的风险等级为<b>{level}</b>（评分 {score:.0f}%）。"
            f"我们为您配置了一个预期年化收益率为 <b>{ret:.2f}%</b>、年化波动率为 <b>{vol:.2f}%</b> "
            f"（夏普比率 {sharpe:.2f}）的多元化投资组合。"
            f"Monte Carlo 模拟显示，在未来 {simulation.get('horizon_years', 'N/A')} 年的投资期内，"
            f"您的投资组合有 <b>{prob:.1f}%</b> 的概率实现正收益，"
            f"预期终值中位数为 <b>¥{median_final:,.0f}</b>（总收益约 {total_ret:.1f}%）。"
        )
        self.story.append(Paragraph(summary, self.styles["HighlightBox"]))
        self.story.append(Spacer(1, 6 * mm))

    def add_risk_summary(self, risk_profile: dict):
        """Risk assessment summary section."""
        self.story.append(Paragraph("1. 风险测评结果", self.styles["SectionHeader"]))

        level = risk_profile.get("risk_level_label", "N/A")
        score = risk_profile.get("total_score", 0) * 100

        self.story.append(Paragraph(
            f"风险等级：<b>{level}</b>&nbsp;&nbsp;|&nbsp;&nbsp;风险评分：<b>{score:.0f}%</b>",
            self.styles["BodyTextCN"],
        ))

        desc = risk_profile.get("risk_level_description", "")
        if desc:
            self.story.append(Paragraph(
                f"<i>{desc}</i>", self.styles["BodyTextCN"]
            ))

        cat_scores = risk_profile.get("category_scores", {})
        if cat_scores:
            self.story.append(Paragraph("各维度得分", self.styles["SubHeader"]))
            cat_labels = {
                "time_horizon": "投资期限适配度",
                "financial_situation": "财务稳健度",
                "risk_tolerance": "风险承受能力",
                "investment_preference": "投资偏好进取度",
                "knowledge_experience": "投资知识经验",
            }
            for cat, score_val in cat_scores.items():
                label = cat_labels.get(cat, cat)
                pct = float(score_val) * 100
                bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
                self.story.append(Paragraph(
                    f"• {label}：{bar} {pct:.0f}%",
                    self.styles["BodyTextCN"],
                ))

    def add_portfolio_section(self, portfolio: dict, pie_chart_buf: io.BytesIO):
        """Portfolio allocation section with pie chart."""
        self.story.append(Paragraph("2. 投资组合配置", self.styles["SectionHeader"]))

        # Key metrics in a styled box
        self.story.append(Paragraph("核心指标", self.styles["SubHeader"]))
        metrics_text = (
            f"预期年化收益率：<b>{portfolio['expected_return'] * 100:.2f}%</b>&nbsp;&nbsp;|&nbsp;&nbsp;"
            f"年化波动率：<b>{portfolio['volatility'] * 100:.2f}%</b>&nbsp;&nbsp;|&nbsp;&nbsp;"
            f"夏普比率：<b>{portfolio['sharpe_ratio']:.2f}</b>&nbsp;&nbsp;|&nbsp;&nbsp;"
            f"估计最大回撤：<b>{portfolio['max_drawdown'] * 100:.2f}%</b>"
        )
        self.story.append(Paragraph(metrics_text, self.styles["HighlightBox"]))

        # Allocation table
        self.story.append(Paragraph("持仓明细", self.styles["SubHeader"]))
        table_data = [["代码", "名称", "资产类别", "配置比例", "预期收益", "波动率"]]
        for a in portfolio["allocations"]:
            table_data.append([
                a["ticker"], a["name"][:25], a["asset_class"],
                f"{a['weight'] * 100:.1f}%",
                f"{a['expected_return'] * 100:.2f}%",
                f"{a['volatility'] * 100:.2f}%",
            ])

        table = Table(table_data, colWidths=[50, 120, 55, 60, 60, 60])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, -1), self.font),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        self.story.append(table)
        self.story.append(Spacer(1, 8 * mm))

        # Class summary
        class_map = {}
        class_labels = {"equity": "股票", "bond": "债券", "gold": "黄金", "real_estate": "房地产"}
        for a in portfolio["allocations"]:
            cls = a["asset_class"]
            class_map[cls] = class_map.get(cls, 0) + a["weight"]

        summary_parts = []
        for cls, weight in class_map.items():
            label = class_labels.get(cls, cls)
            summary_parts.append(f"{label} {weight * 100:.1f}%")
        self.story.append(Paragraph(
            "大类资产分布：" + " &nbsp;|&nbsp; ".join(summary_parts),
            self.styles["BodyTextCN"],
        ))

        # Pie chart
        self.story.append(Spacer(1, 6 * mm))
        pie_chart_buf.seek(0)
        img = Image(pie_chart_buf, width=140 * mm, height=110 * mm)
        self.story.append(img)

    def add_simulation_section(self, simulation: dict, fan_chart_buf: io.BytesIO, hist_buf: io.BytesIO):
        """Monte Carlo simulation results."""
        self.story.append(Paragraph("3. Monte Carlo 模拟分析", self.styles["SectionHeader"]))

        horizon = simulation.get("horizon_years", "N/A")
        initial = simulation.get("initial_amount", 0)
        paths = simulation.get("num_paths", 0)

        self.story.append(Paragraph("模拟设定", self.styles["SubHeader"]))
        self.story.append(Paragraph(
            f"初始投资 <b>¥{initial:,.0f}</b> | 投资期限 <b>{horizon}年</b> | "
            f"模拟 <b>{paths:,}</b> 条路径（基于几何布朗运动模型）",
            self.styles["BodyTextCN"],
        ))

        self.story.append(Paragraph("关键统计", self.styles["SubHeader"]))
        median = simulation.get("median_final_value", 0)
        p5 = simulation.get("percentile_5", 0)
        p95 = simulation.get("percentile_95", 0)
        var95 = simulation.get("var_95", 0)
        prob = simulation.get("probability_positive", 0) * 100

        self.story.append(Paragraph(
            f"• 预期终值（中位数）：<b>¥{median:,.0f}</b> | "
            f"总收益率约 <b>{((median / initial - 1) * 100) if initial else 0:.1f}%</b>",
            self.styles["BodyTextCN"],
        ))
        self.story.append(Paragraph(
            f"• 悲观情景 (P5, 95%置信下限)：<b>¥{p5:,.0f}</b> | "
            f"乐观情景 (P95, 95%置信上限)：<b>¥{p95:,.0f}</b>",
            self.styles["BodyTextCN"],
        ))
        self.story.append(Paragraph(
            f"• 95% VaR（在险价值）：<b>¥{var95:,.0f}</b> | "
            f"实现正收益概率：<b>{prob:.1f}%</b>",
            self.styles["BodyTextCN"],
        ))

        # Fan chart
        self.story.append(Spacer(1, 4 * mm))
        self.story.append(Paragraph("收益路径模拟图", self.styles["SubHeader"]))
        fan_chart_buf.seek(0)
        self.story.append(Image(fan_chart_buf, width=160 * mm, height=100 * mm))

        # Histogram
        self.story.append(Paragraph("终值概率分布", self.styles["SubHeader"]))
        hist_buf.seek(0)
        self.story.append(Image(hist_buf, width=160 * mm, height=90 * mm))

    def add_advisor_section(self, advisor_response: dict | None):
        """AI advisor analysis section."""
        self.story.append(Paragraph("4. AI 投资顾问深度分析", self.styles["SectionHeader"]))

        if advisor_response is None:
            self.story.append(Paragraph(
                '未生成AI分析。如需获取AI深度分析，请先在应用中点击「生成 AI 分析」按钮。',
                self.styles["BodyTextCN"],
            ))
            return

        # Summary
        s = advisor_response.get("summary", "")
        if s:
            self.story.append(Paragraph("投资组合概述", self.styles["SubHeader"]))
            self.story.append(Paragraph(s, self.styles["BodyTextCN"]))

        # Allocation rationale
        rationale = advisor_response.get("allocation_rationale", "")
        if rationale:
            self.story.append(Paragraph("配置逻辑详解", self.styles["SubHeader"]))
            self.story.append(Paragraph(rationale, self.styles["BodyTextCN"]))

        # Key risks
        risks = advisor_response.get("key_risks", [])
        if risks:
            self.story.append(Paragraph("风险全景图", self.styles["SubHeader"]))
            for risk in risks:
                sev_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    risk.get("severity", ""), "⚪"
                )
                self.story.append(Paragraph(
                    f"{sev_icon} <b>{risk.get('risk_name', '')}</b>",
                    self.styles["BodyTextCN"],
                ))
                desc = risk.get("description", "")
                if desc:
                    self.story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{desc}", self.styles["BodyTextCN"]))
                mitigation = risk.get("mitigation", "")
                if mitigation:
                    self.story.append(Paragraph(
                        f"&nbsp;&nbsp;&nbsp;&nbsp;<i>对策：{mitigation}</i>",
                        self.styles["BodyTextCN"],
                    ))

        # Market scenarios
        scenarios = advisor_response.get("market_scenarios", [])
        if scenarios:
            self.story.append(Paragraph("市场情景推演", self.styles["SubHeader"]))
            for sc in scenarios:
                self.story.append(Paragraph(
                    f"<b>{sc.get('scenario', '')}</b>（可能性：{sc.get('probability', 'N/A')}）",
                    self.styles["BodyTextCN"],
                ))
                if sc.get("description"):
                    self.story.append(Paragraph(
                        f"&nbsp;&nbsp;&nbsp;&nbsp;{sc['description']}", self.styles["BodyTextCN"]
                    ))
                if sc.get("projected_impact"):
                    self.story.append(Paragraph(
                        f"&nbsp;&nbsp;&nbsp;&nbsp;影响预估：{sc['projected_impact']}",
                        self.styles["BodyTextCN"],
                    ))

        # Recommendations
        recs = advisor_response.get("investment_recommendations", "")
        if recs:
            self.story.append(Paragraph("投资建议", self.styles["SubHeader"]))
            self.story.append(Paragraph(recs, self.styles["HighlightBox"]))

    def add_financial_plan(self, user_info: dict, portfolio: dict, simulation: dict):
        """Add personalized financial planning section."""
        self.story.append(Paragraph("5. 个人财务规划建议", self.styles["SectionHeader"]))

        age = user_info.get("age", 0)
        income = user_info.get("income", 0)
        assets = user_info.get("asset_size", 0)
        horizon = simulation.get("horizon_years", 5)
        goal = user_info.get("investment_goal", "未指定")

        # Portfolio analysis
        equity_weight = sum(
            a["weight"] for a in portfolio.get("allocations", [])
            if a.get("asset_class") == "equity"
        )

        # Generate personalized advice based on user profile
        advice_parts = []

        # Age-based
        if age < 30:
            advice_parts.append(
                "您处于财富积累的早期阶段，时间优势明显。建议保持较高比例的权益类配置，"
                "利用长期复利效应实现资产增值。随着收入增长，逐步提高定投金额。"
            )
        elif age < 45:
            advice_parts.append(
                "您处于职业和收入的黄金期，应充分利用收入增长加速资产积累。建议保持"
                "股债平衡的配置，开始为子女教育和退休规划做系统性储备。"
            )
        else:
            advice_parts.append(
                "您已进入财富保值与增长并重的阶段。建议逐步降低权益比例，增加固收类"
                "资产，注重现金流的稳定性和资产的保值功能。"
            )

        # Income-based
        if income > 0:
            invest_ratio = assets / income if income > 0 else 0
            advice_parts.append(
                f"您的可投资资产约为年收入的 {invest_ratio:.1f} 倍。"
                f"建议每月将收入的 15%-25% 用于定期投资，建立纪律化的投资习惯。"
            )

        # Goal-based
        if goal and goal != "未指定":
            advice_parts.append(f"针对您的投资目标「{goal}」，我们建议将此投资组合作为核心配置，并根据目标的时间节点动态调整风险暴露。")

        # Horizon-based
        advice_parts.append(
            f"在 {horizon} 年的投资期限内，建议每半年至一年进行一次组合再平衡，"
            f"将各类资产的比例恢复至目标配置，以控制风险并捕捉再平衡收益。"
        )

        for part in advice_parts:
            self.story.append(Paragraph(f"• {part}", self.styles["BodyTextCN"]))

        # Action plan
        self.story.append(Paragraph("行动建议", self.styles["SubHeader"]))
        steps = [
            "立即行动：在完成风险评估后，按照推荐比例配置资产，避免因犹豫而错失市场机会。",
            "分批建仓：如有大额资金，建议分3-6个月逐步建仓，降低单点入市风险。",
            "定期定额：设定每月固定日期定额投资，利用平均成本法平滑市场波动。",
            "年度检视：每年进行一次投资组合检视和风险重评，确保配置与人生阶段匹配。",
            "持续学习：关注宏观经济和投资知识，提高独立判断能力，不盲从市场情绪。",
        ]
        for i, step in enumerate(steps, 1):
            self.story.append(Paragraph(f"{i}. {step}", self.styles["BodyTextCN"]))

    def add_glossary(self):
        """Add a glossary of key financial terms."""
        self.story.append(Paragraph("6. 关键术语解释", self.styles["SectionHeader"]))
        terms = [
            ("夏普比率 (Sharpe Ratio)", "衡量投资组合每单位风险所获得的超额回报。大于1为良好，大于2为优秀。"),
            ("最大回撤 (Max Drawdown)", "投资组合从峰值到谷底的最大跌幅，反映最坏情况下的损失幅度。"),
            ("Monte Carlo 模拟", "基于随机过程的统计模拟方法，用于预测投资组合在未来不同市场条件下的可能表现。"),
            ("VaR (Value at Risk)", "在给定置信水平下，投资组合在特定时期内的最大可能损失。"),
            ("几何布朗运动 (GBM)", "描述资产价格随机波动的数学模型，是Monte Carlo模拟的基础。"),
            ("ETF (交易型开放式指数基金)", "在交易所上市交易的指数基金，具有低成本、高透明度和流动性好的特点。"),
        ]
        for title, desc in terms:
            self.story.append(Paragraph(f"<b>{title}</b>：{desc}", self.styles["BodyTextCN"]))

    def add_disclaimer(self):
        """Add risk disclaimer."""
        self.story.append(Paragraph("7. 风险提示与免责声明", self.styles["SectionHeader"]))

        disclaimer_path = Path(__file__).parent / "templates" / "disclaimer.txt"
        if disclaimer_path.exists():
            text = disclaimer_path.read_text(encoding="utf-8")
        else:
            text = "投资有风险，过往表现不代表未来收益。本报告仅供参考，不构成投资建议。"

        for line in text.split("\n"):
            line = line.strip()
            if line:
                self.story.append(Paragraph(line, self.styles["DisclaimerCN"]))

    def build(self) -> str:
        """Build the PDF document and save to file."""
        doc = BaseDocTemplate(
            self.output_path,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        main_frame = Frame(
            20 * mm, 15 * mm,
            self.width - 40 * mm,
            self.height - 30 * mm,
            id="main",
        )
        main_template = PageTemplate(id="main", frames=[main_frame])
        doc.addPageTemplates([main_template])

        doc.build(self.story)
        return self.output_path
