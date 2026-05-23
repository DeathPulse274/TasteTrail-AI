# Deployment Plan — TasteTrail-AI

This document explains how to deploy the TasteTrail-AI project:
- Backend (FastAPI) on Railway
- Frontend (Vite + React) on Vercel

Keep secrets (LLM keys, DATA_URL) only in host environment variables/secrets (never commit to Git).

---

## 1. Architecture overview

- Backend: FastAPI app located under `src/tastetrail/api` exposing `/api/*` endpoints used by the frontend.
- Frontend: Vite + React in `frontend/` that calls the backend API for recommendations.
- Data: processed dataset (`data/processed/restaurants.parquet`) used by the backend; prefer hosting this file on an object store (S3, Railway plugin, or using `DATA_URL`) and set `DATA_URL` or provide persistent storage on the host.
- Secrets: LLM provider keys (`LLM_API_KEY`), `LLM_BASE_URL`, `LLM_MODEL`, and any storage credentials.

---

## 2. Prepare repository

1. Make sure `requirements.txt` is accurate for the Python backend and `pyproject.toml`/`poetry.lock` if used.
2. Add a `Procfile` (recommended for Railway):

```
web: uvicorn src.tastetrail.api.main:app --host 0.0.0.0 --port $PORT
```

3. Ensure the backend listens to the `$PORT` env var (FastAPI / Uvicorn default shown above).
4. Add a small `start` script in `frontend/package.json` if missing: `build` script should create a static `dist/` compatible with Vercel.

---

## 3. Backend deployment — Railway

Railway is ideal for simple Python web services.

A. Create and connect the Railway project
- Create a Railway account and new project.
- Connect your GitHub repository and pick the backend folder (root of repo) for deployment.

B. Configure build & start
- Railway auto-detects Python apps. If not, set build command:

```
pip install -r requirements.txt
```

- Set the start command to the `Procfile` command or:

```
uvicorn src.tastetrail.api.main:app --host 0.0.0.0 --port $PORT
```

C. Environment variables (add as Railway secrets)
- `DATA_PATH` — set to where your app expects the parquet or leave as default and use `DATA_URL`.
- `DATA_URL` — (recommended) publicly accessible URL to the processed `restaurants.parquet` in S3 or object storage. Backend will attempt to download it if file missing.
- `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` — the LLM config (store as Railway environment variables / secrets).
- Any additional DB/credentials used by your app.

D. Data & storage
- Prefer S3/compatible storage for the processed dataset. Upload `restaurants.parquet` and set `DATA_URL` to the file URL (presigned or public).
- Alternatively use Railway's filesystem if dataset is small and you commit it (not recommended for large files) or use Railway's persistent storage plugin.

E. CORS and domain
- Ensure backend CORS allows requests from your deployed frontend domain. E.g., configure FastAPI `CORSMiddleware` with Vercel domain(s).

F. Verify deployment
- After deploy, visit the Railway-assigned URL and test `/api/health` or `/api/locations`.

G. Logs & monitoring
- Use Railway logs to view app startup and runtime errors.
- Add health checks and uptime monitoring (Pingdom, UptimeRobot) if needed.

H. Rollbacks
- Railway supports redeploying previous commits; keep releases simple and tag releases for easy rollbacks.

---

## 4. Frontend deployment — Vercel

A. Prepare frontend
- Ensure `frontend/package.json` contains:
  - `build` script (e.g. `vite build`)
  - `preview` or `start` if needed locally
- Update the frontend to read the backend base URL from an env var. With Vite, use `VITE_API_BASE` and reference it in code as `import.meta.env.VITE_API_BASE`.
  - If the frontend currently uses relative paths (`/api/...`) configure Vercel to proxy API requests to your Railway URL (Vercel rewrites), or change the frontend to use absolute API URL at runtime.

B. Connect to Vercel
- Create a Vercel account and import the GitHub repo.
- Configure the project root to `frontend/`.
- Set build command: `npm install && npm run build` (or `pnpm`/`yarn` equivalents).
- Output directory: `dist` (Vite default) or as produced by your build.

C. Environment variables on Vercel
- Add `VITE_API_BASE` (e.g. `https://your-railway-app.up.railway.app`) in Vercel dashboard under Project Settings → Environment Variables for `Production`.
- If you must call LLM directly from frontend (not recommended), add public keys carefully — avoid exposing private keys in browser code.

D. CORS
- Ensure the backend `CORSMiddleware` allows the Vercel domain.

E. Preview / branches
- Vercel will deploy preview URLs for pull requests automatically.

F. Custom domain & SSL
- Add a custom domain in Vercel and configure DNS. Vercel provides automatic SSL certs.

G. Verify
- Visit the Vercel URL and ensure the UI loads and calls the backend successfully. Check the browser devtools network tab for failing requests.

---

## 5. CI / CD recommendations

- Use GitHub Actions to run tests and linting on push/PR. Basic example steps:
  - `actions/checkout`
  - Set up Python, install requirements, run tests `pytest`
  - Set up Node, run `npm ci` and `npm run build` for the frontend CI check (but Vercel will build itself).
- Configure protected branches and require CI to pass before merging to `main`.

---

## 6. Security & secrets

- Store `LLM_API_KEY` and any storage credentials only as host secrets (Railway / Vercel env vars). Do NOT commit `.env` to the repo.
- Use Railway/Vercel secret management and rotate keys periodically.
- Limit LLM API key scope if provider supports fine-grained keys.

---

## 7. Logging, metrics & error tracking

- Add structured logging in the backend (JSON logs) and forward logs to a provider (LogDNA, Datadog, Sentry).
- Add Sentry (or similar) to capture backend exceptions and frontend errors.

---

## 8. Costs & sizing

- Start with free-tier Railway and Vercel for staging.
- Move to paid tiers when you need guaranteed uptime, more concurrency, or larger model usage.
- Monitor LLM usage as it will likely be the dominant cost.

---

## 9. Rollback & emergency steps

- To rollback frontend: redeploy a previous successful commit in Vercel dashboard.
- To rollback backend: choose a previously successful deployment in Railway and redeploy.
- Keep a small checklist for key steps to disable LLM calls (e.g., unset `LLM_API_KEY`) if runaway costs occur.

---

## 10. Optional: Deploy Streamlit app

If you want the Streamlit replica deployed as well:
- Streamlit Cloud: Connect the repo, set `app/main.py` as the run file and add required secrets.
- Or deploy Streamlit on Railway: set start command `streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0` and set `PYTHONUNBUFFERED=1`.
- For larger traffic or better control, package the Streamlit app into a Docker container and deploy to Railway or any container host.

---

## Quick checklist (deploy order)

1. Upload dataset to S3 (or ensure `DATA_URL` is reachable).
2. Create Railway project and set env vars/secrets (including `DATA_URL`, LLM keys).
3. Deploy backend and verify `/api/locations` and `/api/recommendations`.
4. Configure CORS on backend for Vercel domain.
5. Create Vercel project for `frontend/`, set `VITE_API_BASE` to backend URL, and deploy.
6. Verify end-to-end flow in browser and monitor logs.

---

If you want, I can:
- Generate Railway `Dockerfile` and `Procfile` variants, or
- Add sample GitHub Actions workflows for CI/CD and automatic deploys to Railway/Vercel.

