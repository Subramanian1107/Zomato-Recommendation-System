# Phase 4 Evaluation — API & Orchestration

**Phase:** 4 — API & Orchestration  
**Depends on:** Phase 3  
**Blocks:** Phase 5  
**Implementation plan:** [§ Phase 4](../implementationPlan.md#phase-4--api--orchestration)  
**Edge cases:** [API-*](../edgecase.md#phase-4--api--orchestration)

---

## Objective

Verify the full recommendation pipeline is exposed via FastAPI with correct contracts, startup lifecycle, error handling, and acceptable end-to-end latency.

---

## Prerequisites

- Phase 3 signed off
- `OPENAI_API_KEY` in `.env` for live E2E test
- Server startable via uvicorn

---

## Evaluation Criteria

### P0 — Must Pass

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E4.1 | `GET /health` returns 200 | `curl /health` | ☐ |
| E4.2 | `GET /metadata/locations` returns location list | curl + count ~93 | ☐ |
| E4.3 | `GET /metadata/cuisines` returns cuisine list | curl | ☐ |
| E4.4 | `GET /metadata/budget-bands` returns low/medium/high | curl | ☐ |
| E4.5 | `POST /recommendations` valid request returns 200 + results | curl POST | ☐ |
| E4.6 | Response includes `summary`, `recommendations`, `candidate_count` | JSON inspection | ☐ |
| E4.7 | Each item has explanation + dataset-backed facts | Response review | ☐ |
| E4.8 | No matches returns 200 with empty list + `relaxation_note` | Strict filters POST | ☐ |
| E4.9 | Invalid body returns 422 | Missing field POST | ☐ |
| E4.10 | Unknown location returns 422 with suggestions | API-02 POST | ☐ |
| E4.11 | Index loaded once at startup (lifespan) | Log / code review | ☐ |
| E4.12 | OpenAPI docs at `/docs` | Browser check | ☐ |
| E4.13 | Integration tests pass | `pytest tests/integration/ -v` | ☐ |
| E4.14 | E2E with real LLM completes in < 10 seconds | Timed curl | ☐ |

### P1 — Should Pass

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E4.15 | LLM timeout returns fallback or 504 per architecture | Mock timeout | ☐ |
| E4.16 | LLM parse failure returns 200 with fallback results | Mock bad JSON | ☐ |
| E4.17 | `filters_applied` echoed in response | Response inspection | ☐ |
| E4.18 | Structured logging: filter counts, LLM latency | Log review | ☐ |
| E4.19 | Concurrent requests handled without error | 5 parallel curls | ☐ |
| E4.20 | `max_results` respected (1–10) | POST with max_results=3 | ☐ |

### P2 — Nice to Have

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E4.21 | Request ID in logs | Log inspection | ☐ |
| E4.22 | `/health` reports degraded if index not ready | API-10 | ☐ |
| E4.23 | CORS configured for Streamlit origin | Phase 5 prep | ☐ |

---

## Automated Verification

```bash
uvicorn zomato_rec.main:app --port 8000 &
sleep 5  # allow index load

curl -s http://localhost:8000/health
curl -s http://localhost:8000/metadata/locations | head -c 200
curl -s -X POST http://localhost:8000/recommendations \
  -H "Content-Type: application/json" \
  -d '{"location":"Indiranagar","cuisine":"North Indian","budget":"medium","min_rating":4.0}'

pytest tests/integration/test_recommendation_flow.py -v
```

---

## API Test Matrix

| Request | Expected HTTP | Expected Body | Edge ID |
|---------|---------------|---------------|---------|
| Valid preferences | 200 | ≥1 recommendation | — |
| Strict impossible filters | 200 | `recommendations: []` + note | API-20 |
| Missing `location` | 422 | validation error | API-01 |
| `min_rating: 6` | 422 | validation error | API-03 |
| Unknown location `"Delhi"` | 422 | suggestions | DATA-60 |
| `budget: "premium"` | 422 | validation error | API-04 |

---

## Sample Valid Request

```json
{
  "location": "Indiranagar",
  "cuisine": "North Indian",
  "budget": "medium",
  "min_rating": 4.0,
  "additional_preferences": "family-friendly",
  "online_order": null,
  "book_table": null,
  "max_results": 5
}
```

---

## Manual Checklist

- [ ] All P0 criteria pass
- [ ] Startup logs row count and load time
- [ ] `/docs` shows correct request/response schemas
- [ ] No API key in logs or error responses

---

## Edge Cases to Spot-Check

| ID | Test |
|----|------|
| API-11 | 5 concurrent POST /recommendations |
| API-21 | Force fallback — still 200 with results |
| API-30 | Kill parquet + corrupt cache — startup fails clearly |

---

## Sign-Off

| Field | Value |
|-------|-------|
| Evaluator | |
| Date | |
| Result | ☐ Pass → proceed to Phase 5 &nbsp; ☐ Fail — blockers: |

**Notes:**
