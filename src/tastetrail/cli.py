"""CLI for TasteTrail-AI recommendations."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from tastetrail.models import BudgetBand, UserPreferences
from tastetrail.orchestration.recommender import Recommender
from tastetrail.store import RestaurantStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Get AI restaurant recommendations")
    parser.add_argument("--location", required=True, help="City, e.g. Bangalore")
    parser.add_argument(
        "--budget",
        required=True,
        choices=[b.value for b in BudgetBand],
        help="Budget band: low, medium, high",
    )
    parser.add_argument("--cuisine", default=None, help="Preferred cuisine")
    parser.add_argument("--min-rating", type=float, default=None, dest="min_rating")
    parser.add_argument("--additional", default=None, help="Extra preferences")
    parser.add_argument("--top-n", type=int, default=None, dest="top_n")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(message)s",
    )

    try:
        store = RestaurantStore.load()
        preferences = UserPreferences(
            location=args.location,
            budget=BudgetBand(args.budget),
            cuisine=args.cuisine,
            min_rating=args.min_rating,
            additional_preferences=args.additional,
            top_n=args.top_n,
        )
        result = Recommender(store).recommend(preferences)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    output = {
        "summary": result.summary,
        "recommendations": [
            {
                "rank": rec.rank,
                "name": rec.restaurant.name if rec.restaurant else None,
                "cuisine": rec.restaurant.cuisines if rec.restaurant else [],
                "rating": rec.restaurant.rating if rec.restaurant else None,
                "estimated_cost": rec.restaurant.estimated_cost if rec.restaurant else None,
                "explanation": rec.explanation,
            }
            for rec in result.recommendations
        ],
        "metadata": result.metadata.model_dump(),
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
