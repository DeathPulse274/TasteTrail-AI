"""TasteTrail-AI — Streamlit UI (Phase 3)."""

from __future__ import annotations

import streamlit as st
from pydantic import ValidationError
import os
import urllib.request
from pathlib import Path

from tastetrail.models import BudgetBand, UserPreferences
from tastetrail.orchestration.recommender import Recommender
from tastetrail.store import RestaurantStore
from tastetrail.config import get_settings

BUDGET_OPTIONS = {
    "low": "Low (under ₹300 for two)",
    "medium": "Medium (₹300–₹700 for two)",
    "high": "High (over ₹700 for two)",
}


@st.cache_resource(show_spinner="Loading restaurant data…")
def _load_store() -> RestaurantStore:
    settings = get_settings()
    try:
        return RestaurantStore.load(settings=settings)
    except FileNotFoundError as exc:
        # If DATA_URL is provided, attempt to download the processed dataset automatically.
        data_url = os.environ.get("DATA_URL")
        if not data_url:
            raise

        dest: Path = settings.data_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            with st.spinner("Downloading dataset from DATA_URL…"):
                urllib.request.urlretrieve(data_url, str(dest))
            return RestaurantStore.load(settings=settings)
        except Exception as download_exc:
            raise FileNotFoundError(
                f"{exc}\nAttempted to download DATA_URL but failed: {download_exc}"
            )


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
            body {
                background: linear-gradient(180deg, #02040a 0%, #06101d 100%);
            }
            .stApp {
                color: #e2e8f0;
            }
            .hero-card,
            .filter-card,
            .results-card,
            .recommendation-card {
                background: rgba(15, 23, 42, 0.82);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 32px;
                box-shadow: 0 36px 80px rgba(0, 0, 0, 0.25);
                backdrop-filter: blur(20px);
            }
            .hero-card {
                padding: 2rem 2.5rem;
                margin-bottom: 2rem;
            }
            .hero-title {
                font-size: clamp(2.8rem, 5vw, 4.8rem);
                font-weight: 800;
                margin: 0;
                line-height: 1.1;
            }
            .hero-subtitle {
                color: #cbd5e1;
                font-size: 1.05rem;
                margin-top: 1rem;
                max-width: 64rem;
            }
            .stSelectbox, .stSlider, .stNumberInput, .stTextArea {
                border-radius: 18px;
            }
            .stButton>button {
                border-radius: 18px;
                padding: 0.95rem 1.5rem;
                font-weight: 700;
            }
            .stButton>button:hover {
                transform: translateY(-1px);
            }
            .section-title {
                display: inline-flex;
                align-items: center;
                gap: 0.75rem;
                margin-bottom: 1rem;
                font-size: 0.95rem;
                letter-spacing: 0.18em;
                text-transform: uppercase;
                color: #7dd3fc;
            }
            .no-results {
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 24px;
                padding: 1.75rem;
                background: rgba(15, 23, 42, 0.9);
            }
            .card-grid {
                display: grid;
                gap: 1.5rem;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            }
            .recommendation-card {
                padding: 1.5rem;
                transition: transform 0.25s ease, background 0.25s ease, border-color 0.25s ease;
                position: relative;
            }
            .recommendation-card:hover {
                transform: translateY(-6px);
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(125, 211, 252, 0.25);
            }
            .recommendation-card h3 {
                margin: 0 0 0.75rem 0;
                font-size: 1.25rem;
            }
            .recommendation-card .tag-row {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                margin: 0.75rem 0 1rem;
            }
            .recommendation-card .tag {
                background: rgba(125, 211, 252, 0.1);
                color: #cfe9ff;
                font-size: 0.72rem;
                padding: 0.35rem 0.75rem;
                border-radius: 999px;
                border: 1px solid rgba(125, 211, 252, 0.18);
            }
            .recommendation-card .details {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.75rem;
                margin-bottom: 1rem;
            }
            .recommendation-card .detail-pill {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 16px;
                padding: 0.75rem 0.9rem;
                font-size: 0.875rem;
                color: #e2e8f0;
            }
            .recommendation-card .explanation-container {
                position: relative;
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 20px;
                padding: 1rem;
                overflow: hidden;
            }
            .recommendation-card .explanation-label {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                margin-bottom: 0.75rem;
                font-size: 0.75rem;
                letter-spacing: 0.18em;
                text-transform: uppercase;
                color: #94a3b8;
            }
            .recommendation-card .explanation-preview {
                margin: 0;
                color: #cbd5e1;
                line-height: 1.7;
                font-style: italic;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .recommendation-card .explanation-overlay {
                position: absolute;
                inset: 0;
                background: rgba(3, 7, 18, 0.98);
                color: #e2e8f0;
                opacity: 0;
                pointer-events: none;
                transition: opacity 0.2s ease;
                padding: 1.25rem;
                overflow: auto;
            }
            .recommendation-card:hover .explanation-overlay,
            .recommendation-card .explanation-container:hover .explanation-overlay {
                opacity: 1;
                pointer-events: auto;
            }
            .recommendation-card .explanation-overlay .overlay-title {
                margin-bottom: 0.75rem;
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 0.16em;
                color: #94a3b8;
            }
            .recommendation-card .explanation-overlay .overlay-text {
                white-space: pre-wrap;
                line-height: 1.7;
                color: #e2e8f0;
            }
            .recommendation-card p {
                margin: 0.5rem 0 0 0;
                color: #cbd5e1;
                line-height: 1.7;
            }
            .filter-card {
                padding: 1.75rem;
                margin-bottom: 2rem;
            }
            .filter-grid {
                display: grid;
                grid-template-columns: 1.3fr 1fr;
                gap: 1.5rem;
            }
            .field-group {
                display: grid;
                gap: 1rem;
            }
            .field-label {
                font-size: 0.78rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                color: #94a3b8;
                margin-bottom: 0.35rem;
            }
            .large-button .stButton>button {
                width: 100%;
                padding: 1rem 1.5rem;
            }
            @media(max-width: 950px) {
                .filter-grid {
                    grid-template-columns: 1fr;
                }
                .recommendation-card .details {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header() -> None:
    st.set_page_config(
        page_title="TasteTrail-AI",
        page_icon="🍽️",
        layout="wide",
    )
    _inject_styles()
    st.markdown(
        """
        <div class="hero-card">
            <div class="section-title">AI dining concierge</div>
            <h1 class="hero-title">TasteTrail AI</h1>
            <p class="hero-subtitle">A smarter restaurant recommendation experience with natural preference inputs, budget awareness, and explanation-backed picks.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_results(result) -> None:
    if result.metadata.used_fallback:
        st.info(
            "Showing rating-based picks (Groq AI was unavailable or returned no valid results). "
            "Check your `LLM_API_KEY` in `.env` for full AI explanations."
        )

    if result.summary:
        st.markdown('<div class="results-card">', unsafe_allow_html=True)
        st.subheader("Overview")
        st.markdown(result.summary)
        st.markdown('</div>', unsafe_allow_html=True)

    if not result.recommendations:
        st.markdown(
            '<div class="no-results"><strong>No recommendations found.</strong><br/>Try lowering rating, selecting a different budget, or removing cuisine filters.</div>',
            unsafe_allow_html=True,
        )
        return

    st.subheader(f"Top {len(result.recommendations)} recommendations")
    st.markdown('<div class="results-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-grid">', unsafe_allow_html=True)
    for rec in result.recommendations:
        restaurant = rec.restaurant
        if restaurant is None:
            continue
        cuisine_display = ", ".join(c.title() for c in restaurant.cuisines) or "—"
        rating_display = f"{restaurant.rating:.1f}" if restaurant.rating is not None else "Not rated"
        st.markdown(
            f"""
            <div class="recommendation-card">
                <div style='display:flex; justify-content:space-between; align-items:center; gap:1rem; margin-bottom:0.75rem;'>
                    <div>
                        <div style='font-size:0.75rem; letter-spacing:0.18em; text-transform:uppercase; color:#7dd3fc; margin-bottom:0.35rem;'>Rank #{rec.rank}</div>
                        <div style='font-size:1.35rem; font-weight:800; color:#f8fafc; line-height:1.1;'>{restaurant.name}</div>
                    </div>
                    <div style='font-size:0.95rem; color:#94a3b8;'>{rating_display} ★</div>
                </div>
                <div class='tag-row'>
                    <span class='tag'>{restaurant.budget_band.value.title()}</span>
                    <span class='tag'>{restaurant.location}</span>
                </div>
                <div class='details'>
                    <div class='detail-pill'>Cuisine: {cuisine_display}</div>
                    <div class='detail-pill'>Cost: {restaurant.estimated_cost or '—'}</div>
                    <div class='detail-pill'>Match score: {max(70, min(100, 100 - (rec.rank - 1) * 6))}%</div>
                </div>
                <div class='explanation-container'>
                    <div class='explanation-label'>Why AI Picked It</div>
                    <p class='explanation-preview'>"{rec.explanation}"</p>
                    <div class='explanation-overlay'>
                        <div class='overlay-title'>Full explanation</div>
                        <div class='overlay-text'>"{rec.explanation}"</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if result.metadata.latency_ms is not None:
        st.caption(
            f"Found {result.metadata.candidate_count} candidates · "
            f"Responded in {result.metadata.latency_ms:.0f} ms"
        )


def main() -> None:
    _render_header()

    try:
        store = _load_store()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.code("python scripts/ingest_data.py", language="bash")
        st.stop()

    locations = [
        loc for loc in store.distinct_locations()
        if loc and loc.strip().lower() != "nan"
    ]
    cuisines = ["All cuisines", *store.distinct_cuisines()[:150]]

    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    with st.form("preferences_form", clear_on_submit=False):
        st.markdown("""
            <div class="section-title">Your preferences</div>
            <h2 style='margin:0;font-size:1.9rem;'>Tell us what you feel like eating</h2>
            <p style='color:#94a3b8;margin-top:0.5rem;'>Pick your area, budget, and cuisine to get restaurant suggestions tailored to your taste.</p>
        """, unsafe_allow_html=True)

        st.markdown('<div class="filter-grid">', unsafe_allow_html=True)
        left, right = st.columns([1.2, 1])
        with left:
            location = st.selectbox(
                "Area *",
                options=locations,
                index=0 if locations else None,
                format_func=lambda x: x.split(",")[0].strip() if x else x,
            )
            cuisine_choice = st.selectbox("Cuisine", options=cuisines)
            additional = st.text_area(
                "Additional preferences",
                placeholder="e.g. family-friendly, quick service, outdoor seating",
                height=110,
            )
        with right:
            budget_label = st.radio(
                "Budget",
                options=list(BUDGET_OPTIONS.keys()),
                index=1,
                format_func=lambda k: BUDGET_OPTIONS[k],
                horizontal=True,
            )
            min_rating = st.slider(
                "Minimum rating",
                min_value=1.0,
                max_value=5.0,
                value=3.0,
                step=0.5,
            )
            top_n = st.number_input("Number of results", min_value=1, max_value=10, value=5)

        submitted = st.form_submit_button("Get recommendations", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if not submitted:
        st.info("Use the form above to generate restaurant recommendations.")
        return

    if not location:
        st.error("Please select a city.")
        return

    cuisine = None if cuisine_choice == "All cuisines" else cuisine_choice
    try:
        preferences = UserPreferences(
            location=location,
            budget=BudgetBand(budget_label),
            cuisine=cuisine,
            min_rating=min_rating if min_rating > 0 else None,
            additional_preferences=additional.strip() or None,
            top_n=int(top_n),
        )
    except ValidationError as err:
        st.error("Invalid preferences. Please check your inputs.")
        st.json(err.errors())
        return

    recommender = Recommender(store)
    with st.spinner("TasteTrail is finding the best restaurants for you…"):
        result = recommender.recommend(preferences)

    _render_results(result)


if __name__ == "__main__":
    main()
