# EmailScout Project – Senior Developer Overview

## 📄 Project Summary

This repository implements a **smart email assistant** that:

1. **Detects scams** and classifies emails as safe/unsafe.
2. **Recognises opportunities** (scholarships, internships, jobs, workshops, competitions) using NLP/AI.
3. **Scores relevance** based on a student’s profile (major & interests).
4. **Provides a polished dashboard** with priority badges, deadlines, reminders, and task management.

The code follows modern Django best‑practice patterns, is fully type‑annotated where useful, and includes extensive inline documentation to aid future contributors.

---

## 🔎 Opportunity Recognition & Relevance Scoring

**Responsibilities**
- Identify opportunity types from email content.
- Parse text with regular‑expression heuristics and optional NLP models.
- Match against the user’s `StudentProfile` (major + comma‑separated interests).
- Generate a relevance score (0‑10) and optional deadline extraction.

**Key Implementation**
- `emails/opportunity_detection.py` → `OpportunityDetector` class.
- Integrated into the fetch pipeline (`fetch_emails`) after scam detection.
- Scores are stored on the `Email` model (`opportunity_type`, `relevance_score`, `deadline`).
- Dashboard views (`opportunities_board`) compute priority badges based on deadline proximity and relevance.

---

## 🛡️ Scam Detection & Email Filtering

**Responsibilities**
- Analyze sender, links, and content for phishing cues.
- Classify emails with a confidence score and detailed reason list.
- Auto‑reject high‑confidence scams and flag suspicious ones.

**Key Implementation**
- `emails/scam_detection.py` → `ScamDetector` class.
- Runs immediately after a new email is persisted.
- Adds fields to `Email` (`is_scam`, `scam_confidence`, `scam_reasons`, `scam_severity`, `is_flagged`).
- Security report view (`security_report`) aggregates statistics and displays recent flagged items.

---

## 📊 Dashboard & User Interface

**Responsibilities**
- Show filtered opportunities with deadlines, scores, and dynamic priority badges.
- Enable users to add reminders/tasks directly from email listings.
- Provide a clean, responsive UI built with vanilla CSS, modern typography, and subtle animations.

**Key Implementation**
- Templates: `email_list.html`, `opportunities_board.html`, `security_report.html`.
- Models: `Task` (reminders) with add/toggle views.
- Navigation bar includes **Dashboard**, **Opportunities**, **Profile**, and **Logout**.
- Priority logic in `views.py` now safely handles `None` relevance scores.

---

## 🛠️ Senior‑Level Development Practices

- **Modular architecture** – each functional area lives in its own module (`scam_detection`, `opportunity_detection`, `tasks`).
- **Type safety & linting** – run `flake8` and `mypy` as part of CI (not shown here but recommended).
- **Comprehensive tests** – unit tests for detectors and integration tests for view logic should reside in `emails/tests/`.
- **Documentation** – every public class/function includes a docstring; high‑level design lives in this README and `PROJECT_OVERVIEW.md`.
- **Security‑first** – all external API calls use OAuth tokens with scoped permissions; no secrets are hard‑coded.
- **Performance** – email fetching runs in parallel via `ThreadPoolExecutor`; avoid blocking DB calls.

---

## 📦 Getting Started

```bash
# Activate virtualenv (if used)
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Run development server
python manage.py runserver
```

Navigate to `http://127.0.0.1:8000/` and explore the dashboard.

---

*Prepared by the senior development lead to guide future contributors and maintain high code quality.*
