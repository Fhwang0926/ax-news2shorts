# Project and output contract

```text
<project>/
├── project.json
├── scene-plan.json
├── post-production.json
├── rights-manifest.json
├── input/story.srt
├── input/tiktok-source.mp4       # TikTok import only
├── input/tiktok-source.json      # TikTok import only
├── input/tiktok-storyboard.json  # TikTok import only
├── scenes/
│   ├── scene-01.json
│   ├── scene-01.png
│   └── scene-01.annotation.json
├── previews/
│   ├── scene-01-regions.png
│   └── scene-01.mp4
├── renders/scene-01.mp4
├── assets/audio/
│   ├── monkeys-spinning-monkeys.mp3 # licensed catalog example
│   └── background-music.wav         # generated fallback
├── outputs/
│   ├── preview.mp4
│   └── final.mp4
├── render-report.json
├── youtube-upload.json
├── youtube-upload.md
└── delivery-note.md                 # licensed music credit and upload note
```

## Status flow

```text
planned -> assets_ready -> annotated -> preview_rendered -> draft_rendered -> rendered
```

Do not advance status merely because a path exists. Require the corresponding validation and approval.

## Proof levels

- `validate`: project files and JSON contracts were checked.
- `--render-ready`: every selected scene has a valid image, annotation, and rights record.
- rendered-file validation: the output file exists and its media properties were probed when `ffprobe` is available.
- `--final`: clean-final rights and approval gates passed.

None of these proves lawful publication, factual accuracy, monetization, or platform acceptance.

## Output properties

- Region preview: source image with numbered annotation boxes.
- Review clip: approximately `540x960`, 15 FPS, H.264, planned scene caption, and configured scene zoom. The default includes a local-review label; an explicitly confirmed news2shorts compatibility draft may omit only that visible label while preserving draft and publication-blocked metadata.
- Final scene and merge: `1080x1920`, 30 FPS, H.264. `render --all` adds AAC background music and configured scene zooms when enabled. A licensed catalog track also creates `delivery-note.md` with its required credit.
- A full merge ends with one 1.8-second silent subscribe/like CTA shot and writes editable YouTube upload information.

This plugin does not add narration, vocals, unverified external music, commercial chart recordings, or uploads. Upload fields that require account or policy judgment remain review-required. Add a platform-library commercial song only through the official Shorts music picker after upload.
