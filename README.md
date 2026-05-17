# TasteTrail-AI

AI-powered restaurant recommendations inspired by Zomato. Combines structured restaurant data with an LLM to rank options and explain why each fits your preferences.

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/problemStatement.md](docs/problemStatement.md) | Problem and goals |
| [docs/architecture.md](docs/architecture.md) | System design |
| [docs/implementationPlan.md](docs/implementationPlan.md) | Phase-wise build plan |
| [docs/eval/phase0-eval.md](docs/eval/phase0-eval.md) | Phase 0 evaluation criteria |

## Requirements

- Python 3.11+
- (Phase 2+) [Groq](https://console.groq.com/keys) API key (`LLM_API_KEY`)

## Setup

```bash
# Clone and enter the project
cd TasteTrail-AI

# Create a virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate (macOS/Linux)
# source .venv/bin/activate

# Install dependencies (editable package + pytest)
pip install -r requirements.txt

# Configure environment
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
# Edit .env and set LLM_API_KEY (Groq) for AI-powered explanations
```

## Verify installation (Phase 0)

```bash
python -c "import tastetrail; print(tastetrail.__version__)"
pytest tests/ -q
```

## Ingest restaurant data (Phase 1)

Downloads the Zomato dataset from Hugging Face (~50k rows, first run may take a few minutes):

```bash
python scripts/ingest_data.py
```

Output: `data/processed/restaurants.parquet` (gitignored). See [docs/datasetSchema.md](docs/datasetSchema.md) for column mapping and budget rules.

```bash
python -c "from tastetrail.store import RestaurantStore; s=RestaurantStore.load(); print(len(s), 'restaurants'); print(s.distinct_locations()[:5])"
```

## Get recommendations (Phase 2)

Set your Groq `LLM_API_KEY` in `.env` for AI explanations (otherwise results use rating-based fallback):

```bash
tastetrail --location Bangalore --budget medium --cuisine chinese --min-rating 4.0
# or
python -m tastetrail.cli --location Bangalore --budget medium --top-n 3
```

## Web UI (Phase 3)

```bash
streamlit run app/main.py
```

Use the form to set city, budget, cuisine, and rating — results show name, cuisine, rating, cost, and AI explanation.

### REST API (optional)

```bash
uvicorn tastetrail.api.main:app --reload
```

- `GET /health` — liveness and dataset info  
- `POST /recommendations` — JSON body matching `UserPreferences`  
- `GET /docs` — interactive OpenAPI UI  

## Project layout

```
src/tastetrail/     Core package (models, config; pipeline in later phases)
app/                Streamlit UI (Phase 3)
scripts/            Data ingestion CLI (Phase 1)
data/processed/     Generated restaurant parquet (not committed)
tests/              Pytest suite
docs/               Design and evaluation docs
```

## Roadmap

| Phase | Status | Command / notes |
|-------|--------|-----------------|
| 0 | Done | Foundation, models, config |
| 1 | Done | `python scripts/ingest_data.py` → `data/processed/restaurants.parquet` |
| 2 | Done | `tastetrail` CLI / `Recommender.recommend()` |
| 3 | Done | `streamlit run app/main.py` · optional FastAPI |

## License

See repository license (add as needed).
