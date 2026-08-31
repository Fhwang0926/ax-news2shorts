# Editorial and rights policy

## Fact evidence

The signal Short is not a fact source. A non-sensitive core claim requires at least two usable sources from different registrable host names. Syndicated copies, mirror pages, or multiple URLs under one domain do not count as independent sources.

Sensitive topics include death, accident, crime, politics, medicine, criticism of a named person, and corporate controversy. Each sensitive core claim requires:

- at least one official or primary source; and
- at least two additional independent sources; and
- at least three distinct source domains in total.

Every factual statement used by the English script or a scene must reference claim IDs whose status is `confirmed` or a source-backed `attributed` statement. `disputed` and `unknown` claims cannot be used.

## Global Potential Score

The positive dimensions are fixed: Visual 20, Curiosity 20, Universal 15, Korea Uniqueness 15, Emotion 10, Surprise 10, Freshness 10. Enter each dimension as an integer percentage from 0 to 100. The CLI converts it to the weighted score.

The fixed penalties are domestic-person dependency −20, domestic-political context −30, required background knowledge −15, earlier overseas viral evidence −40, and unverifiable facts −50. The total is clamped to 0–100.

Decision bands are `MAKE` 80–100, `REVIEW` 65–79, `HOLD` 50–64, and `SKIP` 0–49. `GLOBAL_REPOST` is always `SKIP`. `UNKNOWN` cannot be promoted above `REVIEW`.

## Originality guard

Claim-order and beat-order similarity each use the longest common subsequence divided by the longer corresponding array. Overall structure similarity is the larger of those two percentages. A value of 70% or more requires rewrite. A value of 60% or more also requires rewrite when hook and payoff functions both match.

Korean-to-English lexical overlap is recorded as `not_applicable_cross_language`; it must not be converted into a meaningless token-overlap score. Codex must separately review semantic similarity of the hook, conclusion, reveal order, analogies, and phrasing. Packaging requires `semantic_review.decision: PASS` and a meaningful note.

## Rights boundary

Do not download or package the source video, its audio, thumbnails, screenshots, captions, creator branding, or any third-party media. An asset search query is not a license. Keep paths empty and asset status `planned`; record the preliminary rights state separately as `GREEN`, `YELLOW`, or `RED`. Later asset selection must independently establish provenance, permitted use, required attribution, and synthetic-media disclosure.

Do not bypass access controls, use cookies or logged-in sessions, remove watermarks, or claim publication readiness. A generated package is an editorial handoff, not a rights clearance or upload authorization.
