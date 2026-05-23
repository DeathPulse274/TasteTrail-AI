# TasteTrail-AI Frontend

This is the React frontend for TasteTrail-AI, adapted from the provided Google AI Studio UI files.

## Run locally

1. Start the Python backend:
   ```bash
   cd ..
   python -m uvicorn tastetrail.api.main:app --reload
   ```
2. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```
3. Run the frontend:
   ```bash
   npm run dev
   ```

The app runs on `http://localhost:3000` and proxies API requests to the Python backend.
