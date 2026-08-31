# Scoring contract

The CLI computes a 100-point suitability score from seven researched features plus two evidence-derived features.

| Component | Weight | Input |
| --- | ---: | --- |
| Viral Momentum | 15 | `features.viral_momentum` |
| Hook | 15 | `features.hook` |
| Story / Twist | 10 | `features.story_twist` |
| Korean Gap | 15 | derived from `korean_gap.similar_results_count` |
| Explainability | 10 | `features.explainability` |
| Visual Clarity | 10 | `features.visual_clarity` |
| Source Traceability | 10 | derived from `source_trace.status` |
| Editability | 5 | `features.editability` |
| Entertainment Value | 10 | `features.entertainment_value` |

Every researched feature is an integer from `0` to `100` and requires a concrete reason. Entertainment Value measures amusement, satisfying surprise, visible oddity, shareable curiosity, or an enjoyable reveal; seriousness or fear alone does not qualify. Treat these as editorial inspection scores, not future-view predictions.

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

## Story-package score

`story_event` candidates also receive a separate renderer-package suitability score:

| Component | Weight |
| --- | ---: |
| Subject Recognition | 18 |
| Conflict / Abnormality | 15 |
| Payoff Clarity | 15 |
| Twist Strength | 12 |
| Asset Readiness | 12 |
| Freshness | 10 |
| Comment Signal | 8 |
| Evidence Strength | 6 |
| Korean Gap Opportunity | 4 |

Every manual component requires a concrete reason. The CLI combines the existing discovery score at 60% and package score at 40% only for `story_event` ranking. Keep both component scores visible; the combined `ranking_score` is a comparison aid, not a view prediction, factual verification, or renderer approval.

## Eligibility and output

A candidate is excluded when the post is not publicly inspectable, the content was not observed, it is not short-form or cleanly clippable, it has no exact public metric, it falls outside the requested discovery window, or rights are `not_permitted`.

The CLI deduplicates canonical URLs, normalized event-level `story_cluster_id` values, and normalized `content_fingerprint` values, keeps the higher-ranking record, and emits at most ten candidates. `--min-youtube` reserves slots for eligible YouTube candidates and reports any shortfall; it never makes an ineligible video eligible. Rights remain a separate field and never become publication-ready because a candidate scores well.
