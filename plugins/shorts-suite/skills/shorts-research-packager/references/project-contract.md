# Project contract

## Required structure

```text
<package-dir>/
├── project.json
├── source-graph.json
├── claim-sheet.json
├── asset-manifest.json
├── comments.json
├── story.json
├── timeline.json
├── narration.md
├── subtitles.srt
├── report.md
├── sources/
├── evidence/
├── assets/raw/
├── assets/derived/
├── comments/raw/
├── comments/production/
├── scenes/
└── review/
```

The initializer creates this structure from one selected `shortlist.json` candidate and refuses to overwrite a non-empty directory.

## Source graph

`source-graph.json.nodes[]` requires a unique `id`, public `url`, source type, publisher when known, timestamps, origin status, rights status, and evidence. `edges[]` connect node IDs without asserting an origin that the evidence does not establish.

## Claim sheet

`claim-sheet.json.claims[]` uses:

```json
{
  "id": "claim-001",
  "statement": "Exact supported statement",
  "status": "verified",
  "confidence": 0.92,
  "supporting_source_ids": ["source-001"],
  "contradicting_source_ids": [],
  "usable_in_narration": true,
  "notes": ""
}
```

Statuses are `verified`, `likely`, `unconfirmed`, `contradicted`, `opinion`, and `reaction_only`. Usable claims require at least one valid supporting source. A `reaction_only` record cannot be marked usable in narration.

## Asset manifest

`asset-manifest.json.assets[]` records:

```json
{
  "id": "asset-001",
  "type": "image",
  "source_ids": ["source-001"],
  "original_url": "https://example.com/image.jpg",
  "creator": "unknown",
  "collected_at": "2026-08-28T12:00:00+09:00",
  "sha256": "",
  "width": 1920,
  "height": 1080,
  "duration_seconds": null,
  "watermark_present": false,
  "derivation": "raw",
  "relevance": "The exact product named by claim-001.",
  "raw_path": "assets/raw/asset-001.jpg",
  "normalized_path": "assets/derived/asset-001/crop-9x16.png",
  "rights_status": "unreviewed"
}
```

Allowed rights values are `owned`, `licensed`, `permission_confirmed`, `public_domain`, `official_press_asset`, `transformative_review`, `unknown`, `unreviewed`, and `not_permitted`. Only the first five are rights-cleared states. Review-only values keep publication blocked.

## Comments

`comments.json.comments[]` records a valid `source_id`, text, visible metrics when available, capture time, selection reason, `claim_status: reaction_only`, raw context and element paths, and an anonymized `production_path`. A timeline may reference a comment only when the production file exists.

## Story and timeline

`story.json.narration_segments[]` requires a unique `id`, beat, text, and claim IDs. Factual segments may link only to `verified` and `likely` claims.

`timeline.json` is renderer-neutral. Each scene uses:

```json
{
  "id": "scene-001",
  "purpose": "hook",
  "duration_ms": 2400,
  "caption": "예상과 달랐던 공식 대응",
  "narration_segment_ids": ["narration-001"],
  "claim_ids": ["claim-001"],
  "source_ids": ["source-001"],
  "asset_ids": ["asset-001"],
  "comment_ids": [],
  "layout": {"fit": "cover", "position": "center"},
  "motion": {"type": "slow_zoom", "from": 1.0, "to": 1.08},
  "transition": "cut",
  "audio_cue": ""
}
```

Do not include renderer code or native project internals.

## Review and readiness

`project.json.reviews.facts_reviewed` and `rights_reviewed` become true only after explicit review. Handoff validation requires both, non-empty narration and scenes, subtitles, at least one used local asset, valid cross-file IDs, and no used `not_permitted` asset.

Successful handoff validation means the package is structurally ready for a renderer. It does not make the result publishable. `publish_ready` remains false and `publish_blocked` remains true.
