# Project contract

Projects live at `projects/shorts-suite/globalize/<YYYY-MM-DD>/<video-id>`. The CLI rejects path traversal and existing destinations except for a narrowly validated `transcript_pending` resume of the exact same video and URL. A project owns its source, claims, script, and asset plan; do not copy another project's evidence or assets automatically.

When invoked from an installed plugin cache, the CLI locates the nearest current workspace containing both `.agents/plugins/marketplace.json` and `plugins/shorts-suite`, then uses that workspace's `projects/shorts-suite/globalize` directory. `--projects-root` remains the explicit override.

## Commands

```text
doctor --json
discover [--limit 1..10]
init --url <shorts-url> [--transcript-file <authorized-utf8-path>]
score --project-dir <project-dir>
approve --project-dir <project-dir> --stage research|script --confirm
validate --project-dir <project-dir> --stage ingest|research|script|package
package --project-dir <project-dir>
```

`discover` is a read-only, one-time lookup of channel ID `UCbr855WAFQvAX-An7IcHFXg`'s `/shorts` tab. It defaults to three candidates, never writes a project, and always returns `selection_required: true` and `monitoring_enabled: false`. Only a selected candidate URL may be passed to `init`.

## Caption TLS and pending resume

Caption downloads always use a verifying SSL context. The Python default CA is preferred; if its CA file and directory are unavailable, the CLI may use an already installed `certifi` CA bundle. `doctor --json` exposes the selected `caption_tls.mode` and CA path. Missing trusted CA makes `ready` false; TLS verification must never be disabled.

An `init` retry can update an existing destination only when all of these are true:

- project status is `transcript_pending`;
- project ID, source video ID, and canonical Shorts URL match the request;
- `transcript.txt` exists and is empty;
- research, script, and preview approvals remain false; and
- a verified public caption or authorized transcript is now available.

The resume updates `project.json`, `source.json`, `source-analysis.json`, and `transcript.txt`. It does not reset research or content data. Any mismatch or non-pending state fails without overwriting files.

## Status values

Only these values are valid: `initialized`, `transcript_pending`, `ingested`, `researched`, `scored`, `review_required`, `script_drafted`, `script_approved`, `packaged`, `blocked`.

## Research files

`source-analysis.json` stores the functional source beats, event fields, ordered claim IDs, ordered beat roles, origin assessment, sensitive-topic assessment, and score inputs.

`sources.json` contains records like:

```json
{
  "id": "source-01",
  "url": "https://example.org/report",
  "title": "Canonical title",
  "publisher": "Publisher",
  "published_at": "2026-08-27",
  "source_type": "independent"
}
```

`source_type` is one of `official`, `primary`, or `independent`. `fact-sheet.json` contains stable claims with `id`, `statement`, `core`, `status`, `confidence`, and `source_ids`. Usable claim statuses are `confirmed` and source-backed `attributed`; `disputed` and `unknown` claims are blocked from English content.

## Score input

`global_score_input.features` uses the exact keys `visual_impact`, `curiosity`, `universal_understanding`, `korea_uniqueness`, `emotion`, `surprise`, and `freshness`. Each entry has a 0–100 score and an evidence-based reason. `global_score_input.penalties` uses the exact keys `korean_person_only`, `domestic_politics_context`, `background_knowledge_required`, `already_global_viral`, and `facts_unverifiable`, each with `applied` and `reason`.

The computed output is written to `global-score.json`; do not hand-edit it.

## English content

`content-en.json` must contain exactly three angles, five titles, and three hooks, plus selected IDs and `selection_reasons` for the chosen angle, title, and hook. `script_paragraphs` contains paragraph `id`, `text`, and usable `claim_ids`. The concatenated paragraph narration must match `script_text` and the ordered storyboard narration and contain 80–120 English words.

`storyboard.json` contains eight to ten scenes totaling 30–40 seconds. Every scene requires `id`, `role`, `narration`, `caption`, `highlight`, `duration_seconds`, and usable `claim_ids`. The nested `asset` object requires `type`, `preferred_source`, non-empty `search_queries`, `rights_status`, `status: "planned"`, and `asset_path: ""`.

Allowed asset types are `NEWS_IMAGE`, `PUBLIC_PHOTO`, `SOCIAL_POST`, `SCREENSHOT`, `BROLL`, `MAP`, `INFOGRAPHIC`, `AI_IMAGE`, and `TEXT_CARD`. Allowed preliminary rights states are `GREEN`, `YELLOW`, and `RED`; none of them substitutes for final asset clearance. The signal Short itself is not an allowed asset type.

## Originality

`originality.json` contains source/output claim orders, source/output beat orders, claim-order similarity, beat-order similarity, overall deterministic structure similarity, hook/payoff match flags, cross-language lexical status, semantic review, and the final decision. Overall structure similarity is the larger of the claim and beat LCS percentages. The CLI recomputes all deterministic results during validation; mismatched stored values fail validation.

## Package

After script approval, the CLI creates:

- `script_en.md`, `narration.txt`, `subtitles.srt`, `highlights.json`
- `scenes.json`, `assets.csv`, `asset-search.md`
- `capcut-manifest.json`

The manifest format is `global-short-v1`; media slots use `MEDIA_01` style IDs. Package files must contain no source media, TTS audio, rendered video, or CapCut draft. `preview_approved` remains false and `publish_blocked` remains true.
