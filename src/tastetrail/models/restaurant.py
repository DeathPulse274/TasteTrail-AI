"""Restaurant catalog model."""

from pydantic import BaseModel, Field

from tastetrail.models.preferences import BudgetBand


class Restaurant(BaseModel):
    """Normalized restaurant record from the dataset store."""

    id: str
    name: str
    location: str
    cuisines: list[str] = Field(default_factory=list)
    budget_band: BudgetBand
    rating: float | None = None
    estimated_cost: str = ""
    raw_cost: str | None = None
