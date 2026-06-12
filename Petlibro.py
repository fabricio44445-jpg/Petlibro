"""Petlibro: live brand intelligence dashboard for Petlibro on Streamlit."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import html
import os
import re

import altair as alt
import pandas as pd
import streamlit as st

from archive import load_archive as load_repository_history
from collectors import SOURCE_ICONS, collect_mentions, deduplicate


st.set_page_config(
    page_title="Petlibro Intelligence | Petlibro",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

SOURCES = ["Google News", "Reddit", "YouTube", "Blogs", "Publication feeds"]
DEFAULT_BRANDS = ["Petlibro", "Catit", "Sure Petcare", "Whistle"]
STOP_WORDS = {
    "about", "after", "again", "against", "also", "been", "before", "being",
    "feeder", "feeders", "fountain", "fountains", "cat", "cats", "dog", "dogs",
    "pet", "pets", "smart", "could", "from", "have", "into", "more", "most",
    "news", "over", "review", "device", "app", "than", "that", "their",
    "there", "these", "they", "this", "video", "what", "when", "where",
    "which", "while", "with", "would", "your",
}


def secret(name: str) -> str | None:
    try:
        return str(st.secrets[name])
    except (KeyError, FileNotFoundError):
        return os.getenv(name)


@st.cache_data(ttl=900, show_spinner=False)
def load_mentions(
    brands: tuple[str, ...],
    sources: tuple[str, ...],
    youtube_api_key: str | None,
    schema_version: int = 2,
    publication_feed_urls: tuple[str, ...] = (),
) -> tuple[list[dict], list[dict]]:
    del schema_version
    return collect_mentions(
        list(brands),
        list(sources),
        youtube_api_key,
        custom_feed_urls=list(publication_feed_urls),
    )


@st.cache_data(ttl=900, show_spinner=False)
def load_archive(
    brands: tuple[str, ...],
    schema_version: int = 1,
) -> list[dict]:
    del schema_version
    return load_repository_history(list(brands), days=30)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
          --ink:#1B3D0C; --muted:#3D5B2A; --line:#A8C97D;
          --primary:#2D5016; --primary-dark:#1B3D0C; --soft:#E8F0DC;
          --positive:#2D8659; --negative:#D45B5B; --warning:#C89E4F;
          --canvas:#F5F1E8; --surface:#FEFDFB; --nav:#2D5016;
        }
        .stApp { background:var(--canvas); color:var(--ink); }
        [data-testid="stHeader"] { background:rgba(245,241,232,.98); }
        [data-testid="stSidebar"] { background:var(--nav); border-right:1px solid #4A7C2C; }
        [data-testid="stSidebar"] * { color:#F5F1E8; }
        [data-testid="stSidebar"] .stButton button {
          background:#4A7C2C; color:#FEFDFB; border:1px solid #6B9A47; font-weight:800;
          min-height:2.8rem;
        }
        [data-testid="stSidebar"] .stButton button:hover {
          background:#5A9436; border-color:#8DB75A;
        }
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
          color:#E8F0DC; font-size:.8rem; font-weight:800;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-baseweb="input"] > div,
        [data-testid="stSidebar"] input {
          background:#FEFDFB !important; color:#1B3D0C !important;
          border-color:#A8C97D !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] > div *,
        [data-testid="stSidebar"] [data-baseweb="input"] > div *,
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] [role="combobox"] {
          color:#1B3D0C !important;
          -webkit-text-fill-color:#1B3D0C !important;
          opacity:1 !important;
        }
        [data-testid="stSidebar"] input::placeholder { color:#6B8A59 !important; opacity:1; }
        [data-testid="stSidebar"] [data-baseweb="tag"] {
          background:#E8F0DC !important; border:1px solid #A8C97D !important;
        }
        [data-testid="stSidebar"] [data-baseweb="tag"] * { color:#2D5016 !important; }
        [data-testid="stSidebar"] svg { fill:#2D5016; }
        [data-baseweb="popover"] [role="option"],
        [data-baseweb="popover"] li {
          background:#FEFDFB !important; color:#1B3D0C !important;
          -webkit-text-fill-color:#1B3D0C !important;
        }
        [data-baseweb="popover"] [aria-selected="true"] {
          background:#E8F0DC !important; color:#2D5016 !important;
        }
        [data-testid="stSidebar"] hr { border-color:#4A7C2C; }
        [data-testid="stSidebar"] small,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
          color:#D9E5CC !important;
        }
        .block-container { max-width:1500px; padding-top:4.25rem; }
        h1,h2,h3 { letter-spacing:-.025em; color:#1B3D0C; }
        h1 { font-size:2rem !important; }
        .hero {
          background:linear-gradient(115deg,#2D5016 0%,#4A7C2C 68%,#6B9A47 100%);
          border:1px solid #8DB75A; border-radius:18px; padding:1.35rem 1.55rem;
          box-shadow:0 16px 45px rgba(45,80,22,.2); margin-bottom:1rem;
        }
        .hero .kicker {
          color:#E8F0DC; font-size:.72rem; font-weight:900; letter-spacing:.14em;
          text-transform:uppercase;
        }
        .hero h1 { color:#FEFDFB !important; margin:.25rem 0 .35rem; }
        .hero p { color:#E8F0DC; margin:0; font-size:.9rem; }
        .mode-row { display:flex; gap:.45rem; flex-wrap:wrap; margin-top:.85rem; }
        .mode-badge {
          display:inline-flex; align-items:center; gap:.35rem; border-radius:999px;
          padding:.28rem .62rem; background:rgba(255,255,255,.15); color:#1B3D0C;
          border:1px solid rgba(45,80,22,.3); font-size:.7rem; font-weight:800;
        }
        .mode-badge.history { background:#E8F0DC; color:#2D5016; border-color:#A8C97D; }
        .retention-note {
          min-height:2.65rem; display:flex; align-items:center; padding:.65rem .8rem;
          border:1px solid #A8C97D; border-radius:.65rem; background:#E8F0DC;
          color:#1B3D0C; font-size:.78rem; font-weight:700;
        }
        .eyebrow {
          color:var(--primary); font-size:.7rem; font-weight:800;
          letter-spacing:.13em; text-transform:uppercase; margin-bottom:.35rem;
        }
        .subtle { color:var(--muted); font-size:.9rem; margin-top:-.7rem; }
        .metric-card {
          background:var(--surface); border:1px solid var(--line); border-radius:14px;
          padding:1.15rem 1.2rem; min-height:128px;
          box-shadow:0 8px 24px rgba(45,80,22,.07);
        }
        .metric-label { color:var(--muted); font-size:.76rem; font-weight:650; }
        .metric-value { font-size:1.8rem; font-weight:800; margin:.75rem 0 .3rem; color:#1B3D0C; }
        .metric-change {
          display:inline-block; color:var(--positive); background:#D9F0E8;
          border-radius:5px; padding:.12rem .35rem; font-size:.68rem; font-weight:800;
        }
        .metric-change.down { color:var(--negative); background:#F8DEDE; }
        .metric-change.bad-up { color:var(--negative); background:#F8DEDE; }
        .metric-change.good-down { color:var(--positive); background:#D9F0E8; }
        .metric-change.neutral { color:#3D5B2A; background:#E8EDE2; }
        .metric-foot { color:#6B8A59; font-size:.68rem; margin-left:.35rem; }
        .panel {
          background:var(--surface); border:1px solid var(--line); border-radius:14px;
          padding:1.2rem; box-shadow:0 10px 35px rgba(45,80,22,.05);
        }
        .briefing {
          background:linear-gradient(120deg,#4A7C2C,#2D5016 70%,#5A9436);
          border-radius:14px; padding:1.35rem 1.5rem; color:#FEFDFB; margin:.35rem 0 1rem;
        }
        .briefing .eyebrow { color:#D9E5CC; }
        .briefing h3 { color:#FEFDFB; margin:.15rem 0 .45rem; }
        .briefing p { color:#E8F0DC; line-height:1.65; }
        .briefing strong { color:#D9E5CC; }
        .mention-card {
          background:var(--surface); border:1px solid var(--line); border-radius:12px;
          padding:1rem 1.1rem; margin-bottom:.7rem;
        }
        .mention-top { display:flex; align-items:center; gap:.5rem; margin-bottom:.5rem; }
        .source-pill,.sentiment {
          border-radius:999px; padding:.2rem .5rem; font-size:.68rem; font-weight:800;
        }
        .source-pill { color:#1B3D0C; background:#E8F0DC; border:1px solid #A8C97D; }
        .sentiment.Positive { color:#2D8659; background:#D9F0E8; border:1px solid #A8C97D; }
        .sentiment.Negative { color:#8B3A3A; background:#F8DEDE; border:1px solid #D9BABA; }
        .sentiment.Neutral { color:#3D5B2A; background:#E8EDE2; border:1px solid #C4CDB8; }
        .mention-title { font-weight:800; font-size:.96rem; line-height:1.4; color:#1B3D0C; }
        .mention-summary { color:var(--muted); font-size:.8rem; line-height:1.5; margin:.4rem 0; }
        .mention-meta { color:#6B8A59; font-size:.7rem; }
        .stLinkButton a { 
          background:#4A7C2C !important; border:1px solid #6B9A47 !important; 
          color:#FEFDFB !important; padding:0.5rem 1rem !important; border-radius:0.375rem !important;
          text-decoration:none !important; font-weight:700 !important;
        }
        .stLinkButton a:hover {
          background:#5A9436 !important; border-color:#2D5016 !important;
        }
        .status-ok { color:#2D8659; font-weight:800; }
        .status-error { color:#D45B5B; font-weight:800; }
        [data-testid="stMetric"] {
          background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:1rem;
        }
        .stTabs [data-baseweb="tab-list"] { gap:.5rem; }
        .stTabs [data-baseweb="tab"] {
          background:#E8F0DC; border:1px solid #A8C97D; border-radius:9px;
          padding:.55rem 1rem; color:#2D5016;
        }
        .stTabs [aria-selected="true"] {
          background:#4A7C2C !important; color:#FEFDFB !important; border-color:#6B9A47;
        }
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        [data-testid="stNumberInput"] input {
          background:#FEFDFB !important; color:#1B3D0C !important;
          border-color:#A8C97D !important;
        }
        .stButton button, .stDownloadButton button, .stLinkButton a {
          background:#4A7C2C !important; border-color:#6B9A47 !important; color:#FEFDFB !important; font-weight:800 !important;
        }
        .stButton button:hover, .stDownloadButton button:hover, .stLinkButton a:hover {
          background:#5A9436 !important; border-color:#2D5016 !important; color:#FEFDFB !important;
        }
        [data-testid="stAlert"] { border:1px solid #A8C97D; }
        a { color:var(--primary) !important; }
        @media (max-width:700px) {
          .block-container { padding:4rem .8rem 1.5rem; }
          h1 { font-size:1.65rem !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def safe(value: object) -> str:
    return html.escape(str(value or ""))


def relative_time(value: datetime) -> str:
    seconds = max(0, int((datetime.now(timezone.utc) - value).total_seconds()))
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def topic_counts(rows: list[dict], brand: str) -> list[tuple[str, int]]:
    ignored = STOP_WORDS | {part.casefold() for part in re.findall(r"\w+", brand)}
    words: list[str] = []
    for row in rows:
        for word in re.findall(r"[A-Za-z][A-Za-z0-9'-]{3,}", row["title"]):
            normalized = word.casefold().strip("-'")
            if normalized not in ignored:
                words.append(normalized)
    return Counter(words).most_common(8)


def period_rows(rows: list[dict], start_days: int, end_days: int = 0) -> list[dict]:
    now = datetime.now(timezone.utc)
    oldest = now - timedelta(days=start_days)
    newest = now - timedelta(days=end_days)
    return [row for row in rows if oldest <= row["published_at"] < newest]


def percent_change(current: float, previous: float) -> tuple[str, str]:
    if previous == 0:
        if current == 0:
            return "no change", "neutral"
        return "new activity", "up"
    change = round((current - previous) / previous * 100)
    return f"{abs(change)}% vs prior 7d", "up" if change > 0 else "down" if change < 0 else "neutral"


def point_change(current: float, previous: float) -> tuple[str, str]:
    change = round(current - previous)
    return (
        f"{abs(change)} pts vs prior 7d",
        "up" if change > 0 else "down" if change < 0 else "neutral",
    )


def metric_card(
    label: str,
    value: str,
    change: str,
    foot: str,
    direction: str = "neutral",
) -> None:
    arrow = (
        "↗"
        if direction in {"up", "bad-up"}
        else "↘"
        if direction in {"down", "good-down"}
        else "•"
    )
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{safe(label)}</div>
          <div class="metric-value">{safe(value)}</div>
          <span class="metric-change {safe(direction)}">{arrow} {safe(change)}</span>
          <span class="metric-foot">{safe(foot)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_mention(row: dict) -> None:
    summary = row.get("summary") or "No summary supplied by this source."
    confidence = row.get("sentiment_confidence", "Low")
    reason = row.get("sentiment_reason", "Automated text classification")
    st.markdown(
        f"""
        <div class="mention-card">
          <div class="mention-top">
            <span class="source-pill">{SOURCE_ICONS.get(row["source"], "•")} {safe(row["source"])}</span>
            <span class="sentiment {safe(row["sentiment"])}">{safe(row["sentiment"])}</span>
          </div>
          <div class="mention-title">{safe(row["title"])}</div>
          <div class="mention-summary">{safe(summary[:300])}</div>
          <div class="mention-meta">
            {safe(row.get("author", "Unknown"))} · {safe(relative_time(row["published_at"]))} ·
            {safe(confidence)} confidence · {safe(reason)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button(
        "Open source ↗",
        row["link"],
        width="content",
    )


def render_overview(rows: list[dict], target: str, competitor: str | None) -> None:
    target_rows = [row for row in rows if row["brand"] == target]
    competitor_rows = [row for row in rows if competitor and row["brand"] == competitor]
    positive = sum(row["sentiment"] == "Positive" for row in target_rows)
    negative = sum(row["sentiment"] == "Negative" for row in target_rows)
    positive_pct = round(positive / len(target_rows) * 100) if target_rows else 0
    share = round(len(target_rows) / len(rows) * 100) if rows else 0
    current_target = period_rows(target_rows, 7)
    previous_target = period_rows(target_rows, 14, 7)
    current_all = period_rows(rows, 7)
    previous_all = period_rows(rows, 14, 7)
    current_positive = (
        sum(row["sentiment"] == "Positive" for row in current_target)
        / len(current_target)
        * 100
        if current_target
        else 0
    )
    previous_positive = (
        sum(row["sentiment"] == "Positive" for row in previous_target)
        / len(previous_target)
        * 100
        if previous_target
        else 0
    )
    current_share = len(current_target) / len(current_all) * 100 if current_all else 0
    previous_share = (
        len(previous_target) / len(previous_all) * 100 if previous_all else 0
    )
    current_negative = sum(row["sentiment"] == "Negative" for row in current_target)
    previous_negative = sum(row["sentiment"] == "Negative" for row in previous_target)

    volume_change, volume_direction = percent_change(
        len(current_target), len(previous_target)
    )
    sentiment_change, sentiment_direction = point_change(
        current_positive, previous_positive
    )
    share_change, share_direction = point_change(current_share, previous_share)
    risk_change, risk_direction = percent_change(current_negative, previous_negative)
    risk_direction = (
        "bad-up"
        if risk_direction == "up"
        else "good-down"
        if risk_direction == "down"
        else "neutral"
    )

    metric_cols = st.columns(4)
    with metric_cols[0]:
        metric_card(
            "Total mentions",
            f"{len(target_rows):,}",
            volume_change,
            "7-day movement",
            volume_direction,
        )
    with metric_cols[1]:
        metric_card(
            "Positive sentiment",
            f"{positive_pct}%",
            sentiment_change,
            f"{positive} positive mentions",
            sentiment_direction,
        )
    with metric_cols[2]:
        metric_card(
            "Share of voice",
            f"{share}%",
            share_change,
            f"{len(target_rows)} of {len(rows)} mentions",
            share_direction,
        )
    with metric_cols[3]:
        metric_card(
            "Negative alerts",
            f"{current_negative}",
            risk_change,
            "Sentiment risk",
            risk_direction,
        )

    attention_col, topic_col = st.columns([2, 1])
    with attention_col:
        st.markdown(
            f'<div class="eyebrow">{safe("Latest activity")}</div>',
            unsafe_allow_html=True,
        )
        st.subheader("Mentions requiring attention")
        priority = sorted(
            target_rows,
            key=lambda row: (
                row["sentiment"] != "Negative",
                -abs(row["sentiment_score"]),
                -row["published_at"].timestamp(),
            ),
        )[:4]
        if priority:
            for row in priority:
                render_mention(row)
        else:
            st.info("No mentions match the current filters.")

    with topic_col:
        st.markdown(
            f'<div class="eyebrow">{safe("Conversation drivers")}</div>',
            unsafe_allow_html=True,
        )
        st.subheader("Trending terms")
        topics = topic_counts(target_rows, target)
        if topics:
            topic_frame = pd.DataFrame(topics, columns=["topic", "mentions"])
            bars = (
                alt.Chart(topic_frame)
                .mark_bar(color="#1e4620", cornerRadiusEnd=4)
                .encode(
                    x=alt.X("mentions:Q", title=None),
                    y=alt.Y("topic:N", sort="-x", title=None),
                    tooltip=["topic:N", "mentions:Q"],
                )
                .properties(height=300)
            )
            st.altair_chart(bars, use_container_width=True)
        else:
            st.info("Not enough text to identify topics.")


def render_mentions(rows: list[dict]) -> None:
    st.markdown(
        f'<div class="eyebrow">{safe("Unified inbox")}</div>',
        unsafe_allow_html=True,
    )
    st.header("Live mentions")
    st.caption(f"{len(rows)} results · newest first · open a source to verify context")
    if not rows:
        st.warning("No mentions match the current filters.")
        return

    page_size = 12
    pages = max(1, (len(rows) + page_size - 1) // page_size)
    page = st.number_input(
        "Page",
        min_value=1,
        max_value=pages,
        value=1,
    )
    start = (page - 1) * page_size
    for row in rows[start : start + page_size]:
        render_mention(row)


def render_analytics(rows: list[dict], target: str) -> None:
    st.markdown(
        f'<div class="eyebrow">{safe("Deeper analysis")}</div>',
        unsafe_allow_html=True,
    )
    st.header("Analytics")
    target_rows = [row for row in rows if row["brand"] == target]
    if not target_rows:
        st.warning("No data is available for this view.")
        return

    frame = pd.DataFrame(target_rows)
    source_counts = frame.groupby("source").size().reset_index(name="mentions")
    source_chart = (
        alt.Chart(source_counts)
        .mark_bar(color="#1e4620", cornerRadiusEnd=5)
        .encode(
            x=alt.X("mentions:Q", title="Mentions"),
            y=alt.Y("source:N", sort="-x", title=None),
            tooltip=["source:N", "mentions:Q"],
        )
        .properties(height=280)
    )
    sentiment_counts = (
        frame.groupby(["source", "sentiment"]).size().reset_index(name="mentions")
    )
    sentiment_chart = (
        alt.Chart(sentiment_counts)
        .mark_bar()
        .encode(
            x=alt.X("mentions:Q", stack="normalize", title="Share"),
            y=alt.Y("source:N", title=None),
            color=alt.Color(
                "sentiment:N",
                scale=alt.Scale(
                    domain=["Positive", "Neutral", "Negative"],
                    range=["#198754", "#c9d0ce", "#d55050"],
                ),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=["source:N", "sentiment:N", "mentions:Q"],
        )
        .properties(height=280)
    )

    first, second = st.columns(2)
    with first:
        st.subheader("Mentions by source")
        st.altair_chart(source_chart, use_container_width=True)
    with second:
        st.subheader("Sentiment by source")
        st.altair_chart(sentiment_chart, use_container_width=True)

    st.info(
        "Sentiment is based on explicit product praise, value/deal language, "
        "complaints, failures, solution phrases, and negation. Unclear or mixed "
        "language is classified as neutral. Confidence and the strongest reason "
        "are shown on each mention.",
        icon=":material/info:",
    )


def render_source_health(statuses: list[dict]) -> None:
    st.markdown(
        f'<div class="eyebrow">{safe("Collection diagnostics")}</div>',
        unsafe_allow_html=True,
    )
    st.header("Source health")
    st.caption("Failures are shown explicitly; Petlibro never silently drops a source.")
    if not statuses:
        st.info("No source checks have run.")
        return
    frame = pd.DataFrame(statuses)
    frame["Status"] = frame["ok"].map({True: "Connected", False: "Unavailable"})
    st.dataframe(
        frame[["brand", "source", "Status", "count", "message"]].rename(
            columns={
                "brand": "Brand",
                "source": "Source",
                "count": "Mentions",
                "message": "Details",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


inject_styles()

if "brands" not in st.session_state:
    st.session_state.brands = DEFAULT_BRANDS.copy()

with st.sidebar:
    st.markdown("## 🐾 Petlibro")
    st.caption("Pet tech market intelligence")

    target_brand = st.selectbox(
        "Primary brand",
        st.session_state.brands,
    )
    competitor_options = ["None"] + [
        brand for brand in st.session_state.brands if brand != target_brand
    ]
    competitor_choice = st.selectbox(
        "Compare with",
        competitor_options,
    )
    competitor_brand = None if competitor_choice == "None" else competitor_choice

    st.divider()
    new_brand = st.text_input(
        "Add a tracked brand",
        placeholder="e.g. Whistle",
    )
    if st.button("Add brand", width="stretch"):
        cleaned = new_brand.strip()
        if cleaned and cleaned.casefold() not in {
            brand.casefold() for brand in st.session_state.brands
        }:
            st.session_state.brands.append(cleaned)
            st.rerun()

    st.divider()
    selected_sources = st.multiselect(
        "Sources",
        SOURCES,
        default=SOURCES,
    )
    publication_feed_urls = st.text_area(
        "Additional publication feeds",
        placeholder="Add one RSS feed URL per line",
        help="Enter custom RSS feeds to extend publication coverage.",
        height=120,
    )
    custom_feed_urls = [
        line.strip() for line in publication_feed_urls.splitlines() if line.strip()
    ]
    if custom_feed_urls and "Publication feeds" not in selected_sources:
        selected_sources.append("Publication feeds")

    date_window = st.select_slider(
        "Date range",
        options=[1, 3, 7, 14, 30],
        value=30,
        format_func=lambda days: f"Last {days} days",
    )
    selected_sentiments = st.multiselect(
        "Sentiment",
        ["Positive", "Neutral", "Negative"],
        default=["Positive", "Neutral", "Negative"],
    )
    query = st.text_input(
        "Search",
        placeholder="Headline, author, publisher",
    )

    st.divider()
    force_refresh = st.button(
        "↻ Refresh live data",
        width="stretch",
    )
    if force_refresh:
        st.cache_data.clear()
        st.rerun()
    if not secret("YOUTUBE_API_KEY"):
        st.caption(
            "YouTube is paused until `YOUTUBE_API_KEY` is added to Streamlit Secrets."
        )

brands_to_fetch = [target_brand] + ([competitor_brand] if competitor_brand else [])
with st.spinner("Collecting live mentions…"):
    live_mentions, source_statuses = load_mentions(
        tuple(brands_to_fetch),
        tuple(selected_sources),
        secret("YOUTUBE_API_KEY"),
        2,
        tuple(custom_feed_urls),
    )

archived_mentions = load_archive(tuple(brands_to_fetch), 1)
session_rows = st.session_state.get("session_archive", [])
mentions = deduplicate(archived_mentions + session_rows + live_mentions)
st.session_state.session_archive = mentions
archive_message = (
    f"{len(archived_mentions)} retained mentions loaded"
    if archived_mentions
    else "Archive enabled; history begins with the next scheduled collection"
)

source_statuses.append(
    {
        "brand": "Workspace",
        "source": "30-day archive",
        "count": len(mentions),
        "ok": True,
        "message": archive_message,
    }
)

cutoff = datetime.now(timezone.utc) - timedelta(days=date_window)
filtered = [
    row
    for row in mentions
    if row["published_at"] >= cutoff
    and row["source"] in selected_sources
    and row["sentiment"] in selected_sentiments
    and (
        not query
        or query.casefold()
        in f"{row['title']} {row.get('summary','')} {row.get('author','')} {row.get('publisher','') }".casefold()
    )
]

latest_collection = max(
    (
        row.get("collected_at", row.get("published_at", datetime.now(timezone.utc)))
        for row in live_mentions
    ),
    default=datetime.now(timezone.utc),
)

history_badge = '<span class="mode-badge history">● 30-day history enabled</span>'
youtube_badge = (
    '<span class="mode-badge">YouTube connected</span>'
    if secret("YOUTUBE_API_KEY")
    else '<span class="mode-badge">YouTube pending</span>'
)
st.markdown(
    f"""
    <section class="hero">
      <div class="kicker">live brand intelligence</div>
      <h1>{safe(target_brand)} intelligence</h1>
      <p>What changed, why it matters, and which public sources support it.</p>
      <div class="mode-row">
        {history_badge}
        {youtube_badge}
        <span class="mode-badge">Updated {safe(relative_time(latest_collection))}</span>
        <span class="mode-badge">{len(filtered)} visible mentions</span>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

csv_frame = pd.DataFrame(filtered)
if not csv_frame.empty:
    csv_frame["published_at"] = csv_frame["published_at"].astype(str)

download_col, freshness_col = st.columns([0.28, 0.72])
with download_col:
    st.download_button(
        "Download CSV",
        csv_frame.to_csv(index=False).encode("utf-8"),
        file_name=f"{target_brand.casefold().replace(' ', '-')}-mentions.csv",
        mime="text/csv",
        width="stretch",
    )
with freshness_col:
    retention_text = (
        f"30-day history active · {len(archived_mentions)} archived mentions · new data is collected automatically every 15 minutes"
        if archived_mentions
        else "30-day history is enabled and will build automatically every 15 minutes"
    )
    st.markdown(
        f'<div class="retention-note">✓ {safe(retention_text)}</div>',
        unsafe_allow_html=True,
    )

overview_tab, mentions_tab, analytics_tab, health_tab = st.tabs(
    [
        "Overview",
        "Mentions",
        "Analytics",
        "Source health",
    ]
)
with overview_tab:
    render_overview(filtered, target_brand, competitor_brand)
with mentions_tab:
    render_mentions(filtered)
with analytics_tab:
    render_analytics(filtered, target_brand)
with health_tab:
    render_source_health(source_statuses)

st.caption(
    "Sentiment is automated and should be reviewed in context. "
    "Feed availability and indexing vary by source."
)