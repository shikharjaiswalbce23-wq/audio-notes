# Troubleshooting

## Goal

A quick reference for common problems and how to fix them.

> This document will grow with each phase. Check back after each phase is implemented.

---

## General

### Backend won't start

**Symptom:** `uvicorn: command not found` or `ModuleNotFoundError`

**Fix:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

### Frontend won't start

**Symptom:** `next: command not found` or `Module not found`

**Fix:**
```bash
cd frontend
npm install
npm run dev
```

---

### Database connection refused

**Symptom:** `could not connect to server: Connection refused`

**Fix:**
1. Check that PostgreSQL is running
2. Check `DATABASE_URL` in `backend/.env`
3. Make sure the database exists

---

### Redis connection refused

**Symptom:** `redis.exceptions.ConnectionError`

**Fix:**
1. Check that Redis is running: `redis-cli ping` → should return `PONG`
2. Check `REDIS_URL` in `backend/.env`

---

### CORS error in browser

**Symptom:** `Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000' has been blocked by CORS policy`

**Fix:** Make sure `CORS_ORIGINS` in the backend includes `http://localhost:3000`. See `backend/app/main.py`.

---

## More entries will be added each phase.
