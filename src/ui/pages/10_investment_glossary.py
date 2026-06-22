"""Investment Glossary page.

Searchable bilingual (CN/EN) encyclopedia of investment and finance terms.
Part of the "独立工具" (Independent Tools) module.
"""

import yaml
from pathlib import Path

import streamlit as st

from src.ui.components.sidebar import render_sidebar
from src.ui.i18n import t, _, get_lang

# ── Constants ────────────────────────────────────────────────────────────────

RED_UP = "#e74c3c"
CARD_BG = "#fafbfc"


# ── Data loading ─────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _load_glossary() -> dict:
    """Load glossary from YAML. Cached for instant loading."""
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "investment_glossary.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get_category_map(glossary: dict) -> dict:
    """Build {key: {name, icon}} map from categories list."""
    return {cat["key"]: {"name": cat["name"], "icon": cat["icon"]}
            for cat in glossary.get("categories", [])}


# ── Header ───────────────────────────────────────────────────────────────────

def _render_header():
    """Render page title and description."""
    st.title(t("📚 投资术语百科"))
    st.markdown(
        f"<p style='color:#888;font-size:0.95em'>"
        + t("中英双语投资百科，随时随地查阅金融术语 · 共收录 **{n}** 个术语").format(
            n=len(_load_glossary().get('terms', [])))
        + "</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")


# ── Search & Filter ──────────────────────────────────────────────────────────

def _render_filters(glossary: dict, cat_map: dict):
    """Render search box and category pills. Returns (search_query, selected_category)."""
    col_search, col_cat = st.columns([3, 5])

    with col_search:
        search_query = st.text_input(
            t("🔍 搜索术语"),
            placeholder=t("输入中文或英文关键词搜索…"),
            label_visibility="collapsed",
            key="glossary_search",
        )

    with col_cat:
        # Build category options
        cat_keys = ["all"] + [cat["key"] for cat in glossary.get("categories", [])]
        cat_labels = [t("📂 全部")] + [
            f"{cat['icon']} {t(cat['name'])}" for cat in glossary.get("categories", [])
        ]
        selected = st.selectbox(
            t("类别筛选"),
            options=cat_keys,
            format_func=lambda k: cat_labels[cat_keys.index(k)] if k in cat_keys else k,
            label_visibility="collapsed",
            key="glossary_category",
        )

    return search_query.strip().lower(), selected


# ── Term filtering ───────────────────────────────────────────────────────────

def _filter_terms(glossary: dict, search_query: str, category: str) -> list[dict]:
    """Filter and return matching terms."""
    terms = glossary.get("terms", [])
    results = []

    for term in terms:
        # Category filter
        if category and category != "all":
            if term.get("category") != category:
                continue

        # Search filter (match name_zh, name_en, definition)
        if search_query:
            haystack = " ".join([
                term.get("name_zh", ""),
                term.get("name_en", ""),
                term.get("definition", ""),
            ]).lower()
            if search_query not in haystack:
                continue

        results.append(term)

    return results


# ── Term card ────────────────────────────────────────────────────────────────

def _render_term_card(term: dict, cat_map: dict):
    """Render a single term as a styled card.

    Args:
        term: Dict with name_zh, name_en, category, difficulty, definition, related.
        cat_map: {key: {name, icon}} mapping.
    """
    cat_info = cat_map.get(term.get("category", ""), {})
    cat_icon = cat_info.get("icon", "")
    cat_name = t(cat_info.get("name", term.get("category", "")))

    difficulty = term.get("difficulty", "beginner")
    diff_color = {
        "beginner": "#27ae60",
        "intermediate": "#f39c12",
        "advanced": "#e74c3c",
    }
    diff_label = {
        "beginner": t("入门"),
        "intermediate": t("进阶"),
        "advanced": t("高级"),
    }

    with st.container(border=True):
        # Row 1: Chinese name + English name + badges
        col_name, col_badges = st.columns([3, 1.2])

        with col_name:
            # In English mode, show English name as primary
            if get_lang() == 'en':
                primary = term['name_en']
                secondary = term['name_zh']
            else:
                primary = term['name_zh']
                secondary = term['name_en']
            st.markdown(
                f"<span style='font-size:1.15em;font-weight:600'>{primary}</span>"
                f"&nbsp;&nbsp;"
                f"<span style='color:#888;font-size:0.85em'>{secondary}</span>",
                unsafe_allow_html=True,
            )

        with col_badges:
            diff_color_hex = diff_color.get(difficulty, "#888")
            st.markdown(
                f"<div style='text-align:right'>"
                f"<span style='background:{diff_color_hex}15;color:{diff_color_hex};"
                f"padding:2px 10px;border-radius:12px;font-size:0.75em;margin-right:6px'>"
                f"{diff_label.get(difficulty, difficulty)}</span>"
                f"<span style='background:#f0f0f0;padding:2px 10px;border-radius:12px;"
                f"font-size:0.75em'>{cat_icon} {cat_name}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # Row 2: Definition
        if get_lang() == 'en' and term.get('definition_en'):
            def_text = term['definition_en'].strip()
        else:
            def_text = term['definition'].strip()
        st.markdown(
            f"<p style='margin-top:8px;margin-bottom:6px;line-height:1.7;color:#444;font-size:0.93em'>"
            f"{def_text}</p>",
            unsafe_allow_html=True,
        )

        # Row 3: Related terms (if any)
        related = term.get("related", [])
        if related:
            related_labels = []
            all_terms = {t["id"]: t for t in _load_glossary().get("terms", [])}
            for rel_id in related:
                rel_term = all_terms.get(rel_id)
                if rel_term:
                    related_labels.append(rel_term["name_zh"])
            if related_labels:
                st.markdown(
                    "<div style='font-size:0.78em;color:#aaa;margin-top:4px'>"
                    "📎 " + t("相关术语：") + " · ".join(related_labels) +
                    "</div>",
                    unsafe_allow_html=True,
                )

    # Small gap between cards
    st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)


# ── Main entry ───────────────────────────────────────────────────────────────

def show():
    """Display the Investment Glossary page."""
    render_sidebar()

    glossary = _load_glossary()
    cat_map = _get_category_map(glossary)
    total_count = len(glossary.get("terms", []))

    _render_header()
    search_query, category = _render_filters(glossary, cat_map)
    results = _filter_terms(glossary, search_query, category)

    # Result count
    if search_query or (category and category != "all"):
        st.markdown(
            f"<p style='color:#888;font-size:0.85em;margin-bottom:12px'>"
            + t("找到 **{n}** / {total} 个术语").format(n=len(results), total=total_count)
            + "</p>",
            unsafe_allow_html=True,
        )

    if not results:
        st.info(t("📭 没有找到匹配的术语，试试更换关键词或类别筛选。"))
        return

    # Render term cards
    for term in results:
        _render_term_card(term, cat_map)

    # Footer
    st.markdown("---")
    st.caption(
        t("📚 投资术语百科 — 磐策 PánCè 知识库。内容仅供参考学习，不构成投资建议。")
    )


if __name__ == "__main__":
    show()
