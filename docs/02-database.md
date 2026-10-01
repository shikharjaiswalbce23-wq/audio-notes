# Phase 2 — Database

> **Status:** ✅ Completed

This document covers:
- PostgreSQL/SQLite connection with SQLAlchemy configured in `database.py`.
- The `Upload` model created in `models.py` featuring a `GUID` column for UUID primary keys.
- Pydantic schemas defined in `schemas.py` for request validation and response formatting.
- Migrations set up with Alembic (run `alembic upgrade head`).
- CRUD operations implemented in `crud.py` for creating uploads, updating statuses, and saving transcription/summary results.
