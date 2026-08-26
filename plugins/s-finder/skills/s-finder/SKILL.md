---
name: s-finder
description: Research current foreign-origin videos across YouTube Shorts, TikTok, Instagram Reels, X, and Reddit; trace probable originals, check Korean saturation, score Korean explainer-Shorts fit, and compare up to ten candidates. Use for overseas viral-source discovery, original-source comparison, Korean Gap checks, s-finder, or 쇼츠 후보 찾기 requests. Do not use for downloading, video production, uploading, rights clearance, or view guarantees.
---

# 쇼츠 후보 찾기

Find overseas video sources that are rising, visually understandable, and improved by concise Korean explanation. Return a research shortlist, not a finished content choice.

## Start

Run the local preflight before a research session:

```text
python3 <plugin-root>/scripts/s_finder.py doctor --json
```

Read [research-workflow.md](references/research-workflow.md) before discovering sources. Read [candidate-schema.md](references/candidate-schema.md) before recording candidates. Read [scoring.md](references/scoring.md) before ranking or explaining a result.

## Workflow

1. Accept a topic, one or more public video URLs, or a bare request. For a bare request, use a 48-hour window, return up to ten eligible candidates, and rotate across human skill, technology, unusual behavior, animals, food, transportation, and visually surprising events. Do not ask the user to restate these defaults.
2. Inspect current public evidence with the available browser or web-research surface. Search-result snippets are discovery leads, not final candidate evidence. Record a source as `blocked` or `unavailable` when it cannot be inspected; never bypass login, CAPTCHA, paywalls, region controls, or other access restrictions.
3. Verify the visible post, creator, publish time, exact public metrics, observable action, likely story pattern, probable source trail, Korean semantic matches, and current rights status. Keep claims at the level supported by the evidence.
4. Create a candidate JSON file using [candidate-schema.md](references/candidate-schema.md). Keep only minimal research metadata and links; do not retain cookies, account data, page dumps, or unrelated browsing history.
5. Validate and rank the evidence:

```text
python3 <plugin-root>/scripts/s_finder.py validate \
  --input <research-candidates.json> \
  --max-age-hours 48

python3 <plugin-root>/scripts/s_finder.py rank \
  --input <research-candidates.json> \
  --output-dir <research-output> \
  --max-age-hours 48 \
  --top-k 10
```

   For user-supplied older URLs, use `--max-age-hours 0` and label the result as a comparison rather than current discovery.
6. Present no more than ten eligible candidates. Include Candidate ID, canonical URL, visible metrics and capture time, observable action, score breakdown, Korean Gap evidence, source-trace status and confidence, rights status, risks, and why Korean narration adds value.
7. Stop for the user's Candidate ID. Never silently choose, download, script, render, schedule, or upload a candidate.

## Evidence and safety boundaries

- Prefer the earliest verifiable creator post, visible watermark or handle, explicit attribution, and consistent repost links. The oldest post found is only a clue; use `probable_original` unless authorship is actually verified.
- `unknown` and `repost_only` are valid source results. Never force a creator conclusion to improve the score.
- Korean captions, hashtags, or uploader names alone do not prove Korean saturation. Use Korean paraphrases and semantic matches, and preserve the queries and result links checked.
- Exact public counts must be recorded as integers with evidence. Do not convert vague labels, hashtag totals, or search snippets into candidate metrics.
- `owned`, `licensed`, and `permission_confirmed` require evidence. Otherwise keep rights `unknown`; `not_permitted` excludes a candidate.
- Rights `unknown` permits research and local review only. A ranking score does not establish reuse rights, fair use, monetization eligibility, future views, or publication readiness.
- Return fewer than ten candidates when the evidence is weak. Do not pad the shortlist or relax the time, source, or evidence gates without the user's direction.

## Scope

This MVP uses one research skill and one standard-library ranking CLI. It does not include platform API credentials, a database, a scheduler, a browser extension, media acquisition, vision analysis of every candidate, feedback learning, or the downstream Shorts production pipeline.
