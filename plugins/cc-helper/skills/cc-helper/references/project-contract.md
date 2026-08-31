# Project and CLI contract

## Commands

```text
python3 <plugin-root>/scripts/cc_helper.py doctor --json

python3 <plugin-root>/scripts/cc_helper.py init \
  --title "<selected issue title>" \
  --candidate-id "<candidate-id>" \
  --category "<category>" \
  --source-url "<canonical-source-url>"

python3 <plugin-root>/scripts/cc_helper.py collect-assets \
  --project-dir "<project-dir>" \
  --source-url "<canonical-page-url>" \
  --list-only

python3 <plugin-root>/scripts/cc_helper.py collect-assets \
  --project-dir "<project-dir>" \
  --source-url "<canonical-page-url>" \
  --asset-url "<selected-image-or-video-url>" \
  --community-capture

python3 <plugin-root>/scripts/cc_helper.py compose-readable-source \
  --source-file "<source-image>" \
  --output-file "<readable-card.png>" \
  --panel "source_x,source_y,width,height:target_x,target_y,width,height"

python3 <plugin-root>/scripts/cc_helper.py review-asset \
  --project-dir "<project-dir>" \
  --asset-id "<asset-id>" \
  --evidence-role incident_evidence \
  --fact-id "<fact-id>" \
  --content-description "<what is visibly shown>" \
  --approve-content --approve-quality \
  --main-subject-visible --crop-safe \
  --display-focus source_text --preview-checked \
  --evidence-readable --visual-anchor-term "<visible source phrase>"

python3 <plugin-root>/scripts/cc_helper.py validate \
  --project-dir "<project-dir>" \
  --stage assets

python3 <plugin-root>/scripts/cc_helper.py prepare-capcut \
  --project-dir "<project-dir>" \
  --dry-run

python3 <plugin-root>/scripts/cc_helper.py clone-capcut \
  --project-dir "<project-dir>" \
  --confirm

python3 <plugin-root>/scripts/cc_helper.py retime-capcut \
  --project-dir "<project-dir>" \
  --confirm-existing

python3 <plugin-root>/scripts/cc_helper.py validate \
  --project-dir "<project-dir>" \
  --stage capcut
```

`collect-assets` also accepts `--local-file`. Known Korean community hosts automatically select `community-capture-safe`; use `--community-capture` for another community host or a local community screenshot. The safe mode fits the complete original inside a centered 1000×1056 maximum foreground box so the CapCut template cannot cut its edges. Recollecting an existing matching image in safe mode replaces only its normalized PNG and resets its quality/readability review. Add `--synthetic --text-free --derived-from <asset-id>` for an inspected image-generation result. `--text-free` confirms that the image contains no editorial copy, dates, labels, source notes, logos, pseudo-text, or watermarks. The source original and generated result remain separate manifest records.

For a public-figure `editorial_animation` in `obvious-editorial-eye-band` mode, `review-asset` also requires `--people-visible --people-treatment editorial_animation`, `--portrait-style-strength obvious-editorial`, `--portrait-eye-motif editorial-ruler-eye-band`, `--approve-identity --approve-clothing --approve-context`, `--approve-style-obvious --approve-eye-motif --approve-ruler-ticks`, and `--confirm-eye-motif-editorial-only`. That last confirmation means the eye-band has no anonymizing or rights-clearing effect.

## Required files

`research.json` contains one to three candidates, one selected Candidate ID, canonical sources, and facts whose `source_ids` resolve to those sources. A direct user topic is initialized as `direct-topic` but still needs at least one source-linked fact before asset validation.

`project.json.youtube_upload_mode` is `copy-handoff` for new projects. Missing mode preserves legacy handoff behavior. `project.json.youtube_upload` contains the copy-only YouTube handoff:

```json
{
  "status": "copy_ready",
  "title": "1-100 characters",
  "description": "1-5000 characters",
  "hashtags": ["#one", "#to", "#five"],
  "tags": ["one to fifteen search tags without #"],
  "pinned_comment": "1-500 characters",
  "category": "people_and_blogs | news_and_politics | entertainment | sports",
  "language": "ko",
  "audience": "made_for_kids | not_made_for_kids",
  "altered_content": true,
  "altered_content_reason": "required when true",
  "recommended_visibility": "private | unlisted | public",
  "thumbnail": {"white": "", "yellow": ""},
  "source_ids": ["source-01"]
}
```

The thumbnail lines must exactly match `storyboard.title`. Source IDs must resolve in `research.json`. A `publish_blocked: true` project must recommend `private`. These values generate `handoff/youtube-upload.json` and `handoff/youtube-upload.md`; they never initiate an upload.

`storyboard.json` contains:

- `message`: the one-sentence video point.
- `title.white` and `title.yellow`: fixed top title lines, each at most 16 characters.
- `beats`: 7–10 objects with unique `id` and spoken `narration`.
- `scenes`: exactly 15 sequential `scene-01` through `scene-15` objects.
- `pacing_mode`: new projects use `narration-hold`; missing means legacy behavior.
- `narration_flow_mode`: new projects use `conversational-chain`; missing means legacy behavior. Each beat also records `flow_role` in nondecreasing `hook → setup → trigger → explanation → reaction → response → consequence → resolution → aftermath` order. The first role is `hook`, the sequence includes `trigger` and `resolution`, and the final role is `resolution` or `aftermath`.
- `caption_sync_mode`: new projects use `clause`; missing keeps legacy caption validation.
- `visual_validation_mode`: new projects use `evidence-first`; missing keeps legacy visual validation.
- `display_validation_mode`: new projects use `short-preview`; missing keeps legacy display validation.
- `final_visual_review_mode`: new projects use `player-check`; missing keeps legacy final-review behavior.
- `person_visual_mode`: new projects use `stylize-or-remove`; missing keeps legacy person handling.
- `public_figure_style_mode`: new projects use `obvious-editorial-eye-band`; missing keeps legacy public-figure styling.
- `person_motion_mode`: new projects use `subtle-deterministic`; missing keeps static visuals.
- `narration_performance_mode`: new projects use `reviewed-external`; missing keeps the legacy narration handoff.

Beat and scene narration use casual friend-explainer Korean. Asset validation rejects formal `합니다` or `했습니다` sentence endings, adjacent `~데/~는데` beat endings, and a final `~함 → ~함` pair. Narration may use interpretation, inferred intent, exaggeration, metaphor, and slang without direct factual confirmation; sourced facts remain recorded separately in `research.json`.

Each scene contains `beat_id`, `role`, `duration`, `narration`, `caption`, optional `caption_anchor`, `fact_ids`, `visual_requirement`, `asset_id`, `source_label`, and optional `sfx`. `visual_requirement` is one of `direct_incident`, `direct_subject`, `contextual`, or `symbolic_allowed`; it is intentionally independent of structural `role`. Legacy projects keep distinct assets and 1–4 second scenes. Narration-hold projects allow 1–7 second scenes, require every beat to appear once as a contiguous run of one to three slots, and require every slot in that run to use the same asset. Cross-beat and non-contiguous repeats are rejected. Scenes 2–15 require a lower caption.

With `caption_sync_mode: clause`, scenes 2–15 require a non-empty alphanumeric opening `caption_anchor` found within the first two narration words, and the caption must begin with it. The caption's final normalized word must equal the narration clause's final normalized word so spoken connectives and endings are retained. Scene 1 keeps both caption and anchor empty. Joining the scene narration clauses for each beat must reproduce the beat narration after punctuation and whitespace normalization. Caption durations under 1.3 seconds or over 3.2 seconds warn; over 4.5 seconds fails.

When `project.json.narration_audio.path` exists, `handoff/narration-timing.json` is required. It records `source: capcut_waveform_review | typecast_timestamp_review`, the WAV path, SHA-256 and measured duration, plus ordered gapless `beats` and 15 `scenes` with start/end seconds. Every same-beat follower scene also records `onset_policy: strong_speech`, a `spoken_prefix` present at the start of both narration and caption, measured `strong_speech_onset_seconds`, and `frame_rate: 30`; its selected start must be within one frame of that measured onset. The final structural scene must end within 0.15 seconds of the WAV and exactly at `narration_audio.capcut_duration_us`.

With `narration_performance_mode: reviewed-external`, `handoff/narration-performance.json` is also required. cc-helper does not create Typecast audio; it validates an externally generated WAV and its review evidence. The file uses `source: external_tts_review` and binds the current `handoff/narration-typecast.txt`, narration WAV, and `handoff/narration-timing.json` by relative path and SHA-256. `storyboard_narration_sha256` separately binds every beat ID and narration string so changing the spoken story invalidates the audio review even when pronunciation-oriented Typecast text differs. Its `beats` list must exactly follow every storyboard beat ID; the current Park Wi package therefore has 10 rows. Each row records `emotion_type: smart | preset`, optional `emotion_preset: normal | toneup | tonedown`, `tempo`, `pause_after_seconds`, and `measured_pause_after_seconds`. Validation derives the actual pause again from the WAV at -40 dB with a 0.08-second minimum; tempo must be 0.90–1.10, every non-final pause must be 0.12–0.40 seconds and differ from its plan by no more than 0.10 seconds, the recorded measurement must match the WAV within 0.04 seconds, and the final pause must be zero.

The same performance file records loudness, true peak, silence thresholds, and a `listening_review` bound to the three file hashes plus the storyboard-narration hash. Validation re-measures the current WAV and requires -18 to -14 integrated LUFS with true peak at or below -1 dBTP. A `reviewer_kind: automated` record may use `status: automated_reviewed` only for profile variation, measured pauses, timestamp alignment, loudness, and true peak; it produces a human-listening warning. A `reviewer_kind: human` record uses `status: approved` and must approve `naturalness`, `dynamics`, `breathing`, `pronunciation`, `pace`, and `no_audio_artifacts`. Replacing the script, audio, timing, or storyboard narration invalidates the review.

`asset-manifest.json` stores source page URL, direct asset URL, retrieval time, SHA-256, original dimensions, source and normalized paths, `normalization_mode`, media type, synthetic state, derivation, person class, relevance, `visual_text`, and `rights_status`. Community images use `normalization_mode: community-capture-safe`; asset validation rejects a known community image that was normalized as an ordinary fill/crop. Evidence-first records add:

```json
{
  "evidence_role": "incident_evidence | official_evidence | source_capture | source_photo | context | editorial_animation | non_identifying_fallback | unreviewed",
  "review": {
    "content": "approved | review_required",
    "quality": "approved | review_required",
    "reviewed_at": "",
    "asset_sha256": "",
    "fact_ids": [],
    "content_description": "",
    "main_subject_visible": false,
    "crop_safe": false,
    "non_identifying": false,
    "people_visible": false,
    "people_treatment": "none_visible | editorial_animation | cropped_out | non_identifying",
    "display_focus": "subject | source_text | mixed",
    "preview_checked": false,
    "evidence_readable": false,
    "visual_anchor_terms": [],
    "normalized_sha256": ""
  },
  "fallback_reason": "",
  "portrait_style": "",
  "portrait_style_strength": "",
  "portrait_eye_motif": "",
  "portrait_review": {
    "identity_preserved": false,
    "clothing_preserved": false,
    "context_preserved": false,
    "style_obvious_at_preview": false,
    "eye_motif_present": false,
    "ruler_ticks_visible": false,
    "eye_motif_editorial_only": false
  }
}
```

Every CapCut-selected evidence-first asset needs approved content and quality review whose SHA-256 matches the current source file and whose fact IDs cover the scene. The manifest also records normalization strategy, foreground box and width/height/area ratios, and normalized PNG SHA-256. `short-preview` rejects undersized foregrounds and invalidates review when the normalized bytes change. General visuals require 55% width, 28% height, and 22% area; `source_text` or `mixed` additionally require 35% height and 30% area plus readable anchor terms. Genuine low-resolution evidence warns but remains usable only when these final-size rules pass. Synthetic assets cannot claim incident, official, or source-capture roles. A `source_photo` is provenance-only. Under `stylize-or-remove`, a visible public-figure visual uses a text-free `editorial_animation` derivative with `portrait_style: editorial-animation`, directly derived from one reviewed non-synthetic public-figure `source_photo`, `official_evidence`, or `source_capture`, with identity, clothing, and factual context approved. In `obvious-editorial-eye-band` mode it also records `portrait_style_strength: obvious-editorial`, `portrait_eye_motif: editorial-ruler-eye-band`, and approvals for obvious style, motif presence, visible ruler ticks, and editorial-only meaning. The eye-band is forbidden on `non_identifying_fallback` assets and can never set `review.non_identifying: true`; it is an editorial motif, not anonymization, consent, licence, or portrait/publicity-right clearance. Incidental people in source captures are cropped out; private people, minors, victims, and staff use a reviewed non-identifying visual. Source media records `visual_text: source_original`; inspected synthetic images record `visual_text: none`. Review approval never changes `rights_status`; web and local assets still default to `unreviewed`, `local_review_only`, and publication blocked.

`capcut-map.json` is created by the dry run. It records the immutable base-tree hash, destination, display name, 15 material and segment mappings, two title mappings, 14 caption mappings, microsecond timing, canonical base-template snapshots for root segment, root material, mini segment, and mini material geometry, plus `reuse_policy`, `reuse_existing`, and `next_action`. The first successful clone is saved to `project.json.capcut.active_destination_name`. Later preparation reuses that exact folder even when a caller requests a `v2`/`v3` name; it returns `next_action: retime-capcut --confirm-existing`, while `clone-capcut` performs no write. Retime may migrate snapshots only from a structurally compatible base template, never from the edited destination. Same-beat followers use their leader's base segment and material snapshots. With `person_motion_mode: subtle-deterministic`, only mappings backed by `editorial_animation` receive a deterministic `motion_plan`; it records the pattern, beat, segment-local start/end scale and position, duration, and final keyframe offset. A split beat is one continuous interpolation, so each follower starts at the preceding segment's exact end value. Missing mode keeps legacy static behavior.

## CapCut boundary

The default clone source is:

`~/Movies/CapCut/User Data/Projects/com.lveditor.draft/news2shorts`

The source must have a 1080×1920 30fps canvas, one 15-segment image track, two single-segment title tracks, and one 14-segment caption track. Preparation fails when this shape changes.

Clone only while CapCut is closed. The first clone gets a new root draft UUID and local metadata while keeping internal timeline, track, material, and segment IDs. All 17 external image paths are rewritten to files inside the new draft. Mirrored draft snapshots and `mini_draft.json` timing/text are updated together. After that first clone, keep one active destination and update it through `retime-capcut`; never create version-up draft folders. The shared CapCut root index is never edited.

The handoff contains `narration.txt`, optional `narration-timing.json` and `narration-performance.json`, `captions.srt`, `sfx-cues.csv`, `replace-with-video.csv`, `youtube-upload.json`, `youtube-upload.md`, source and generated files, provenance JSON, an editing guide, and when enabled `final-visual-qc.json` plus player screenshots. The YouTube files contain copy and settings only, preserve the project publish block, and are displayed in the final result without uploading. `final-visual-qc.json` binds approved beat-midpoint screenshots to the current semantic visual-timeline, storyboard, and capcut-map hashes and records white/yellow title presence, caption presence, correct visual, source-text readability, and clipping/overlap checks. Public-figure samples also bind player-size obvious-style, eye-band, and ruler-tick approvals. Every motion beat additionally binds start/end player screenshots, and every split motion beat binds the immediate before/after boundary frames with continuity, no-black-frame, and no-jump approvals. A stale or failed sample blocks `validate --stage capcut`. `retime-capcut` edits only an explicitly confirmed existing destination while CapCut is closed, preserves `.bak` recovery snapshots and narration audio IDs, updates the approved audio duration without replacing those IDs, restores canonical base-template geometry across active root/template/mini representations, applies deterministic person motion only to eligible editorial animations, refreshes active draft covers from scene 1, backs up and invalidates only the active timeline's prerender cache, and records the project-side backup paths.
