# Phase Evaluation Guides

Each phase has an **`eval.md`** checklist used to decide whether that phase is complete before moving to the next.

| Phase | Document | Focus |
|-------|----------|-------|
| 0 | [phase0-eval.md](./phase0-eval.md) | Project setup & configuration |
| 1 | [phase1-eval.md](./phase1-eval.md) | Data loading, preprocessing, index |
| 2 | [phase2-eval.md](./phase2-eval.md) | Filtering & candidate selection |
| 3 | [phase3-eval.md](./phase3-eval.md) | LLM prompts, parsing, fallback |
| 4 | [phase4-eval.md](./phase4-eval.md) | FastAPI & orchestration |
| 5 | [phase5-eval.md](./phase5-eval.md) | Streamlit UI |
| 6 | [phase6-eval.md](./phase6-eval.md) | Quality, tests, docs, v1 sign-off |

## Evaluation Levels

| Level | Meaning |
|-------|---------|
| **Must Pass (P0)** | Blockers — phase cannot be signed off |
| **Should Pass (P1)** | Important quality bar — fix before v1 if possible |
| **Nice to Have (P2)** | Optional polish |

## Sign-Off Process

1. Complete all tasks in [implementationPlan.md](../implementationPlan.md) for the phase.
2. Run automated checks listed in the phase `eval.md`.
3. Complete manual verification checklist.
4. Review relevant edge cases in [edgecase.md](../edgecase.md).
5. Mark phase checklist complete and proceed to next phase.
