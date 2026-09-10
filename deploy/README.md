# Deploy guide
## Backend -> Render (free)
1. Push repo to GitHub. In Render dashboard: New -> Blueprint -> select repo (uses deploy/render-backend/render.yaml).
2. Or New -> Web Service -> Root Directory `deploy/render-backend`, Build `pip install -r requirements.txt`, Start `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1`, Plan Free.
3. Add env DR_MODEL_ID / DR_MODEL_FILE (defaults already set).
4. Wait for /api/health to return healthy. First /api/screen call downloads model (~100-300MB) into HF cache - can take 60-120s on free tier, then cached until redeploy/sleep.
## Frontend -> Vercel (free)
1. Vercel -> New Project -> import repo. Framework: Vite. Root: repo root (package.json is at repo root). Build `npm run build`, Output `dist`.
2. Env var: VITE_API_BASE_URL=https://<render-service>.onrender.com (no trailing slash).
3. Deploy. Frontend calls `${VITE_API_BASE_URL}/api/screen` - already wired in src/services/api.ts.
