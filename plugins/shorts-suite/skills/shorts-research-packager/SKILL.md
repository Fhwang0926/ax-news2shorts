---
name: shorts-research-packager
description: Turn one explicitly selected Shorts Discovery Candidate ID into a source-linked, renderer-neutral research package with claims, optional comment evidence, assets, narration, scenes, subtitles, and rights state. Use after discovery selection, not for automatic selection, rendering, upload, publication, or rights approval.
---

# 쇼츠 리서치 패키저

Build the evidence and editing handoff for one candidate that the user already selected. Keep discovery, deep research, renderer handoff, and publication as separate states.

## Start

Run the local preflight and initialize from the exact discovery artifact:

```text
python3 <plugin-root>/scripts/research_package.py doctor --json

python3 <plugin-root>/scripts/research_package.py init \
  --shortlist <shortlist.json> \
  --candidate-id <selected-candidate-id> \
  --project-dir <package-dir>
```

Do not initialize from an inferred or top-ranked candidate. Read [research-workflow.md](references/research-workflow.md) before collecting evidence. Read [project-contract.md](references/project-contract.md) before filling or validating package files.

## Workflow

1. Confirm that the Candidate ID was explicitly selected and exists once in the shortlist.
2. Initialize the package without overwriting an existing non-empty directory.
3. Verify only the selected event and its likely source trail. Prefer structured public sources first; use Browser or Computer Use when visible or interactive state must be checked. Do not build a duplicate browser MCP for ordinary page work.
4. Build `source-graph.json`, then separate verified facts, likely claims, unknowns, contradictions, opinions, and reactions in `claim-sheet.json`.
5. Collect only story-relevant assets. Preserve raw and derived files separately, record source IDs, hashes, watermarks, derivation, and rights state, and never remove attribution or bypass access controls.
6. Capture comments only when they add representative reaction, an official reply, or a research lead. Preserve contextual raw evidence and use an anonymized production derivative. Comments remain `reaction_only` unless independently verified through other sources.
7. Write narration segments whose factual statements link only to `verified` or `likely` claim IDs. Build a renderer-neutral `timeline.json` that links narration, claims, sources, assets, and optional comments.
8. Validate research readiness. Record fact and rights reviews only after the user actually reviews them, then validate renderer handoff readiness.
9. Stop at the package boundary. Do not render, upload, publish, schedule, decide rights, or treat local review as publication approval.

## Commands

```text
python3 <plugin-root>/scripts/research_package.py validate \
  --project-dir <package-dir> \
  --stage research

python3 <plugin-root>/scripts/research_package.py validate \
  --project-dir <package-dir> \
  --stage handoff
```

`handoff` requires source-linked usable claims, reviewed facts and rights, narration, scenes, subtitles, and real local files for every used asset and production comment capture. It still returns `publish_ready: false` and `publish_blocked: true`.

## Boundaries

- Rights `unknown`, `unreviewed`, or `transformative_review` may support a local review handoff only. They never establish final render or publication permission.
- A `not_permitted` asset may remain recorded for audit but cannot be used by the timeline.
- Do not store cookies, credentials, unrelated browsing history, private account data, or unnecessary personal identifiers.
- Do not bypass login, CAPTCHA, paywall, DRM, hotlink protection, region controls, or private-account restrictions.
- Do not copy another channel's voice, title wording, or visual identity. Generalize the observed story structure.
