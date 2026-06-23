# Edge Cases

This document catalogs known edge cases for the **Zomato AI Restaurant Recommendation System**. Each entry describes the scenario, expected behavior, and which phase owns the fix or handling.

Use this alongside:
- [architecture.md](./architecture.md) — design and error-handling contracts
- [implementationPlan.md](./implementationPlan.md) — phase tasks and acceptance criteria
- [eval/](./eval/) — phase evaluation checklists

---

## How to Read This Document

| Column | Meaning |
|--------|---------|
| **ID** | Stable reference (e.g., `DATA-01`) |
| **Severity** | `Critical` — must handle; `High` — strong UX impact; `Medium` — degrades quality; `Low` — cosmetic or rare |
| **Phase** | Primary phase responsible |
| **Expected Behavior** | What the system should do |

---

## Phase 0 — Project Setup

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| SETUP-01 | Missing `.env` file | High | App starts with defaults where safe; fails fast with clear message if `OPENAI_API_KEY` required at runtime |
| SETUP-02 | Invalid env var types (e.g., `MAX_CANDIDATES=abc`) | High | Pydantic validation error on startup with field name |
| SETUP-03 | Partial `.env` (only some vars set) | Medium | Sensible defaults for optional vars; required vars documented in `.env.example` |
| SETUP-04 | Python version < 3.11 | High | Install fails or explicit version check with readable error |
| SETUP-05 | Editable install path issues | Medium | `pip install -e .` resolves `zomato_rec` imports from `src/` |
| SETUP-06 | Secrets committed to git | Critical | `.gitignore` blocks `.env`; no API keys in repo history |
| SETUP-07 | Missing optional dev dependencies | Low | Core app runs; test/lint tools fail with install hint |

---

## Phase 1 — Data Layer

### Dataset Loading

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| DATA-01 | Hugging Face download timeout / network failure | Critical | Retry with backoff; surface actionable error; document offline parquet fallback |
| DATA-02 | Dataset schema change (column renamed/removed) | High | Loader validates expected columns; fail with column diff in error |
| DATA-03 | Empty dataset returned | Critical | Abort preprocessing; log error; do not write empty cache |
| DATA-04 | Row count ≠ ~51,717 | Medium | Log warning; continue if within tolerance (e.g., ±5%) |
| DATA-05 | Duplicate `url` values | Medium | Stable `restaurant_id` from url hash; duplicates remain distinct rows if urls differ |
| DATA-06 | Missing `url` on row | High | Fall back to row-index-based ID; log count of fallback IDs |

### Rating (`rate`)

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| DATA-10 | Value `"-"` or empty | High | `rating = None` |
| DATA-11 | Format `"4.5/5"` | High | Parse to `4.5` |
| DATA-12 | Format `"NEW"` or non-numeric | High | `rating = None` |
| DATA-13 | Rating > 5 or < 0 | Medium | Clamp or set `None`; log anomaly |
| DATA-14 | ~15% rows missing rating (43942/51717) | High | Preprocessing completes; missing ratings excluded when min_rating filter applied |

### Cost (`approx_cost(for two people)`)

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| DATA-20 | Comma-separated `"1,200"` | High | Parse to `1200` |
| DATA-21 | Non-numeric / empty | High | `cost_for_two = None` |
| DATA-22 | Range strings `"300-400"` | Medium | Take lower bound, upper bound, or midpoint — document chosen rule |
| DATA-23 | Missing cost (~346 rows) | High | Row retained; excluded from budget filter when band applied |
| DATA-24 | Zero or negative cost | Medium | Treat as `None` or invalid |

### Cuisines & Text Fields

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| DATA-30 | Empty `cuisines` | High | `cuisines = []`; row still indexed |
| DATA-31 | Mixed casing `"North Indian, chinese"` | High | Normalize to lowercase for matching; preserve display casing separately if needed |
| DATA-32 | Extra whitespace `" North Indian , Chinese "` | High | Strip per token |
| DATA-33 | Single cuisine (no comma) | High | Single-element list |
| DATA-34 | Empty `dish_liked` | Medium | `popular_dishes = []` |
| DATA-35 | Very long `dish_liked` string | Low | Truncate for LLM context if passed downstream |

### Boolean Fields

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| DATA-40 | `online_order` = `"Yes"` / `"No"` | High | Map to `True` / `False` |
| DATA-41 | Missing or unexpected value | High | Default to `False` |
| DATA-42 | Case variants `"yes"`, `"YES"` | Medium | Case-insensitive mapping |

### Reviews

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| DATA-50 | `reviews_list` as Python-literal string tuples | High | Parse safely; extract text snippets |
| DATA-51 | Malformed review string | Medium | Skip row's reviews; `review_snippets = []` |
| DATA-52 | Extremely long review (>10k chars) | Medium | Keep only 2–3 snippets, each truncated (e.g., 200 chars) |
| DATA-53 | Review contains special chars / unicode | Medium | Preserve unicode; no encoding errors |

### Location & Geography

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| DATA-60 | User asks for `"Delhi"` or `"Mumbai"` | High | Not in dataset; rejected at API/UI with Bangalore-only guidance |
| DATA-61 | Location string with trailing spaces | High | Strip during preprocessing |
| DATA-62 | Same restaurant name, multiple branches | Medium | Treat as separate records (different urls/locations) |
| DATA-63 | `location` vs `listed_in(city)` mismatch | Medium | Filter on `location` field consistently; document which field is canonical |

### Cache & Index

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| DATA-70 | Corrupt parquet cache | High | Detect on read failure; re-download and rebuild |
| DATA-71 | Stale cache after code change | Medium | Version stamp in cache metadata or rebuild flag |
| DATA-72 | `data/processed/` not writable | High | Clear error; suggest permissions fix |
| DATA-73 | Budget percentile with too few valid costs | Medium | Fallback to fixed rupee bands documented in metadata |

---

## Phase 2 — Filtering

### Location Filter

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| FILT-01 | Case mismatch `"indiranagar"` vs `"Indiranagar"` | High | Case-insensitive match |
| FILT-02 | Unknown location string | High | API returns 422 with closest valid locations |
| FILT-03 | Empty location string | High | 422 validation error |
| FILT-04 | Location with special characters | Medium | Exact match after normalization only |

### Cuisine Filter

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| FILT-10 | Partial match `"Indian"` → `"North Indian"` | High | Substring match on normalized cuisine tokens |
| FILT-11 | Cuisine not in dataset (e.g., `"Ethiopian"`) | High | Empty candidates + `relaxation_note` |
| FILT-12 | Multi-word cuisine `"Fast Food"` | High | Match as substring or token per design |
| FILT-13 | Empty cuisine string | High | 422 validation error |

### Rating Filter

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| FILT-20 | `min_rating = 0` | Medium | Include all rated restaurants |
| FILT-21 | `min_rating = 5.0` | High | Very few results; valid empty or small set |
| FILT-22 | Restaurant with `rating = None` | High | Excluded when min_rating filter active |
| FILT-23 | Floating point boundary `4.0` vs `3.999` | High | Use `>=` comparison |

### Budget Filter

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| FILT-30 | Restaurant missing `cost_for_two` | High | Excluded from budget-filtered results |
| FILT-31 | Cost exactly on percentile boundary | Medium | Document inclusive/exclusive bounds consistently |
| FILT-32 | All three bands empty for a location+cuisine combo | High | Empty result + relaxation suggesting lower rating or different budget |
| FILT-33 | User selects `low` but wants premium spot | Medium | LLM may explain trade-off in Phase 3; hard filter still applies |

### Boolean Filters

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| FILT-40 | `online_order=True` filters out most rows | Medium | Valid small set; empty state if none |
| FILT-41 | Both `online_order` and `book_table` required | Medium | AND logic; may sharply reduce candidates |
| FILT-42 | `null` vs `False` for optional toggles | High | Only filter when explicitly `True` |

### Ranker & Candidate Cap

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| FILT-50 | 500+ matches after filters | High | Return exactly `MAX_CANDIDATES` (20), highest rated first |
| FILT-51 | Tie on rating | Medium | Break tie by `votes DESC` |
| FILT-52 | Tie on rating and votes | Low | Stable secondary sort (e.g., name or id) |
| FILT-53 | All candidates have `rating = None` but passed other filters | High | Rank by votes; document behavior |
| FILT-54 | Fewer than 5 matches | High | Pass all to LLM (no padding with unrelated rows) |
| FILT-55 | Zero matches | Critical | Empty list + actionable `relaxation_note` |

### Overly Strict Combinations

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| FILT-60 | Koramangala + rare cuisine + high budget + 4.8 min + book_table | High | Empty result; suggest which filter to relax first |
| FILT-61 | Valid location, impossible rating for that area | Medium | Empty result with rating relaxation hint |

---

## Phase 3 — LLM Layer

### Prompt Construction

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| LLM-01 | `additional_preferences` empty | Medium | Omit or mark "None"; prompt still valid |
| LLM-02 | `additional_preferences` > 500 chars | High | Truncate with ellipsis before prompt |
| LLM-03 | Prompt injection in free text ("ignore instructions…") | High | Truncate length; system prompt resists; no code execution |
| LLM-04 | Unicode / emoji in preferences | Medium | Pass through safely in UTF-8 |
| LLM-05 | Candidate with all null optional fields | Medium | Include in JSON with nulls; LLM still ranks |
| LLM-06 | 20 candidates × long review snippets | High | Snippet truncation keeps prompt under token budget |

### LLM API

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| LLM-10 | Missing `OPENAI_API_KEY` | Critical | Clear error at call time; tests use mock |
| LLM-11 | API rate limit (429) | High | Retry once with backoff; then fallback |
| LLM-12 | API timeout (>30s) | High | Fallback to deterministic ranking; log timeout |
| LLM-13 | API returns 5xx | High | Retry once; fallback on second failure |
| LLM-14 | Empty LLM response | High | Trigger repair retry, then fallback |
| LLM-15 | LLM returns markdown-wrapped JSON | High | Strip fences in parser before JSON load |

### LLM Output / Parser

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| LLM-20 | Valid JSON but unknown `restaurant_id` | Critical | Drop invalid entries; fallback if too few remain |
| LLM-21 | LLM invents restaurant not in candidates | Critical | Rejected by ID validation; never shown to user |
| LLM-22 | LLM returns wrong rating in explanation text | Medium | Display rating from dataset; explanation text allowed to paraphrase |
| LLM-23 | Duplicate ranks (two `rank: 1`) | High | Dedupe; renumber sequentially |
| LLM-24 | Missing `summary` field | Medium | Default summary from template |
| LLM-25 | Fewer than 5 recommendations returned | Medium | Accept partial list if IDs valid |
| LLM-26 | More than 5 recommendations | Medium | Trim to `max_results` |
| LLM-27 | Malformed JSON | High | Repair retry once → fallback |
| LLM-28 | JSON with trailing commas / comments | Medium | Parser tolerant or repair retry |
| LLM-29 | LLM returns same ID twice | High | Dedupe; keep first occurrence |

### Fallback Path

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| LLM-30 | Fallback triggered | High | Top N from pre-LLM ranker; generic explanations; `fallback_used` logged |
| LLM-31 | Fallback with 1–2 candidates only | Medium | Return available count without inventing more |
| LLM-32 | Repair retry succeeds after initial failure | Medium | Use repaired response; no fallback flag |

### Soft Preferences

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| LLM-40 | "Family-friendly" (not in structured data) | Medium | LLM infers from rest_type, reviews; notes uncertainty |
| LLM-41 | Conflicting soft prefs ("quick" + "fine dining") | Medium | LLM acknowledges trade-off in summary |
| LLM-42 | Soft pref impossible for all candidates | Medium | `relaxation_note` explains compromise |

---

## Phase 4 — API & Orchestration

### Request Validation

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| API-01 | Missing required field in POST body | High | 422 with field errors |
| API-02 | Invalid JSON body | High | 422 |
| API-03 | `min_rating` out of range (6.0, -1) | High | 422 |
| API-04 | `budget` not in low/medium/high | High | 422 |
| API-05 | `max_results` > 10 or < 1 | High | 422 |
| API-06 | Extra unknown fields in body | Low | Ignore (Pydantic default) or reject per config |

### Endpoint Behavior

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| API-10 | `GET /health` before index loaded | Medium | Return degraded status or wait for lifespan complete |
| API-11 | Concurrent recommendation requests | Medium | Handle safely; shared read-only index |
| API-12 | Very rapid repeated requests | Low | Optional rate limit; no crash |
| API-13 | Metadata endpoints during startup | Medium | 503 or block until index ready |

### Response Contract

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| API-20 | Empty recommendations | High | 200 with `recommendations: []` and `relaxation_note` |
| API-21 | Partial LLM failure with fallback | High | 200 with results + internal flag logged |
| API-22 | `filters_applied` echo | Medium | Reflect actual filters for debugging/UI |
| API-23 | `candidate_count` vs returned count | Medium | `candidate_count` = pre-LLM filter count |

### Startup & Lifecycle

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| API-30 | Index build fails on startup | Critical | Process exits non-zero; log root cause |
| API-31 | Second startup uses warm cache | High | Load parquet < 2s |
| API-32 | Config change requires restart | Medium | Document; no hot reload of index |

---

## Phase 5 — UI (Streamlit)

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| UI-01 | API not running | High | Connection error message; no stack trace to user |
| UI-02 | API slow (>10s) | High | Loading spinner; optional timeout message |
| UI-03 | Empty recommendations | High | Show `relaxation_note`; suggest filter changes |
| UI-04 | Restaurant with `rating = None` in results | Medium | Display "No rating" or hide stars gracefully |
| UI-05 | Restaurant with `cost_for_two = None` | Medium | Display "Cost unavailable" |
| UI-06 | Very long explanation text | Low | Wrap text; no layout break |
| UI-07 | Metadata fetch fails on page load | High | Error banner; disable submit or use retry |
| UI-08 | User submits without selecting location | High | Client-side validation before API call |
| UI-09 | 422 from API (invalid location) | High | Show validation message from API |
| UI-10 | Streamlit rerun clears results | Medium | Acceptable v1 behavior; document or preserve via session state |
| UI-11 | Mobile/narrow viewport | Low | Layout remains readable (Streamlit default) |
| UI-12 | Special chars in restaurant name | Medium | Render correctly (unicode) |

---

## Phase 6 — Quality & Cross-Cutting

### Performance

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| PERF-01 | Cold dataset load | Medium | Complete < 30s |
| PERF-02 | Warm cache load | High | < 2s |
| PERF-03 | Filter on full index | High | < 100ms |
| PERF-04 | End-to-end with LLM | High | < 10s typical |

### Security

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| SEC-01 | API key in logs | Critical | Never log secrets |
| SEC-02 | Prompt injection via `additional_preferences` | High | Length limit + system prompt hardening |
| SEC-03 | Public deployment without rate limit | Medium | Document optional slowapi |

### Data Integrity / Grounding

| ID | Scenario | Severity | Expected Behavior |
|----|----------|----------|-------------------|
| GROUND-01 | LLM cites restaurant not in candidate set | Critical | Blocked by parser |
| GROUND-02 | Displayed rating ≠ dataset rating | Critical | Fact merge always wins |
| GROUND-03 | User cross-checks Zomato live site | Low | Historical 2019 data may differ; document in UI |

---

## Edge Case → Test Mapping

| Area | Primary Test File | Eval Doc |
|------|-------------------|----------|
| Data preprocessing | `tests/unit/test_preprocessor.py` | [eval/phase1-eval.md](./eval/phase1-eval.md) |
| Filtering | `tests/unit/test_filters.py` | [eval/phase2-eval.md](./eval/phase2-eval.md) |
| LLM parser | `tests/unit/test_parser.py` | [eval/phase3-eval.md](./eval/phase3-eval.md) |
| API | `tests/integration/test_recommendation_flow.py` | [eval/phase4-eval.md](./eval/phase4-eval.md) |
| UI | Manual checklist | [eval/phase5-eval.md](./eval/phase5-eval.md) |
| Full system | Demo script + audit | [eval/phase6-eval.md](./eval/phase6-eval.md) |

---

## Related Documents

- [problemStatement.md](./problemStatement.md)
- [architecture.md](./architecture.md)
- [implementationPlan.md](./implementationPlan.md)
- [eval/README.md](./eval/README.md)
