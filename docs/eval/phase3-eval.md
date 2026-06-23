# Phase 3 Evaluation — LLM Layer

**Phase:** 3 — LLM Layer  
**Depends on:** Phase 2  
**Blocks:** Phase 4  
**Implementation plan:** [§ Phase 3](../implementationPlan.md#phase-3--llm-layer)  
**Edge cases:** [LLM-*](../edgecase.md#phase-3--llm-layer)

---

## Objective

Verify prompts are grounded, LLM responses parse correctly, factual fields merge from the dataset, and failures degrade to deterministic fallback without crashing.

---

## Prerequisites

- Phase 2 signed off
- `OPENAI_API_KEY` set for live LLM tests (optional if mock-only eval)
- Mock LLM fixture in `tests/conftest.py`

---

## Evaluation Criteria

### P0 — Must Pass

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E3.1 | LLM client implements async `complete()` protocol | Code review | ☐ |
| E3.2 | System prompt forbids inventing restaurants | Prompt review | ☐ |
| E3.3 | User prompt includes preferences + candidate JSON with IDs | Prompt snapshot test | ☐ |
| E3.4 | Parser validates every `restaurant_id` against candidate set | Unit test unknown ID | ☐ |
| E3.5 | Display fields sourced from `RestaurantRecord`, not LLM | Compare parsed output to dataset | ☐ |
| E3.6 | Unknown IDs dropped or trigger fallback | LLM-20 test | ☐ |
| E3.7 | Malformed JSON → repair retry → fallback | LLM-27 test | ☐ |
| E3.8 | Fallback returns top N with generic explanations | Mock failure test | ☐ |
| E3.9 | `additional_preferences` truncated to 500 chars | LLM-02 test | ☐ |
| E3.10 | LLM timeout respected (`LLM_TIMEOUT_SECONDS`) | Mock slow response | ☐ |
| E3.11 | Unit tests pass | `pytest tests/unit/test_parser.py -v` | ☐ |
| E3.12 | Integration test with mocked LLM passes | `pytest tests/integration/test_recommendation_flow.py -v` | ☐ |

### P1 — Should Pass

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E3.13 | Duplicate ranks deduplicated | LLM-23 test | ☐ |
| E3.14 | Duplicate IDs deduplicated | LLM-29 test | ☐ |
| E3.15 | Markdown-fenced JSON stripped before parse | LLM-15 test | ☐ |
| E3.16 | Partial list (<5) accepted when IDs valid | LLM-25 test | ☐ |
| E3.17 | `relaxation_note` populated when soft prefs unmet | Manual LLM test | ☐ |
| E3.18 | API rate limit triggers retry then fallback | LLM-11 mock | ☐ |
| E3.19 | `fallback_used` flag logged | Log inspection | ☐ |
| E3.20 | Live LLM call returns valid JSON (1 smoke test) | Real API call | ☐ |

### P2 — Nice to Have

| # | Criterion | How to Verify | Pass |
|---|-----------|---------------|------|
| E3.21 | Token estimate logged per request | Log inspection | ☐ |
| E3.22 | Prompt injection string handled safely | LLM-03 test | ☐ |
| E3.23 | Provider swappable via config | Code review | ☐ |

---

## Automated Verification

```bash
pytest tests/unit/test_parser.py -v
pytest tests/integration/test_recommendation_flow.py -v
```

---

## Parser Test Matrix

| Input | Expected | Edge ID |
|-------|----------|---------|
| Valid JSON with known IDs | Merged recommendations | — |
| Unknown `restaurant_id` | Rejected / fallback | LLM-20 |
| Duplicate `rank: 1` | Renumbered | LLM-23 |
| Invalid JSON | Repair → fallback | LLM-27 |
| Empty LLM response | Fallback | LLM-14 |
| ```json ... ``` wrapped | Parsed after strip | LLM-15 |

---

## Grounding Audit (Phase 3 Mini)

Run one live recommendation and verify:

| Check | Pass |
|-------|------|
| Every returned `name` exists in candidate set | ☐ |
| Every `rating` matches dataset record | ☐ |
| Every `cost_for_two` matches dataset record | ☐ |
| No restaurant appears that was not in filtered candidates | ☐ |

---

## Manual Checklist

- [ ] All P0 criteria pass
- [ ] System prompt reviewed for Bangalore scope and JSON-only output
- [ ] Fallback path tested by forcing parser failure
- [ ] Mock LLM used in CI; live LLM optional locally

---

## Edge Cases to Spot-Check

| ID | Test |
|----|------|
| LLM-01 | Missing API key — clear error |
| LLM-21 | Invented restaurant name in JSON with fake ID — blocked |
| LLM-40 | "Family-friendly" in additional_preferences — explanation references reviews/type |
| LLM-30 | Full fallback path returns usable results |

---

## Sign-Off

| Field | Value |
|-------|-------|
| Evaluator | |
| Date | |
| Result | ☐ Pass → proceed to Phase 4 &nbsp; ☐ Fail — blockers: |

**Notes:**
