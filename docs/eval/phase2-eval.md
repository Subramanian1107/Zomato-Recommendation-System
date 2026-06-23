# Phase 2 Evaluation — Filtering Layer

**Phase:** 2 — Filtering  
**Depends on:** Phase 1  
**Blocks:** Phase 3  
**Implementation plan:** [§ Phase 2](../implementationPlan.md#phase-2--filtering-layer)  
**Edge cases:** [FILT-*](../edgecase.md#phase-2--filtering)

---

## Objective

Verify hard filters enforce user constraints deterministically, candidate sets are bounded, ranking is correct, and empty results include actionable guidance.

---

## Prerequisites

- Phase 1 signed off
- `RestaurantIndex` buildable from cache
- `UserPreferences` model defined

---

## Evaluation Criteria

### P0 — Must Pass

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E2.1 | Location filter returns only matching neighborhood | Unit test Indiranagar | ☐ |
| E2.2 | Cuisine filter supports partial match (`Indian` → `North Indian`) | Unit test | ☐ |
| E2.3 | Min rating filter excludes `rating = None` | Unit test | ☐ |
| E2.4 | Min rating uses `>=` boundary | 4.0 excludes 3.9 | ☐ |
| E2.5 | Budget filter respects percentile bands from index | Unit test per band | ☐ |
| E2.6 | Restaurants with null cost excluded when budget filter active | FILT-30 test | ☐ |
| E2.7 | Candidate count never exceeds `MAX_CANDIDATES` (20) | Test high-match query | ☐ |
| E2.8 | Pre-LLM ranker sorts rating DESC, votes DESC | Unit test ties | ☐ |
| E2.9 | Empty filter result includes `relaxation_note` | Overly strict combo | ☐ |
| E2.10 | Filter pipeline completes in < 100ms on full index | Timed run | ☐ |
| E2.11 | Unit tests pass | `pytest tests/unit/test_filters.py -v` | ☐ |

### P1 — Should Pass

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E2.12 | Case-insensitive location match | FILT-01 | ☐ |
| E2.13 | Optional `online_order=True` filter works | FILT-40 | ☐ |
| E2.14 | Optional `book_table=True` filter works | FILT-41 | ☐ |
| E2.15 | Both boolean filters use AND logic | Combined test | ☐ |
| E2.16 | Tie-breaker stable when rating and votes equal | FILT-52 | ☐ |
| E2.17 | Fewer than 5 matches returns all (no padding) | FILT-54 | ☐ |
| E2.18 | Relaxation note suggests specific filter to loosen | Manual review message | ☐ |

### P2 — Nice to Have

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E2.19 | Log `filter.input_count` and `filter.output_count` | Log inspection | ☐ |
| E2.20 | Fuzzy location suggestions for unknown input | FILT-02 (may live in Phase 4) | ☐ |

---

## Automated Verification

```bash
pytest tests/unit/test_filters.py -v

python - <<'EOF'
from zomato_rec.data.index import build_index
from zomato_rec.filtering.engine import FilterEngine
from zomato_rec.models.preferences import UserPreferences
import time

index = build_index()
engine = FilterEngine(index)

prefs = UserPreferences(
    location="Koramangala",
    cuisine="North Indian",
    budget="medium",
    min_rating=4.0,
)
t0 = time.time()
candidates = engine.apply(prefs)
elapsed = (time.time() - t0) * 1000

print(f"Candidates: {len(candidates)} in {elapsed:.1f}ms")
assert all(c.location.lower() == "koramangala" for c in candidates)
assert len(candidates) <= 20
EOF
```

---

## Filter Scenario Test Matrix

| Scenario | Expected | Edge ID |
|----------|----------|---------|
| Location = `Indiranagar` | All in Indiranagar | FILT-01 |
| Cuisine = `Chinese` + location | Intersection only | — |
| `min_rating = 4.5` | None below 4.5 | FILT-23 |
| Budget = `low` | Costs within low band | FILT-30 |
| Rare cuisine + strict rating | Empty + note | FILT-60 |
| 500+ matches | Exactly 20, top rated | FILT-50 |

---

## Manual Checklist

- [ ] All P0 criteria pass
- [ ] Smoke test Koramangala + North Indian + medium + 4.0 returns ≥1 candidate
- [ ] Impossible combo returns empty list with helpful note
- [ ] No LLM calls in this phase (filter-only)

---

## Edge Cases to Spot-Check

| ID | Test |
|----|------|
| FILT-02 | Unknown location handling (or defer to Phase 4 API) |
| FILT-21 | min_rating=5.0 — very small or empty set |
| FILT-53 | Candidates with null rating ranked by votes |

---

## Sign-Off

| Field | Value |
|-------|-------|
| Evaluator | |
| Date | |
| Result | ☐ Pass → proceed to Phase 3 &nbsp; ☐ Fail — blockers: |

**Notes:**
