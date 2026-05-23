# Deployment Plan — Streamlit

This document describes how to deploy the TasteTrail-AI project using Streamlit (Streamlit Community Cloud) as the primary hosting environment for the user-facing app (`app/main.py`). It also includes notes about data, secrets, and alternatives (Docker / containerized deployment) when Streamlit Cloud is not appropriate.

## Summary

- Primary (recommended): deploy the Streamlit UI at `app/main.py` to Streamlit Cloud. The Streamlit app loads the `RestaurantStore` from `data/processed/` and runs the recommendation flows server-side, so you do not need to separately run the FastAPI backend for the demo UI.
- If you need the React frontend or the FastAPI API publicly available, deploy them separately (Vercel/Netlify for frontend, Render/Heroku/Cloud Run for backend) or use Docker Compose to host all services.

## Prerequisites

- A GitHub repository containing this project (push changes to a public or private repo accessible to Streamlit Cloud).
- Ensure `requirements.txt` (root) contains all Python dependencies. Streamlit Cloud installs packages from `requirements.txt` by default.
- Python version: use a stable Streamlit-supported version (recommend `3.11` or `3.10`). Update `pyproject.toml`/`requirements.txt` accordingly if you pin a different Python minor version.
- Processed dataset: `data/processed/` must contain the files expected by `RestaurantStore.load()`. Either commit the processed files to the repo (small datasets) or host them externally (S3, GitHub Release) and update the app code to download at startup.

## Required environment variables / secrets

Set the following secrets in Streamlit Cloud (App settings → Secrets):

- `LLM_API_KEY` — API key for the configured large language model provider (if using LLM features).
- Any provider-specific variables used by `src/tastetrail/llm/providers/*` (for example `GROQ_API_KEY`, `OPENAI_API_KEY`, etc.).
- `DATA_URL` (optional) — if the processed dataset lives externally, set a URL so the app can download it on first run.

Note: The project uses `python-dotenv` locally; in the cloud use Streamlit's secret management instead of committing `.env`.

## Steps — Streamlit Cloud deployment

1. Verify local run and data

   - Create a clean virtual environment and install deps:

   ```bash
   python -m venv .venv
   .venv\\Scripts\\activate    # Windows
   source .venv/bin/activate   # macOS/Linux
   pip install -r requirements.txt
   ```

   - Prepare the processed dataset (if not committed):

   ```bash
   python scripts/ingest_data.py
   ```

   - Run the Streamlit app locally to verify everything works:

   ```bash
   streamlit run app/main.py
   ```

   - Confirm the app loads and recommendations work (use small sample data first).

2. Push the repository to GitHub

   - Commit and push all relevant files, including the `app/` folder and either the processed dataset or an automated download flow.

3. Create a Streamlit app (Streamlit Cloud)

   - Go to https://share.streamlit.io and sign in with your GitHub account.
   - Click **New app** → select the repository and branch, set the main file path to `app/main.py` and the Python version (set to `3.11` recommended).
   - Add Secrets in the App settings (see above).

4. Large data considerations

   - If `data/processed/` is large, do NOT commit it; instead host it (S3, Azure Blob, GitHub Release) and set `DATA_URL` in secrets. Modify `app/main.py` or `RestaurantStore.load()` to download and cache the dataset on first run.
   - If dataset is small (<50 MB), you can commit it to the repo to simplify deployment.

5. Monitoring & updates

   - Streamlit Cloud will show logs and app status. Use the Logs panel to inspect startup problems.
   - To update, push a new commit to the branch connected to the Streamlit app — Streamlit Cloud will redeploy automatically.

## Alternative: containerized deployment (Docker)

If you prefer running everything (React frontend + FastAPI backend + optional Streamlit UI) as containers, use Docker and deploy to a container host (Cloud Run, AWS ECS, Azure Container Instances, Render):

1. Add `Dockerfile` for the Streamlit app (example):

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

2. (Optional) Docker Compose to run backend + frontend + streamlit

3. Build and push an image to a registry, then deploy on your cloud provider.

## CI / Automation recommendations

- Add a GitHub Actions workflow to run tests and lint on pull requests (use `python -m pytest` and `pip install -r requirements.txt`).
- Optionally add a job that builds a small artifact (e.g., preprocessed dataset) and uploads it to GitHub Releases or S3, then reference that artifact in Streamlit startup.

## Troubleshooting checklist

- App fails to start on Streamlit Cloud: check logs for missing packages, Python version mismatch, or missing secrets.
- RestaurantStore raises FileNotFoundError: ensure `data/processed/` is present or implement a download path from `DATA_URL`.
- LLM calls fail: verify secrets (`LLM_API_KEY`) and provider endpoints; run locally to reproduce.

## Minimal acceptance criteria (before marking deploy done)

- The Streamlit app at `app/main.py` starts successfully on Streamlit Cloud.
- The app can load the restaurant store (either from committed `data/processed/` or via download) and serve recommendations.
- LLM-based explanations function if a valid `LLM_API_KEY` is provided; otherwise the app gracefully falls back to rating-based recommendations.

---

If you'd like, I can:

- Add a small helper in `app/main.py` to auto-download `DATA_URL` when `RestaurantStore.load()` fails.
- Create a `Dockerfile` and `docker-compose.yml` for a containerized deployment.
- Create a GitHub Actions workflow for CI and a small script to upload or embed processed data.

Choose one and I'll implement it next.
