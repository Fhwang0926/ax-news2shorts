---
name: shorts-discovery
description: Research entertaining current public video signals and story events across YouTube Shorts, other short-video platforms, social networks, news, official pages, and communities, optionally using YouTube Data API metadata as leads; trace probable originals, check Korean saturation, and compare up to ten Korean explainer-Shorts candidates. Use for fun-first discovery and Korean Gap checks, then hand an explicitly selected Candidate ID to Shorts Research Packager; not for automatic selection, rendering, upload, or rights clearance.
---

# 쇼츠 후보 찾기

Find public video signals or story events that are rising, entertaining, explainable, and improved by concise Korean narration. Return a research shortlist, not a finished content choice.

## Start

Run the local preflight before a research session:

```text
python3 <plugin-root>/scripts/discover.py doctor --json
```

Read [research-workflow.md](references/research-workflow.md) before discovering sources. Read [candidate-schema.md](references/candidate-schema.md) before recording candidates. Read [scoring.md](references/scoring.md) before ranking or explaining a result.

When the user asks to include Google YouTube API, read [youtube-data-api.md](references/youtube-data-api.md). Treat API results as discovery leads that still require browser content and source verification.

## Workflow

1. Accept a topic, one or more public URLs, or a bare request. For a bare request, use a 48-hour window and return up to ten eligible candidates. Default to fun-first discovery: prefer amusing corporate behavior, surprising demonstrations, absurd internet incidents, satisfying corrections, strong visual reveals, and recognizable subjects. Unless the user asks for security coverage, include no more than two breach, vulnerability, geopolitical, regulatory, or other heavy candidates. Do not ask the user to restate these defaults.
2. Always inspect YouTube during current or bare discovery. Prefer YouTube Data API leads when configured; otherwise search the public YouTube Shorts surface in the browser. Aim to qualify at least three YouTube candidates and disclose the exact shortfall when fewer pass. Then check the other requested platforms. Search snippets and API metadata are discovery leads, not proof of visible action, original authorship, or rights. Record a source as `blocked` or `unavailable` when it cannot be inspected; never bypass login, CAPTCHA, paywalls, region controls, or other access restrictions.
3. Classify each candidate as `video_signal` or `story_event`. Verify the visible post, creator or publisher, publish time, exact public metrics, observable action or event, likely story pattern, probable source trail, Korean semantic matches, packaging readiness, and current rights status. Keep claims at the level supported by the evidence.
4. Create a candidate JSON file using [candidate-schema.md](references/candidate-schema.md). Keep only minimal research metadata and links; do not retain cookies, account data, page dumps, or unrelated browsing history.
5. Validate and rank the evidence:

```text
python3 <plugin-root>/scripts/discover.py validate \
  --input <research-candidates.json> \
  --max-age-hours 48

python3 <plugin-root>/scripts/discover.py rank \
  --input <research-candidates.json> \
  --output-dir <research-output> \
  --max-age-hours 48 \
  --top-k 10 \
  --min-youtube 3
```

   For user-supplied older URLs, use `--max-age-hours 0` and label the result as a comparison rather than current discovery.
6. Present no more than ten eligible candidates. Include Candidate ID, canonical URL, visible metrics and capture time, observable action, entertainment score and reason, score breakdown, Korean Gap evidence, source-trace status and confidence, rights status, risks, and why Korean narration adds value. State the YouTube eligible count and shortfall.
7. Stop for the user's Candidate ID. Never silently choose, download, script, render, schedule, or upload a candidate. When the user explicitly selects an ID and asks to continue, hand the exact shortlist and selected ID to `$shorts-research-packager`.

## Evidence and safety boundaries

- Prefer the earliest verifiable creator post, visible watermark or handle, explicit attribution, and consistent repost links. The oldest post found is only a clue; use `probable_original` unless authorship is actually verified.
- `unknown` and `repost_only` are valid source results. Never force a creator conclusion to improve the score.
- Korean captions, hashtags, or uploader names alone do not prove Korean saturation. Use Korean paraphrases and semantic matches, and preserve the queries and result links checked.
- Exact public counts must be recorded as integers with evidence. Do not convert vague labels, hashtag totals, or search snippets into candidate metrics.
- YouTube Data API may establish public title, channel, publication time, duration, views, likes, and comments at the collection time. It does not establish the visible action, Shorts classification, source ownership, media rights, or Korean Gap; verify those separately.
- `owned`, `licensed`, and `permission_confirmed` require evidence. Otherwise keep rights `unknown`; `not_permitted` excludes a candidate.
- Rights `unknown` permits research and local review only. A ranking score does not establish reuse rights, fair use, monetization eligibility, future views, or publication readiness.
- Return fewer than ten candidates when the evidence is weak. Do not pad the shortlist or relax the time, source, or evidence gates without the user's direction.
- A dry but important incident is not automatically entertaining. Deprioritize it unless the audience can understand the oddity, reversal, or consequence in one sentence and the package has strong visuals.

## Scope

This role uses one research skill and one standard-library CLI. YouTube Data API credentials are optional and limited to public metadata reads. It does not include OAuth account access, a database, a scheduler, a browser extension, media acquisition, vision analysis of every candidate, feedback learning, rendering, or upload. Selected-candidate evidence and renderer-neutral packaging belong to `$shorts-research-packager`.
