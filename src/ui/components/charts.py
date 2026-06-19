"""Reusable chart components for Streamlit UI."""

import plotly.graph_objects as go
import plotly.express as px
from src.ui.i18n import t, _


def create_gauge_chart(
    value: float,
    title: str = "",
    min_val: float = 0.0,
    max_val: float = 1.0,
    color: str = "#4285f4",
) -> go.Figure:
    """Create a gauge/donut chart showing a percentage value.

    Args:
        value: Current value (0-1).
        title: Chart title.
        min_val: Minimum value.
        max_val: Maximum value.
        color: Bar color hex.

    Returns:
        Plotly figure.
    """
    pct = (value - min_val) / (max_val - min_val) * 100

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=pct,
            title={"text": title},
            number={"suffix": "%"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, 30], "color": "#e8f0fe"},
                    {"range": [30, 60], "color": "#d2e3fc"},
                    {"range": [60, 80], "color": "#aecbfa"},
                    {"range": [80, 100], "color": "#8ab4f8"},
                ],
            },
        )
    )

    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig


def create_waterfall_chart(
    categories: list[str],
    values: list[float],
    title: str = "",
) -> go.Figure:
    """Create a waterfall chart for asset class breakdown.

    Args:
        categories: Category labels.
        values: Values per category.
        title: Chart title.

    Returns:
        Plotly figure.
    """
    fig = go.Figure(
        go.Waterfall(
            name="",
            orientation="v",
            measure=["relative"] * len(categories),
            x=categories,
            y=values,
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "#34a853"}},
            increasing={"marker": {"color": "#4285f4"}},
            totals={"marker": {"color": "#1a237e"}},
        )
    )

    fig.update_layout(
        title=title,
        height=350,
        showlegend=False,
    )

    return fig


def create_risk_radar(
    category_scores: dict[str, float],
    title: str = "",
) -> go.Figure:
    """Create a radar/spider chart for risk category scores.

    Args:
        category_scores: Dict mapping category names to scores (0-1).
        title: Chart title.

    Returns:
        Plotly figure.
    """
    if not title:
        title = t("风险画像")

    cat_labels = {
        "time_horizon": t("投资期限"),
        "financial_situation": t("财务状况"),
        "risk_tolerance": t("风险承受"),
        "investment_preference": t("投资偏好"),
        "knowledge_experience": t("知识经验"),
    }

    categories = [cat_labels.get(k, k) for k in category_scores.keys()]
    values = [v * 100 for v in category_scores.values()]

    fig = go.Figure(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            marker=dict(color="#4285f4"),
            line=dict(color="#1a237e", width=2),
            name=t("风险评分"),
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                showticklabels=False,
            ),
        ),
        title=title,
        height=400,
        showlegend=False,
    )

    return fig
