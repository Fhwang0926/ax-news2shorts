# Scoring contract

The CLI computes a 100-point suitability score from six researched features plus two evidence-derived features.

| Component | Weight | Input |
| --- | ---: | --- |
| Viral Momentum | 20 | `features.viral_momentum` |
| Hook | 15 | `features.hook` |
| Story / Twist | 15 | `features.story_twist` |
| Korean Gap | 15 | derived from `korean_gap.similar_results_count` |
| Explainability | 10 | `features.explainability` |
| Visual Clarity | 10 | `features.visual_clarity` |
| Source Traceability | 10 | derived from `source_trace.status` |
| Editability | 5 | `features.editability` |

Every researched feature is an integer from `0` to `100` and requires a concrete reason. Treat these as editorial inspection scores, not future-view predictions.

## Derived values

Korean Gap:

- 0 similar Korean results: 100
- 1–3: 80
- 4–10: 50
- above 10: 20

Source Traceability:

- `verified_original`: 100
- `probable_original`: 70
- `repost_only`: 30
- `unknown`: 0

## Penalties

The CLI applies fixed deductions:

| Risk flag | Deduction |
| --- | ---: |
| `tv_film` | 25 |
| `sports_broadcast` | 20 |
| `source_unknown` | 15 |
| `korean_saturated` | 20 |
| `long_interview` | 10 |
| `promotional` | 10 |
| `context_misleading` | 15 |
| `sensitive` | 20 |

`source_unknown` is added automatically for an unknown source. `korean_saturated` is added automatically when more than ten similar Korean results are recorded. `not_permitted` rights are a hard exclusion rather than a deduction.

The result is:

```text
overall = max(0, weighted_component_score - total_penalty)
```

## Eligibility and output

A candidate is excluded when the post is not publicly inspectable, the content was not observed, it is not short-form or cleanly clippable, it has no exact public metric, it falls outside the requested discovery window, or rights are `not_permitted`.

The CLI deduplicates canonical URLs and normalized `content_fingerprint` values, keeps the higher-scoring record, and emits at most ten candidates. Rights remain a separate field and never become publication-ready because a candidate scores well.
