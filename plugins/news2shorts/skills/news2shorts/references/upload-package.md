# YouTube upload package

Use this only for `video` results. It maps `publish.json` to the fields the user sees while uploading in YouTube Studio.

## Required response order

Return a `YouTube 업로드 정보` section after the video and validation summary. Do not shorten, paraphrase, or hide values behind a project-file link.

1. Full title with up to two topic hashtags and its exact `current/100` character count.
2. Full link-free description with its `current/5000` character count and source names. Do not repeat the title or include hashtags.
3. Tags as copyable comma-separated hashtag text. The formatter automatically adds one leading `#` to every non-empty tag and never emits `##`.
4. Thumbnail method, the actual project-relative thumbnail file, and its guidance.
5. Playlist recommendation or `선택 안 함`.
6. Audience as `예, 아동용입니다` or `아니요, 아동용이 아닙니다`.
7. Category and video language.
8. Altered or synthetic content disclosure choice.
9. Paid-promotion and age-restriction choices.
10. Comment and visibility choices; include the scheduled time when applicable.
11. Full pinned comment.

Run the deterministic formatter and include its complete output:

```bash
python3 <plugin-root>/scripts/news2shorts.py upload-package --project-dir "<project-dir>"
```

The formatter must not emit `미작성`, an empty string, or `검토 필요` as ordinary upload information. Before running it, fill every evidence-derived title, description, tag, source line, pinned comment, thumbnail text, and explicit upload decision. If a required value is absent or a decision remains `review_required`, the command fails and lists the fields that must be completed. Do not bypass that failure with invented copy.

When an external artifact genuinely cannot exist yet, record a specific block state rather than a placeholder. For example, a project with fewer than two rights-approved thumbnail stills may use `thumbnail_status: "blocked_rights"`, an empty `thumbnail_file`, and a `thumbnail_note` naming the required assets. The formatter then shows the rights block explicitly, while final validation and upload remain blocked. Do not upload, schedule, publish, or post the pinned comment.

The copyable description must not contain `http`, `https`, `www`, Markdown links, or bare domains. It must also omit production-method boilerplate such as stock-photo providers or licenses, `자료사진` or `해당 단지·사건 사진 아님`, and Typecast, TTS, or synthetic-voice notices. Keep canonical evidence URLs in `sources.json`; use `매체명 — 기사명` in `publish.json.source_lines` and in the description. Keep asset provenance in `rights-manifest.json`, TTS details in `render-report.json`, and synthetic truth in `contains_synthetic_media` plus the reviewed `altered_content` setting. The formatter strips legacy links and production-method boilerplate before display. Version 4 final validation requires the stored description and source lines to be clean; version 5 additionally rejects description hashtags and a body sentence that repeats the title.

The formatter keeps `publish.title` as the editorial base and automatically appends up to two normalized hashtags from the start of `publish.tags`. It skips duplicates and any hashtag that would make the displayed title exceed 100 characters. Leave enough room in the base title; final validation rejects a displayed title with no hashtag.

Keep `publish.tags` as normalized topic terms with or without a single leading `#`. The formatter removes any existing marker, sanitizes the value, and prints every copyable tag with exactly one leading `#`. This applies to the full tag line as well as the two title hashtags.

Treat the title and description as complementary fields. Use the title for the one-line question or curiosity hook. Start the description with the verified answer, evidence, condition, or practical check instead of restating that hook. Store hashtags only through `tags`; the displayed title receives up to two, while the description receives none. The formatter removes legacy description hashtags and exact or near-exact title sentences for backward-compatible output.

## Field decisions

- `thumbnail_method`: new video projects use `file_upload`; the renderer creates a dedicated `thumbnail.jpg` from two or three different rights-approved visuals instead of selecting a video frame. Keep `video_frame` only for compatible legacy projects.
- `thumbnail_file`: use the actual project-relative JPG path. A prompt, frame suggestion, or mock filename is not enough.
- `thumbnail_hook`: write a concrete citizen or consumer question ending with `?`. `thumbnail_subhook` supplies the sourced number, condition, contradiction, consequence, or reversal. Provocative wording and one delayed answer are allowed, but do not hide truth-changing qualifiers or invent blame, urgency, consensus, or a payoff absent from the video.
- `thumbnail_badge`: write a short topic-specific tension cue such as the supported condition, cost, gap, or reversal. Do not use generic `충격`, `속보`, `대박`, or `이게 맞아?` labels.
- `thumbnail_style`: use `auto`, `presenter-led`, or `evidence-led`. On ordinary non-sensitive stories, `auto` uses a separate reviewed `thumbnail-presenter` when available and otherwise falls back to direct evidence. Sensitive stories use `evidence-led`.
- `thumbnail_presenter_file`: for `presenter-led`, point to a rights-approved still recorded with `usage_role: "thumbnail-presenter"`, `presenter_context_reviewed: true`, and `case_party: false`. It must not be a broadcaster, celebrity, article subject, case party, unlicensed stock preview, or named-person substitute.
- `thumbnail_note`: provide the actual project-relative thumbnail path. Do not merely write `좋은 장면 선택`.
- `playlist`: give a concrete channel playlist recommendation or `선택 안 함`.
- `audience`: choose `made_for_kids` only when children are the primary intended audience, not merely because children appear in a general-news story.
- `video_language`: use `ko` for Korean narration and captions.
- `altered_content`: review the actual YouTube disclosure question. Do not infer `yes` from every use of AI tooling; distinguish realistic altered/synthetic depictions from ordinary editing, narration, and clearly illustrative diagrams.
- `paid_promotion`: set `true` only when the project contains paid placement, sponsorship, or endorsement.
- `age_restriction`: use `18_plus` only when the final video needs an adult restriction; otherwise use `none`. Keep `review_required` only in drafts.
- `visibility`: default to `private` unless the user explicitly asks for `unlisted`, `public`, or `scheduled` preparation.
- `schedule_at`: required only for `scheduled`, using an ISO 8601 date and time with timezone.
- `description`: keep it at 5,000 characters or fewer, count the exact displayed text, and use no links, hashtags, title repetition, or production-method boilerplate. Preserve factual source attribution with publisher and article names only.
