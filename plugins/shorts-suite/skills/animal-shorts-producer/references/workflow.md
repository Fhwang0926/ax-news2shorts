# Workflow

## 1. Candidate research

Research current TikTok and YouTube Shorts originals. Write observed public metrics, editorial-fit component scores, and a plain-language `content_explanation` covering story flow, appeal, adaptation direction, and limitations to a candidate input file. Run:

    python3 <plugin-root>/scripts/animal.py score-candidates --input <input.json> --output <ranked.json> --top-k 3

Show the resulting ranked candidates and stop for source selection. Never download while only comparing candidates.

## 2. Source project

Initialize the user's choice with candidates plus candidate-id, source-url, or source-file. New projects default to `--visual-preset observation-contrast-v1`; use `--visual-preset animal-viral-card-v1` only when the user requests the legacy card layout. A URL project starts at source_selected. A local file is copied into the project and starts at source_acquired.

Run acquire only for the selected public URL. A failed direct yt-dlp acquisition becomes source_pending; do not use a mirror.

## 3. Visual review

Run preview and inspect contact-sheet.jpg plus boundary frames in the source video. Author the observation input from visible action. Record protected watermark and face regions before any caption blur region.

Run observe. It writes source-analysis.json and changes the project to source_reviewed.

## 4. Story choice

Author exactly three passing story options. Each option must use a different fun mechanism, contain setup-build-turn-payoff in order, and give every beat an emphasized lower message and a scene music cue. Every beat must reference source-analysis observation IDs. For the observation-contrast preset, add an evidence-grounded `subject_label` to every beat and keep its shorter cadence contract. Optional timed Korean source-caption overrides and no-vocal SFX must come from the visual review, not source-caption claims.

Run stories, show story-options.md, and stop. After the user chooses, run select-story and compose.

## 5. Validation, draft review, and local render

Generate edit-plan.md and run validate --final. Resolve every error before rendering a draft. Warnings about unknown rights remain warnings and must be shown in delivery.

Run render --draft and show outputs/preview.mp4. Stop for the user's story-fit and music-fit decision. Record both with approve-draft; a revise decision keeps the project at rendered_draft. Only draft_approved can render outputs/short.mp4.

Render creates a source-audio plus scene-aware no-vocal-BGM and optional no-vocal-SFX H.264/AAC MP4 at or below 59.5 seconds. It does not upload. render-report.json is technical proof only.
