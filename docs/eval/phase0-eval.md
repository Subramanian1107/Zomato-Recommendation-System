# Phase 0 Evaluation — Project Setup

**Phase:** 0 — Project Setup  
**Depends on:** —  
**Blocks:** Phase 1  
**Implementation plan:** [§ Phase 0](../implementationPlan.md#phase-0--project-setup)  
**Edge cases:** [SETUP-*](../edgecase.md#phase-0--project-setup)

---

## Objective

Confirm the repository skeleton, dependency management, and configuration foundation are ready for incremental development.

---

## Prerequisites

- Python 3.11+ installed
- Fresh virtual environment recommended for evaluation

---

## Evaluation Criteria

### P0 — Must Pass

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E0.1 | `pyproject.toml` exists with package name and dependencies | Inspect file | ☐ |
| E0.2 | Editable install succeeds | `pip install -e ".[dev]"` or `pip install -e .` | ☐ |
| E0.3 | `from zomato_rec.config import Settings` imports without error | `python -c "from zomato_rec.config import Settings"` | ☐ |
| E0.4 | Directory layout matches [architecture §3](../architecture.md#3-project-structure) | Compare tree to spec | ☐ |
| E0.5 | `.env.example` documents all required environment variables | Manual review | ☐ |
| E0.6 | `.gitignore` excludes `.env`, `data/processed/`, `.venv`, `__pycache__` | Inspect file | ☐ |
| E0.7 | No secrets committed in repository | `git status` + scan for keys | ☐ |
| E0.8 | Domain model stub files exist under `models/` | File check | ☐ |
| E0.9 | `tests/conftest.py` exists; pytest discovers test package | `pytest --collect-only` | ☐ |

### P1 — Should Pass

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E0.10 | `Settings` loads defaults when `.env` absent | Run without `.env`; non-secret defaults work | ☐ |
| E0.11 | Invalid env values fail with readable Pydantic error | Set `MAX_CANDIDATES=invalid`; expect validation error | ☐ |
| E0.12 | `data/processed/.gitkeep` present | File exists | ☐ |

### P2 — Nice to Have

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E0.13 | Dev extras include pytest, pytest-asyncio | `pyproject.toml` optional deps | ☐ |
| E0.14 | Python version constraint documented in README or pyproject | File review | ☐ |

---

## Automated Verification

```bash
cd /path/to/Zomato
python -m venv .venv && source .venv/bin/activate
pip install -e .
python -c "from zomato_rec.config import Settings; print(Settings())"
pytest --collect-only
```

**Expected:** No import errors; pytest collects tests (may be zero).

---

## Manual Checklist

- [ ] All P0 criteria marked pass
- [ ] Project structure matches architecture doc
- [ ] `.env.example` includes: `OPENAI_API_KEY`, `LLM_MODEL`, `MAX_CANDIDATES`, `DATA_CACHE_PATH`, `API_PORT`
- [ ] Stubs importable: `preferences`, `restaurant`, `recommendation` models

---

## Edge Cases to Spot-Check

| ID | Test |
|----|------|
| SETUP-01 | Start without `.env` — no crash on import |
| SETUP-02 | Invalid env type — clear validation message |
| SETUP-06 | Confirm `.env` not tracked by git |

---

## Sign-Off

| Field | Value |
|-------|-------|
| Evaluator | |
| Date | |
| Result | ☐ Pass → proceed to Phase 1 &nbsp; ☐ Fail — blockers: |

**Notes:**
