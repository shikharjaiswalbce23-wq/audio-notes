# Phase 11 — Deployment

> **Status:** ✅ Implemented

## Goal
To configure the application for production deployment, setting up the infrastructure as code, environment variables, and CORS policies to ensure secure and reliable communication between the frontend and backend services.

---

## What was implemented

### 1. Infrastructure as Code (`render.yaml`)
Created a simplified Render Blueprint (`render.yaml`) to define the backend infrastructure declaratively. This file configures:
- **FastAPI Web Service:** The main API backend, automatically running database migrations (`alembic upgrade head`) before starting `uvicorn`.
- **BackgroundTasks:** Refactored the architecture to use FastAPI's built-in `BackgroundTasks` instead of a separate RQ worker. This allows the backend to be deployed **100% for free** on Render's Web Service tier.
- **Managed PostgreSQL Instance:** A free-tier PostgreSQL database for storing upload metadata and results.

### 2. CORS & Security (`main.py`)
- Updated `CORSMiddleware` in FastAPI to dynamically read the allowed origin from the `FRONTEND_URL` environment variable.
- This ensures the API only accepts cross-origin requests from the production Next.js frontend or `http://localhost:3000` during local development, preventing unauthorized access.

### 3. Database URL Compatibility (`database.py`)
- Render and Heroku often provide PostgreSQL connection strings starting with `postgres://`, which is no longer supported in newer versions of SQLAlchemy.
- Added a patch in `database.py` to automatically intercept and rewrite `postgres://` to `postgresql://` on startup, preventing deployment crashes.

---

## Deployment Instructions

### Deploying the Backend (Render)
1. Push your code to a GitHub repository.
2. Log in to [Render](https://render.com) and click **New > Blueprint**.
3. Connect your repository. Render will automatically detect the `render.yaml` file.
4. Fill in the missing secret environment variables (AWS, Gnan, Gemini credentials, and `FRONTEND_URL` once Vercel is deployed).
5. Click **Apply**. Render will automatically provision the PostgreSQL DB and the FastAPI Web Service on their free tiers!

### Deploying the Frontend (Vercel)
1. Log in to [Vercel](https://vercel.com) and click **Add New > Project**.
2. Select your GitHub repository.
3. Vercel will automatically detect the Next.js framework.
4. Set the `NEXT_PUBLIC_API_URL` environment variable to your deployed Render Web Service URL (e.g., `https://audio-notes-api.onrender.com`).
5. Click **Deploy**.
6. Once deployed, take the Vercel URL and update the `FRONTEND_URL` variable in your Render dashboard to allow CORS.

---

## Interview Explanation

> "In Phase 11, I prepared the application for a production environment. To ensure the project could be hosted entirely for free on Render without adding a credit card, I refactored the architecture to remove the separate Redis/RQ background worker, opting instead for FastAPI's built-in `BackgroundTasks`. This allowed me to define a streamlined infrastructure-as-code `render.yaml` file containing just a Web Service and a PostgreSQL database. I also ensured that our FastAPI app handles dynamic CORS origins securely using environment variables and patched a common SQLAlchemy deployment bug regarding the `postgres://` URL scheme. Finally, the frontend is ready to be deployed on Vercel simply by pointing `NEXT_PUBLIC_API_URL` to our deployed backend API."
