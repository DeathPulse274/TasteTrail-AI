"""TasteTrail-AI — Streamlit UI (Phase 3)."""

from __future__ import annotations

import streamlit as st
from pydantic import ValidationError

from tastetrail.models import BudgetBand, UserPreferences
from tastetrail.orchestration.recommender import Recommender
from tastetrail.store import RestaurantStore

BUDGET_OPTIONS = {
    "low": "Low (under ₹300 for two)",
    "medium": "Medium (₹300–₹700 for two)",
    "high": "High (over ₹700 for two)",
}


@st.cache_resource(show_spinner="Loading restaurant data…")
def _load_store() -> RestaurantStore:
    return RestaurantStore.load()


def _render_header() -> None:
    st.set_page_config(
        page_title="TasteTrail-AI",
        page_icon="🍽️",
        layout="wide",
    )
    st.title("TasteTrail-AI")
    st.caption(
        "Personalized restaurant picks powered by your preferences and Groq AI — "
        "grounded in real Zomato-style data."
    )


def _render_results(result) -> None:
    if result.metadata.used_fallback:
        st.info(
            "Showing rating-based picks (Groq AI was unavailable or returned no valid results). "
            "Check your `LLM_API_KEY` in `.env` for full AI explanations."
        )

    if result.summary:
        st.subheader("Overview")
        st.markdown(result.summary)

    if not result.recommendations:
        st.warning(result.metadata.message or "No restaurants matched your filters.")
        st.markdown(
            "**Try:** lowering minimum rating, removing cuisine, or choosing another budget band."
        )
        return

    st.subheader(f"Top {len(result.recommendations)} recommendations")
    for rec in result.recommendations:
        restaurant = rec.restaurant
        if restaurant is None:
            continue
        cuisine_display = ", ".join(c.title() for c in restaurant.cuisines) or "—"
        rating_display = f"{restaurant.rating:.1f}" if restaurant.rating is not None else "Not rated"
        with st.container(border=True):
            st.markdown(f"### #{rec.rank} · {restaurant.name}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Rating", rating_display)
            col2.metric("Budget", restaurant.budget_band.value.title())
            col3.metric("Cost", restaurant.estimated_cost or "—")
            st.markdown(f"**Cuisine:** {cuisine_display}")
            st.markdown(f"**Location:** {restaurant.location}")
            st.markdown(f"**Why this pick:** {rec.explanation}")

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

    locations = store.distinct_locations()
    cuisines = ["— Any —", *store.distinct_cuisines()[:150]]

    with st.form("preferences_form", clear_on_submit=False):
        st.subheader("Your preferences")
        c1, c2 = st.columns(2)
        with c1:
            location = st.selectbox(
                "Area *", 
                options=locations, 
                index=0 if locations else None,
                format_func=lambda x: x.split(",")[0].strip() if x else x
            )
            budget_label = st.selectbox(
                "Budget *",
                options=list(BUDGET_OPTIONS.keys()),
                format_func=lambda k: BUDGET_OPTIONS[k],
            )
            cuisine_choice = st.selectbox("Cuisine (optional)", options=cuisines)
        with c2:
            min_rating = st.slider("Minimum rating", min_value=0.0, max_value=5.0, value=3.0, step=0.5)
            top_n = st.number_input("Number of results", min_value=1, max_value=10, value=5)
            additional = st.text_area(
                "Additional preferences (optional)",
                placeholder="e.g. family-friendly, quick service, outdoor seating",
                height=68,
            )

        submitted = st.form_submit_button("Get recommendations", type="primary", use_container_width=True)

    if not submitted:
        st.info("Set your preferences above and click **Get recommendations** to start.")
        return

    if not location:
        st.error("Please select a city.")
        return

    cuisine = None if cuisine_choice == "— Any —" else cuisine_choice
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
