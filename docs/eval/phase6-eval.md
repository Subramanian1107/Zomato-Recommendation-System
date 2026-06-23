# Phase 6 Evaluation — Quality, Observability & v1 Sign-Off

**Phase:** 6 — Quality & Docs  
**Depends on:** Phase 5  
**Blocks:** v1 release  
**Implementation plan:** [§ Phase 6](../implementationPlan.md#phase-6--quality-observability--documentation)  
**Edge cases:** [PERF-*, SEC-*, GROUND-*](../edgecase.md#phase-6--quality--cross-cutting)

---

## Objective

Confirm the full system meets success criteria from the problem statement, passes automated tests, includes complete documentation, and is ready for demo or deployment.

---

## Prerequisites

- Phases 0–5 signed off
- `.env` configured with valid `OPENAI_API_KEY`
- Fresh clone test optional but recommended

---

## Evaluation Criteria

### P0 — Must Pass (Release Blockers)

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E6.1 | `pytest` full suite passes with zero failures | `pytest -v` | ☐ |
| E6.2 | README enables setup from scratch | Fresh clone walkthrough | ☐ |
| E6.3 | `.env.example` documents all variables | Compare to `config.py` | ☐ |
| E6.4 | No secrets in repository | Manual + git scan | ☐ |
| E6.5 | Grounding audit: 10 live responses, no hallucinated names/ratings | Audit table below | ☐ |
| E6.6 | Filter accuracy: hard constraints respected in 5 spot-checks | Manual API tests | ☐ |
| E6.7 | LLM failure degrades to fallback without crash | Force fallback test | ☐ |
| E6.8 | End-to-end demo script completes | [Final demo](../implementationPlan.md#final-demo-script) | ☐ |
| E6.9 | All phase eval docs (0–5) signed off | Review eval folder | ☐ |

### P1 — Should Pass (Quality Bar)

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E6.10 | Warm cache load < 2s | Timed startup | ☐ |
| E6.11 | Filter pipeline < 100ms | Log or timed test | ☐ |
| E6.12 | E2E recommendation < 10s (typical) | Timed POST | ☐ |
| E6.13 | Logs include filter output count per request | Log review | ☐ |
| E6.14 | Logs include LLM latency per request | Log review | ☐ |
| E6.15 | Logs include `fallback_used` when applicable | Log review | ☐ |
| E6.16 | Minimum test counts met | See table below | ☐ |
| E6.17 | Test fixture with 10–20 edge-case rows exists | `tests/fixtures/` | ☐ |

### P2 — Nice to Have

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E6.18 | Dockerfile builds and runs API | `docker build` | ☐ |
| E6.19 | GitHub Actions CI runs pytest on push | CI green | ☐ |
| E6.20 | Request ID in all recommendation logs | Log review | ☐ |

---

## Minimum Test Counts

| Area | Minimum | Actual | Pass |
|------|---------|--------|------|
| Preprocessor unit tests | 8+ | | ☐ |
| Filter unit tests | 10+ | | ☐ |
| Parser unit tests | 6+ | | ☐ |
| API integration tests | 5+ | | ☐ |
| E2E mocked LLM tests | 2+ | | ☐ |

---

## Success Criteria Mapping (Problem Statement)

| # | Success Criterion | Verification | Pass |
|---|-------------------|--------------|------|
| SC-1 | Filter accurately | Phase 2 tests + 5 manual API checks | ☐ |
| SC-2 | Recommend meaningfully | Demo + soft preference test | ☐ |
| SC-3 | Explain clearly | Review 5 explanation texts | ☐ |
| SC-4 | Stay grounded | Grounding audit table | ☐ |
| SC-5 | Perform acceptably | PERF-01–04 checks | ☐ |

---

## Grounding Audit (10 Samples)

Run 10 varied `POST /recommendations` requests. For each response item, verify facts against dataset.

| Run # | Preferences (summary) | Names grounded? | Ratings match? | Costs match? | Pass |
|-------|----------------------|-----------------|----------------|--------------|------|
| 1 | Indiranagar + North Indian | ☐ | ☐ | ☐ | ☐ |
| 2 | Koramangala + Chinese | ☐ | ☐ | ☐ | ☐ |
| 3 | Banashankari + Italian | ☐ | ☐ | ☐ | ☐ |
| 4 | + additional "family-friendly" | ☐ | ☐ | ☐ | ☐ |
| 5 | + online_order true | ☐ | ☐ | ☐ | ☐ |
| 6 | Low budget + 4.0 rating | ☐ | ☐ | ☐ | ☐ |
| 7 | High budget + 4.5 rating | ☐ | ☐ | ☐ | ☐ |
| 8 | Rare cuisine combo | ☐ | ☐ | ☐ | ☐ |
| 9 | Fallback forced | ☐ | ☐ | ☐ | ☐ |
| 10 | max_results=3 | ☐ | ☐ | ☐ | ☐ |

**Audit passes if:** 0 hallucinated restaurants; 0 factual field mismatches.

---

## Performance Checklist

| Metric | Target | Measured | Pass |
|--------|--------|----------|------|
| Cold dataset load | < 30s | | ☐ |
| Warm cache load | < 2s | | ☐ |
| Filter pipeline | < 100ms | | ☐ |
| E2E with LLM | < 10s | | ☐ |

---

## Final Demo Script

Execute end-to-end:

```bash
# 1. Setup
git clone <repo> && cd Zomato
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env   # add OPENAI_API_KEY

# 2. API
uvicorn zomato_rec.main:app --port 8000

# 3. UI (new terminal)
streamlit run ui/streamlit_app.py

# 4. Tests
pytest -v
```

| Step | Pass |
|------|------|
| Install succeeds | ☐ |
| `/health` OK | ☐ |
| Streamlit → 5 recommendations with explanations | ☐ |
| Strict filters → empty state guidance | ☐ |
| `pytest` all green | ☐ |

---

## Documentation Checklist

| Document | Complete | Pass |
|----------|----------|------|
| README.md | Setup + run + architecture links | ☐ |
| `.env.example` | All vars | ☐ |
| problemStatement.md | Current | ☐ |
| architecture.md | Current | ☐ |
| implementationPlan.md | Current | ☐ |
| edgecase.md | Current | ☐ |
| eval/*.md | All phases | ☐ |

---

## v1 Definition of Done

From [implementationPlan.md](../implementationPlan.md#definition-of-done-v1):

| # | Done When | Pass |
|---|-----------|------|
| 1 | All phases 0–6 meet P0 eval criteria | ☐ |
| 2 | Streamlit user receives 5 grounded recommendations | ☐ |
| 3 | Hard filters enforced deterministically | ☐ |
| 4 | LLM failures → fallback, no crash | ☐ |
| 5 | `pytest` passes; README complete | ☐ |
| 6 | Grounding audit: no hallucinated names | ☐ |

---

## Sign-Off

| Field | Value |
|-------|-------|
| Evaluator | |
| Date | |
| Result | ☐ **v1 Approved** &nbsp; ☐ Fail — blockers: |

**Notes:**
