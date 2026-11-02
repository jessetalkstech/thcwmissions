# Project Plan: theHunter: Call of the Wild Mission Tracker

## Project Goal
Create an unofficial mission system for *theHunter: Call of the Wild* to replicate the "classic" experience. Users upload harvest screenshots, and the system automatically validates progress against ordered objectives, awards points, and maintains a leaderboard.

## High-Level Architecture
|- **Backend:** FastAPI (Python 3.12) with SQLAlchemy 2.0 and PostgreSQL.
|- **Vision Engine:** Self-hosted Ollama running the Gemma4 model (accessible via API).
|- **Frontend (MVP):** FastAPI + Jinja2 templates (fastest path to MVP; swappable for a TypeScript SPA later).
|- **Infrastructure:** Dockerized environment for the backend and database.

## Data Model
|- **User:** ID, username, hashed_password, points, created_at.
|- **Mission:** ID, title, description, base_points.
|- **Objective:** ID, mission_id, description, order_index, is_completed.
|- **Harvest:** ID, user_id, image_url, extracted_data (JSON), status (Pending/Processed/Failed).
|- **User_Mission:** user_id, mission_id, current_objective_id, status (Active/Completed).

## Roadmap

### Phase 1: Foundations (The Scaffold)
|- [x] Initialize project structure (`backend/`, `frontend/`, `prompts/`).
|- [x] Configure `pyproject.toml` and environment variables (`.env.example`).
|- [x] Dockerize the PostgreSQL database and FastAPI backend.
|- [x] Define initial SQLAlchemy models and Alembic migrations.

### Phase 2: Mission Engine
|- [x] Implement User authentication and profile management.
|- [x] Create Mission and Objective CRUD.
|- [x] Build the logic for "Active" missions and progress tracking.
|- [x] Implement the point system and leaderboard queries.

### Phase 3: Vision Pipeline
|- [x] Configure local Ollama instance for Gemma4.
|- [x] Build the image upload and processing endpoint.
|- [x] Implement the extraction logic (Text/Image -> JSON).
|- [x] Build the "Validation" logic: compare extracted JSON against the current objective's requirements.

### Phase 4: Frontend & Polishing
|- [x] Build the main dashboard (Jinja2 templates).
|- [x] Build the "Mission View" and "Upload" pages.
|- [x] Implement the Leaderboard UI.
|- [x] Final testing and ruff linting.
