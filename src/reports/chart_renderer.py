"""Chart renderer - exports Plotly figures to static PNG images for PDF.

Uses kaleido for high-quality static image export.
"""

import io
import tempfile
from pathlib import Path

import numpy as np
import plotly.graph_objects as go


def render_pie_chart(allocations: list[dict]) -> io.BytesIO:
    """Render asset allocation pie chart to PNG bytes.

    Args:
        allocations: List of {ticker, name, weight} dicts.

    Returns:
        BytesIO buffer containing PNG image.
    """
    fig = go.Figure(
        data=[
            go.Pie(
                labels=[f"{a['ticker']} ({a['weight']*100:.1f}%)" for a in allocations],
                values=[a["weight"] for a in allocations],
                hole=0.35,
                textinfo="label+percent",
                marker=dict(
                    colors=[
                        "#4285f4", "#34a853", "#fbbc04", "#ea4335",
                        "#46bdc6", "#9c27b0", "#ff6f00", "#607d8b",
                    ][: len(allocations)]
                ),
            )
        ]
    )
    fig.update_layout(
        width=600,
        height=500,
        margin=dict(l=20, r=20, t=40, b=20),
        title="资产配置比例",
    )

    buf = io.BytesIO()
    fig.write_image(buf, format="png", engine="kaleido")
    buf.seek(0)
    return buf


def render_fan_chart(simulation: dict) -> io.BytesIO:
    """Render Monte Carlo fan chart to PNG.

    Args:
        simulation: Simulation result dict with yearly_projections.

    Returns:
        BytesIO buffer containing PNG image.
    """
    years = [p["year"] for p in simulation["yearly_projections"]]

    fig = go.Figure()

    # P10-P90 band
    p90 = [p["percentile_90"] for p in simulation["yearly_projections"]]
    p10 = [p["percentile_10"] for p in simulation["yearly_projections"]]
    fig.add_trace(
        go.Scatter(
            x=years + years[::-1],
            y=p90 + p10[::-1],
            fill="toself",
            fillcolor="rgba(66, 133, 244, 0.2)",
            line=dict(color="rgba(255, 255, 255, 0)"),
            name="P10-P90",
        )
    )

    # P25-P75 band
    p75 = [p["percentile_75"] for p in simulation["yearly_projections"]]
    p25 = [p["percentile_25"] for p in simulation["yearly_projections"]]
    fig.add_trace(
        go.Scatter(
            x=years + years[::-1],
            y=p75 + p25[::-1],
            fill="toself",
            fillcolor="rgba(66, 133, 244, 0.4)",
            line=dict(color="rgba(255, 255, 255, 0)"),
            name="P25-P75",
        )
    )

    # Median
    p50 = [p["percentile_50"] for p in simulation["yearly_projections"]]
    fig.add_trace(
        go.Scatter(
            x=years,
            y=p50,
            mode="lines+markers",
            line=dict(color="#1a73e8", width=3),
            name="中位数 (P50)",
        )
    )

    fig.add_hline(
        y=simulation["initial_amount"],
        line_dash="dash",
        line_color="gray",
        annotation_text="初始投资",
    )

    fig.update_layout(
        width=700,
        height=450,
        xaxis_title="年",
        yaxis_title="组合价值 (¥)",
        template="plotly_white",
        title="Monte Carlo 收益路径模拟",
    )

    buf = io.BytesIO()
    fig.write_image(buf, format="png", engine="kaleido")
    buf.seek(0)
    return buf


def render_histogram(simulation: dict) -> io.BytesIO:
    """Render final value distribution histogram to PNG.

    Args:
        simulation: Simulation result dict with final_values.

    Returns:
        BytesIO buffer containing PNG image.
    """
    final_values = simulation.get("final_values")
    if not final_values:
        # Create empty figure
        fig = go.Figure()
        fig.update_layout(title="无分布数据")
        buf = io.BytesIO()
        fig.write_image(buf, format="png", engine="kaleido")
        buf.seek(0)
        return buf

    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=final_values,
            nbinsx=60,
            marker_color="#4285f4",
            opacity=0.75,
            name="终值分布",
        )
    )

    # Percentile lines
    for value, color, label in [
        (simulation["percentile_5"], "red", "P5"),
        (simulation["median_final_value"], "blue", "P50"),
        (simulation["percentile_95"], "green", "P95"),
    ]:
        fig.add_vline(
            x=value,
            line_dash="dash",
            line_color=color,
            annotation_text=label,
        )

    fig.update_layout(
        width=700,
        height=400,
        xaxis_title="组合终值 (¥)",
        yaxis_title="频次",
        showlegend=False,
        template="plotly_white",
        title="终值概率分布",
    )

    buf = io.BytesIO()
    fig.write_image(buf, format="png", engine="kaleido")
    buf.seek(0)
    return buf
