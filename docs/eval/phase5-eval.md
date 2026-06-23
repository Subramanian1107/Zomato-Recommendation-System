# Phase 5 Evaluation — UI (Streamlit)

**Phase:** 5 — UI  
**Depends on:** Phase 4  
**Blocks:** Phase 6  
**Implementation plan:** [§ Phase 5](../implementationPlan.md#phase-5--ui-streamlit)  
**Edge cases:** [UI-*](../edgecase.md#phase-5--ui-streamlit)

---

## Objective

Verify the Streamlit frontend collects preferences, calls the FastAPI backend, and displays recommendations, empty states, and errors in a user-friendly way—with no duplicated business logic.

---

## Prerequisites

- Phase 4 signed off
- FastAPI running on `localhost:8000` (or configured base URL)
- `OPENAI_API_KEY` set for live recommendation flow

---

## Evaluation Criteria

### P0 — Must Pass

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E5.1 | Location dropdown populated from `/metadata/locations` | UI inspection (not hardcoded) | ☐ |
| E5.2 | Cuisine dropdown populated from `/metadata/cuisines` | UI inspection | ☐ |
| E5.3 | Budget select: low / medium / high | UI inspection | ☐ |
| E5.4 | Min rating slider/input within 0–5 | UI inspection | ☐ |
| E5.5 | Submit triggers `POST /recommendations` | Network tab / logs | ☐ |
| E5.6 | Loading spinner shown during request | UI observation | ☐ |
| E5.7 | Results show rank, name, location, rating, cost, cuisines, explanation | Card review | ☐ |
| E5.8 | LLM `summary` displayed above cards | UI inspection | ☐ |
| E5.9 | Empty results show `relaxation_note` | Strict filter test | ☐ |
| E5.10 | API down shows connection error (no raw stack trace) | Stop API, submit | ☐ |
| E5.11 | No filter/LLM logic in UI code | Code review | ☐ |
| E5.12 | API base URL configurable | Env or config var | ☐ |

### P1 — Should Pass

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E5.13 | Additional preferences text area max 500 chars | UI-08 |
| E5.14 | Online order / book table toggles passed to API | Network inspect POST body | ☐ |
| E5.15 | 422 validation errors shown to user | Invalid submit path | ☐ |
| E5.16 | Null rating displayed gracefully | UI-04 |
| E5.17 | Null cost displayed gracefully | UI-05 |
| E5.18 | Unicode restaurant names render correctly | UI-12 spot-check | ☐ |

### P2 — Nice to Have

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E5.19 | Session state preserves results on minor rerun | UI-10 |
| E5.20 | Popular dishes shown on cards | UI enhancement | ☐ |
| E5.21 | Bangalore-only scope note in UI header | DATA-60 UX | ☐ |

---

## Manual Test Script

### Test 1 — Happy Path

1. Start API: `uvicorn zomato_rec.main:app --port 8000`
2. Start UI: `streamlit run ui/streamlit_app.py`
3. Select: Koramangala, Chinese, medium budget, min rating 3.5
4. Click **Get Recommendations**

| Check | Pass |
|-------|------|
| Loading spinner appears | ☐ |
| Summary text shown | ☐ |
| Up to 5 recommendation cards | ☐ |
| Each card has explanation | ☐ |
| Ratings/costs look reasonable | ☐ |

### Test 2 — Empty State

1. Select strict filters (e.g., min rating 5.0 + rare cuisine + book table)
2. Submit

| Check | Pass |
|-------|------|
| No crash | ☐ |
| Relaxation guidance shown | ☐ |
| Suggestion to loosen filters | ☐ |

### Test 3 — Error State

1. Stop FastAPI
2. Submit form

| Check | Pass |
|-------|------|
| User-friendly error message | ☐ |
| No Python traceback in UI | ☐ |

### Test 4 — Additional Preferences

1. Enter: "family-friendly, quiet atmosphere"
2. Submit with moderate filters

| Check | Pass |
|-------|------|
| Request succeeds | ☐ |
| Explanations reference soft preferences where possible | ☐ |

---

## UI Scenario Matrix

| Scenario | Expected | Edge ID |
|----------|----------|---------|
| API offline | Connection error banner | UI-01 |
| Slow API (>10s) | Spinner persists | UI-02 |
| Empty results | Relaxation note visible | UI-03 |
| Long explanation | Text wraps, no overflow | UI-06 |
| Metadata fetch fails on load | Error + disabled submit | UI-07 |

---

## Architecture Compliance

| Rule | Pass |
|------|------|
| UI calls API only (no direct index/LLM access) | ☐ |
| Dropdown values from metadata endpoints | ☐ |
| Business logic lives in API layer | ☐ |

---

## Sign-Off

| Field | Value |
|-------|-------|
| Evaluator | |
| Date | |
| Result | ☐ Pass → proceed to Phase 6 &nbsp; ☐ Fail — blockers: |

**Notes:**
