# Phase 1 Evaluation — Data Layer

**Phase:** 1 — Data Layer  
**Depends on:** Phase 0  
**Blocks:** Phase 2  
**Implementation plan:** [§ Phase 1](../implementationPlan.md#phase-1--data-layer)  
**Edge cases:** [DATA-*](../edgecase.md#phase-1--data-layer)

---

## Objective

Verify the Hugging Face dataset loads, preprocesses correctly, caches to parquet, and exposes a queryable in-memory restaurant index with accurate metadata.

---

## Prerequisites

- Phase 0 signed off
- Network access for first-time Hugging Face download (or pre-seeded parquet cache)

---

## Evaluation Criteria

### P0 — Must Pass

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E1.1 | Cold start loads ~51,717 rows | Run loader; log row count | ☐ |
| E1.2 | Warm start from parquet completes in < 2 seconds | Time second startup | ☐ |
| E1.3 | Parquet cache written to `data/processed/` | File exists after first run | ☐ |
| E1.4 | Second run reuses cache (no re-download) | Delete network / observe logs | ☐ |
| E1.5 | `get_locations()` returns ~93 unique neighborhoods | `len(get_locations())` | ☐ |
| E1.6 | `get_cuisines()` returns deduplicated list | No duplicate entries after normalization | ☐ |
| E1.7 | `get_budget_ranges()` returns valid low/medium/high tuples | Min ≤ max for each band | ☐ |
| E1.8 | Missing ratings do not crash preprocessing | Process full dataset | ☐ |
| E1.9 | Missing costs do not crash preprocessing | Process full dataset | ☐ |
| E1.10 | `restaurant_id` stable across runs for same `url` | Hash same url twice | ☐ |
| E1.11 | Unit tests pass | `pytest tests/unit/test_preprocessor.py -v` | ☐ |

### P1 — Should Pass

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E1.12 | Rating `"4.5/5"` → `4.5` | Unit test | ☐ |
| E1.13 | Rating `"-"` → `None` | Unit test | ☐ |
| E1.14 | Cost `"1,200"` → `1200` | Unit test | ☐ |
| E1.15 | Cuisines normalized to lowercase list | Unit test | ☐ |
| E1.16 | `online_order` `"Yes"`/`"No"` → bool | Unit test | ☐ |
| E1.17 | Review snippets capped at 2–3 per restaurant | Inspect sample records | ☐ |
| E1.18 | Long reviews truncated without error | DATA-52 spot-check | ☐ |
| E1.19 | Corrupt cache triggers rebuild | DATA-70 manual test | ☐ |

### P2 — Nice to Have

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E1.20 | Cache version metadata for invalidation | Code review | ☐ |
| E1.21 | CLI entry for preprocess-only run | `python -m zomato_rec.data.preprocessor` | ☐ |
| E1.22 | Loader validates expected columns on schema change | DATA-02 test | ☐ |

---

## Automated Verification

```bash
pytest tests/unit/test_preprocessor.py -v

python - <<'EOF'
from zomato_rec.data.index import build_index
import time

t0 = time.time()
index = build_index()
print(f"Load time: {time.time()-t0:.2f}s")
print(f"Rows: {len(index.get_all())}")
print(f"Locations: {len(index.get_locations())}")
print(f"Budget bands: {index.get_budget_ranges()}")
EOF
```

**Expected:**
- Row count ≈ 51,717
- Locations ≈ 93
- Warm load < 2s

---

## Field Normalization Test Matrix

| Input | Expected Output | Edge ID |
|-------|-----------------|---------|
| `"4.1/5"` | `4.1` | DATA-11 |
| `"-"` | `None` | DATA-10 |
| `"NEW"` | `None` | DATA-12 |
| `"1,200"` | `1200` | DATA-20 |
| `""` (cost) | `None` | DATA-21 |
| `"North Indian, Chinese"` | `["north indian", "chinese"]` | DATA-31 |
| `"Yes"` (online_order) | `True` | DATA-40 |

---

## Manual Checklist

- [ ] All P0 criteria pass
- [ ] Spot-check 5 random records for sensible normalized values
- [ ] Confirm Bangalore-only locations (no Delhi/Mumbai)
- [ ] Parquet file size reasonable (~tens of MB, not empty)

---

## Edge Cases to Spot-Check

| ID | Test |
|----|------|
| DATA-01 | Simulate network failure — error message actionable |
| DATA-14 | Count rows with `rating is None` — matches ~15% expectation |
| DATA-23 | Budget filter later excludes null-cost rows |
| DATA-60 | Confirm no non-Bangalore cities in location list |

---

## Sign-Off

| Field | Value |
|-------|-------|
| Evaluator | |
| Date | |
| Result | ☐ Pass → proceed to Phase 2 &nbsp; ☐ Fail — blockers: |

**Notes:**
