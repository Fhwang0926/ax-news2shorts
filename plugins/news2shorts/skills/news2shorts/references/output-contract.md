# Output contract

Each project is self-contained and portable:

```text
<project-dir>/
├── project.json
├── sources.json
├── fact-sheet.json
├── script.md
├── storyboard.json
├── rights-manifest.json
├── publish.json
├── assets/
│   ├── generated/
│   └── collected/
├── audio/
├── preview.mp4
├── short.mp4
├── thumbnail.jpg
├── render-report.json
├── whiteboard-project/         # visual_mode=whiteboard local review only
│   ├── scenes/
│   ├── rights-manifest.json
│   └── outputs/preview.mp4
└── edit-package/
    ├── preview/
    └── short/
```

## `project.json`

Tracks topic, source URL, timezone, status, target length, sensitive-topic classification, retention profile, visual style, fixed quick-reveal format, delivery mode, brand treatment, optional middle CTA, CTA tail, optional generated audio bed, and review flags. New version 17 projects use `quick-reveal` with `delivery_mode: "continuous-flow"` by default or explicit `visual-first`, apply the citizen-question, answer-timing, photo-first contracts, and a role-specific `visual_sourcing.mode`. `fact-stack`, `story-explainer`, `broadcast-card`, and `classic-card` remain available only when rendering an existing legacy project. Final rendering requires:

`narration_style` is backward-compatible and defaults to `standard` when absent. `cc-helper-conversational` is available only for narrated delivery and changes sentence endings and connective flow without weakening source, truth-guard, sensitive-topic, or payoff rules:

```json
{
  "delivery_mode": "continuous-flow",
  "narration_style": "cc-helper-conversational"
}
```

Visual-first rejects `cc-helper-conversational` because it has no narration. Formal `합니다`/`했습니다`/`입니다` endings, adjacent `~데/~는데`, and a final `~함 → ~함` pair are invalid in this style. Verbatim `audio_mode: "source-video"` dialogue is exempt. The style does not permit unsupported intent, exaggeration, slang, blame, consensus, or reaction claims.

```json
{
  "approvals": {
    "editorial_reviewed": true,
    "rights_reviewed": true,
    "synthetic_disclosure_reviewed": true
  }
}
```

Version 4+ records why the format was selected and enables the common post-payoff CTA:

```json
{
  "format_selection": {
    "mode": "auto",
    "selected": "quick-reveal",
    "reason": "서로 다른 검증 주장 4개와 적용 조건 존재",
    "confidence": "high"
  },
  "cta_tail": {
    "enabled": true,
    "duration": 2.0,
    "headline": "빠른 소식 계속",
    "prompt": "구독 · 좋아요",
    "narration": "다음 소식도 바로 전해드릴게요.",
    "comment_headline": "여러분의 판단",
    "comment_prompt": "댓글로 한마디",
    "comment_narration": "여러분의 생각을 댓글로 남겨주세요.",
    "voice_enabled": true,
    "style": "common-dark-yellow"
  }
}
```

Version 17 adds a user-configurable middle CTA. `auto` is the new-project default, `enabled` records an explicit inclusion request, and `disabled` records an explicit exclusion that the renderer must preserve:

```json
{
  "mid_cta": {
    "mode": "auto",
    "placement": "after-auto-rehook",
    "min_duration": 1.5,
    "max_duration": 2.0,
    "style": "pity-native-arrow",
    "voice_enabled": true,
    "voice_delivery": "verdict",
    "sfx_enabled": true,
    "ui_target_profile": "youtube-shorts-mobile",
    "arrow_target": {"x": 0.34, "y": 0.86},
    "ordinary_copy": {
      "headline": "보고 계신데...",
      "emphasis": "구독은 아직이네요",
      "subline": "채널명 옆 구독, 한 번만",
      "narration": "구독은 아직이네요."
    },
    "sensitive_copy": {
      "headline": "잠깐만요",
      "emphasis": "구독은 아직",
      "subline": "채널명 옆 구독, 한 번만",
      "narration": "구독 한 번만 부탁드려요."
    }
  }
}
```

The renderer inserts the middle CTA only for a continuous-flow news body at least 20 seconds long and only after the `rehook` or `turn` boundary nearest 50% within the 40-60% window. It records the selected boundary, normalized UI target, actual Typecast duration, and generated SFX in `render-report.json`. The visual arrow points toward the lower-left Shorts channel area without drawing a fake clickable button. No middle-CTA SRT cue is generated. When the middle CTA renders, the ordinary two-second subscribe/comment tail becomes a 0.8-second voice-free brand close by default. When the user explicitly requests a separate final CTA, set `cta_tail.keep_after_mid_cta: true`; the renderer must preserve both the middle CTA and the configured final CTA instead of disabling either one. Otherwise the version 16 tail behavior remains.

Version 7 through 15 use the mandatory pre-news intro. The renderer supplies the legacy defaults to older projects that omit the object, so rerendering them keeps the same clip:

```json
{
  "brand_intro": {
    "enabled": true,
    "asset": "news-hanmyeon-channel",
    "transition": "fadeblack",
    "transition_duration": 0.25
  }
}
```

The packaged 3.15-second 720x1280 `news-hanmyeon-channel` intro shows the user-provided 뉴스한면 logo and the fixed slogan `세상의 이슈를 모아 / 우리 삶의 문제를 짚습니다`, while retaining its embedded audio. Only the intro-to-first-news-frame boundary uses the 0.25-second video transition and matching audio crossfade. Version 16 replaces this lead-in with `corner-logo`, which overlays the existing logo on the first content frame and adds zero seconds. News scenes remain hard cuts and the CTA appears exactly once.

Version 8 adds automatic CTA variation. Sensitive news always selects `subscribe`. A safe, verified payoff `discussion_prompt` selects `comment` and becomes the comment tail headline, while the narration uses `여러분의 생각을 댓글로 남겨주세요.`. When there is no topic-specific prompt, ordinary projects use a stable SHA-256 two-bucket fallback with an editorial 50:50 subscribe/comment distribution. The same project always keeps the same bucket. This is a production allocation, not an engagement-performance claim. `render-report.json` records the selected variant, reason, strategy, optional distribution and bucket, and the actual screen and narration copy.

Version 9 makes the citizen-question contract mandatory for new projects. `viewer_stake` identifies a concrete citizen or consumer consequence, `tension_question` supplies the opening question, and the selected hook, first visible headline or caption, and first narration all end with `?`. A neutral news-summary lead is invalid. Every video render also creates a separate question-led thumbnail asset and records `purpose: "dedicated-curiosity-thumbnail"`, `separate_asset: true`, and `question_led: true` in `render-report.json`. Version 14 adds explicit `media_type` records and requires approved, non-synthetic actual photos or real footage in at least 60% of visual scenes. Older projects remain compatible.

Version 15 adds `standard`, `hot-real-news`, and `whiteboard` visual modes. `hot-real-news` records a 24-hour discovery window and a minimum of two distinct reporting domains in the latest six-hour window. `whiteboard` creates a separate `whiteboard-project` from inspected local news visuals and uses the installed Whiteboard Shorts SRT renderer. `unreviewed` public visuals are local-draft-only, remain unapproved, inherit `unknown` or `review_required`, and cannot satisfy the clean-final real-media gate.

Version 16 adds first-frame content and explicit delivery timing. New projects use `brand_intro.mode: "corner-logo"`; version 15 and older projects without a mode retain `legacy-full`. `shorts_profile.first_answer_scene_id` must begin by 8.0 seconds in continuous-flow or 1.5 seconds in visual-first. When `truth_guard` is non-empty, `truth_guard_scene_id` must begin by 4.0 seconds. Visual-first uses 4-6 narration-free scenes, a generated no-vocal `news-pulse` bed at `audio/background-music.wav`, and render-report version 4 `retention_timing` plus `audio_bed` records.

The optional `collect-internet-visual` command stores one selected public HTTPS image as a bounded PNG, assigns it to one scene, and records its canonical source page, final download URL, SHA-256, relevance review, and pending permission state. The news Whiteboard integration may omit the visible review badge only after explicit image and annotation confirmation; the nested project and render report must still keep `publish_blocked: true`, `local_review_only`, and the unresolved permission states.

Version 10 adds `editorial_grounding` so a reusable template preserves place, people, and accountability specificity across topics:

```json
{
  "editorial_grounding": {
    "locations_reviewed": true,
    "locations": [
      {"name": "제주도", "scene_ids": ["scene-01"]}
    ],
    "people_reviewed": true,
    "people": [
      {
        "name": "중앙 인물",
        "role": "public_official",
        "scene_ids": ["scene-04"],
        "visual_status": "rights_blocked",
        "asset_path": ""
      }
    ],
    "accountability": {
      "mode": "verified",
      "trigger": "확인된 행위 또는 누락",
      "consequence": "확인된 시민 피해 또는 신뢰 훼손",
      "claim_ids": ["claim-01"],
      "scene_ids": ["scene-02"],
      "reason": ""
    }
  }
}
```

Every recorded location must appear literally in one declared setting scene. Named people use `public_official`, `public_figure`, `private_person`, `victim`, `accused`, or `other`; a `used` person requires a matching rights-approved asset and identity review, while privacy or rights blockers leave `asset_path` empty. `accountability.mode: "verified"` requires an evidence-linked action or omission and its concrete consequence; use `not_applicable` with a reason when the sources do not support that frame. Existing version 9 and earlier projects remain compatible.

Version 11 adds a reusable final-retention contract. Legacy scene-based storyboard version 6 payoff scenes require `payoff_punch` plus `voice_delivery: "verdict"` or `"contrast"`. Version 12+ continuous-flow projects keep `voice_delivery: "auto"` for every scene because the body is synthesized once. In both modes, the punch must add a remaining answer, concrete consequence, supported contradiction, or exact next condition rather than repeat `payoff_title` or `payoff_detail`. Its meaningful wording must also be spoken in a payoff narration with at least two audible beats. Existing projects remain render-compatible.

For new retention projects, `payoff_title`, `payoff_detail`, and `payoff_punch` must also avoid repeating a complete visible caption, evidence label, or evidence value from an earlier scene. Draft validation warns and final validation rejects those duplicates. A conclusion question remains allowed after the factual answer, but the renderer reserves it for the later comment CTA rather than drawing it twice. Relative timing such as `다음 달부터` or `오늘부터` receives a validation warning because it can become false when publication moves; keep the verified absolute date in evidence and use durable status copy when appropriate. Enforcement copy that implies `신고하면 바로 견인` receives a warning unless the source actually supports immediate towing.

New version 14 projects always record `quick-reveal`; legacy projects retain their original selection. The CTA is a renderer-level tail, not a news scene; it follows the complete payoff exactly once.

New projects set automatic narration voice selection:

```json
{
  "narration_voice": {
    "mode": "auto",
    "voice": ""
  }
}
```

Typecast does not expose a numeric most-used ranking. The renderer therefore starts from Typecast's official popular Top 5 set—Daeun, Seohyeon, Piljae, Moonjung, and Kangil—and preserves specialist choices for sensitive news, guide-heavy narration, and story explainers planned for at least 55 seconds. Every other automatic project uses a project-stable ten-bucket default: buckets 0-7 select Piljae and 8-9 select Daeun. The SHA-256 bucket is derived from project identity, so a rerender keeps the same voice while different projects approach an 80:20 production mix. This mix is an editorial setting, not a measured popularity or performance claim. After rendering, the renderer adds the selected Voice ID, name, profile, reason, selection strategy, popularity basis, source, distribution, distribution basis, bucket, and timestamp to this object. Set `mode` to `manual` and `voice` to one of those five names only when a stable override is required. Existing projects without `narration_voice` behave as `auto`.

New projects also enable dual-track visual sourcing:

```json
{
  "visual_sourcing": {
    "web_search_enabled": true,
    "prefer_collected_assets": true,
    "prefer_current_news_and_community_visuals": true,
    "source_priority": [
      "current-news-article",
      "public-community-post",
      "official-primary-media",
      "licensed-media-library",
      "generated-fallback"
    ],
    "allow_unreviewed_news_community_draft": true,
    "community_visual_privacy_review_required": true,
    "korean_visuals_required": true,
    "visual_locale": "ko-KR",
    "foreign_visual_fallback": "blocked",
    "korean_context_review_required": true,
    "generation_fallback": true,
    "real_news_photo_required": true,
    "visual_quality_review_required": true,
    "company_visuals": {
      "mentions_reviewed": true,
      "companies": [
        {
          "name": "기업명",
          "scene_ids": ["scene-02"]
        }
      ]
    },
    "min_real_media_ratio": 0.6,
    "generated_image_size": "720x1280",
    "generated_style": "korean-editorial-realism"
  }
}
```

`source_priority` fixes the new-project search order. Current news articles and public community posts are searched before generic stock libraries, but a public page is never a permission basis by itself. A directly relevant news or community image with unclear rights may be kept only as `unreviewed` local-review evidence when provenance and privacy checks pass. It must be confirmed or replaced before final rendering. Community comments, usernames, avatars, private addresses, license plates, and unrelated people are never retained as visual assets.

`korean_visuals_required` blocks foreign visual fallback. Every used asset must record `visual_locale: "ko-KR"`, `korean_context_reviewed: true`, and a concrete `korean_context_note` based on the actual pixels. New generated fallback uses `korean-editorial-realism`; foreign-looking or country-ambiguous documentary visuals fail validation even when their source page is Korean.

For an explicitly selected international incident with direct Korean citizen impact, initialize the narrow actual-event exception:

```json
{
  "visual_sourcing": {
    "korean_visuals_required": false,
    "visual_locale": "mixed-source",
    "foreign_visual_fallback": "source-event-only",
    "korean_context_review_required": false,
    "generated_style": "source-event-explainer",
    "international_source_visuals": {
      "enabled": true,
      "source_country": "NP",
      "source_locale": "ne-NP",
      "actual_event_only": true,
      "rights_review_required": true,
      "citizen_stake": "네팔 현장에서 연락이 두절된 한국인 9명의 안전과 수색"
    }
  }
}
```

An international actual-event asset uses the configured source locale and country, `source_event_context_reviewed: true`, a concrete `source_event_context_note`, and `actual_event_media: true` for photos or video. Korean response assets may remain `ko-KR` with the ordinary Korean-context fields. This exception never permits generic foreign stock or turns public footage into reusable media; unknown rights remain local-review-only.

Project version 6 adds the central-company visual gate. `mentions_reviewed` confirms that narration and visible copy were checked for specifically named companies. `companies` contains only central parties, not publishers, source credits, or incidental comparisons. Each company needs an exact `name` and the scene IDs of its first meaningful mention. At least one of those scenes must use a rights-approved, non-synthetic logo or directly matching company image whose rights record identifies the company. When no compatible asset exists, final validation remains blocked rather than accepting an invented logo or generic industry image. Existing version 5 and earlier projects remain compatible.

New projects also set `visual_style.show_payoff_label`, `visual_style.show_source_label`, and `visual_style.show_fact_stack_index` to `true`, plus `visual_style.payoff_panel_style: "editorial-card"` and `visual_style.screen_copy_mode: "noun-phrases"`. The renderer replaces the ordinary payoff caption with a dedicated conclusion card, adds a small `뉴스 출처:` label to every scene, and draws structured proof cards only for version 3 fact-stack proof beats. In noun-phrase mode, draft validation warns and final validation rejects long visible copy or Korean sentence endings in `display_headline`, `eyebrow`, `headline`, `headline_highlight`, `caption`, `caption_focus`, `evidence_label`, `evidence_value`, `payoff_title`, `payoff_detail`, `payoff_punch`, `payoff_callback`, and `discussion_prompt`. Narration remains natural full sentences. Final validation requires a qualifying real news photo, `payoff_title`, `payoff_detail`, and scene source fields only when the corresponding new-project flags are enabled, so existing projects remain compatible.

`shorts_profile` separates the attention strategy from the visual format. It records `hook_type`, the selected `hook`, `hook_stake`, `open_loop`, `midpoint_rehook`, `payoff`, and optional `loop_close`. Project version 5 also requires `issue_focus`, `viewer_stake`, `tension_question`, `visual_attention_device`, `visual_attention_scene_id`, and `visual_attention_reason`. `issue_focus` identifies the sourced contradiction or failed expectation beneath a procedural update; `viewer_stake` states the concrete cost, inconvenience, risk, gap, or fairness concern; and `tension_question` names the topic-specific challenge the payoff must answer. The visual attention device is one of `reaction-meme`, `contrast-composite`, `consequence-photo`, `evidence-closeup`, or `motion-proof` and points to the scene where that issue becomes visually legible. `hook_stake` is one sourced sentence explaining why the opening number or claim matters. Project version 3+ quick-reveals require a meaningful term from it in the first frame and first narration plus supporting `claim_ids` on the first scene; this rejects context-free numeric hooks. Version 13 adds `early_rehook_scene_id`, `withheld_detail`, and `truth_guard`: the designated sourced rehook must start by 10.0 seconds including the intro, reveal one new fact, preserve every truth-changing qualifier, and leave only the recorded bounded answer for the payoff. Final rendering of a new retention format requires the hook, issue lens, attention device, open loop, and payoff; non-quick formats also require a midpoint rehook. The payoff must add a verified answer, cause, consequence, or meaning instead of paraphrasing the hook. It must be a complete sentence that gives the current answer and its consequence or next condition; generic endings fail validation.

## `sources.json`

Contains `id`, title, publisher, URL, publication/update times, retrieval time, and source type. IDs are referenced from the fact sheet.

## `fact-sheet.json`

Contains claims with `id`, `statement`, `status`, `confidence`, and `source_ids`. A narration claim without a source ID is invalid.

## `storyboard.json`

Contains ordered scenes. New projects use version 6. Version 3 introduced the strict fact-stack contract, version 4 added story linkage, visual roles, and timed motion, version 5 linked one primary attention device back to the project issue lens, and version 6 adds the final-retention line and scene-level Typecast delivery while older storyboards remain render-compatible. Supported fields are:

- `id`: stable scene ID.
- `duration`: requested minimum seconds.
- `beat`: one of `hook`, `context`, `evidence`, `turn`, `impact`, `rehook`, `payoff`, or `loop` for the new formats.
- `progress`: optional compact progress label.
- `fact_index`: proof counter shown as `FACT N/N` in a version 3 `fact-stack`. Proof beats must form a complete `1/N` through `N/N` sequence.
- `eyebrow`: optional one-line context above the main headline.
- `headline`: large frame title.
- `headline_highlight`: optional exact phrase in the headline to draw with the accent color.
- `caption`: short on-screen message.
- `caption_focus`: optional exact phrase inside `caption` to emphasize in the accent color.
- `claim_ids`: one or more IDs from `fact-sheet.json` supporting a proof beat. A new fact-stack requires at least three distinct linked claims.
- `evidence_kind`: proof presentation type: `photo`, `video`, `document`, `map`, `comparison`, `number`, `timeline`, or `diagram`.
- `evidence_label`: compact noun-phrase label shown on the structured proof card.
- `evidence_value`: optional compact value; required for `number` and `comparison` proof.
- `payoff_title`: direct answer shown in large white type on an `editorial-card` payoff.
- `payoff_detail`: practical meaning, exact condition, or viewer check shown below the payoff title.
- `payoff_punch`: final large retention line that adds a remaining answer, concrete consequence, supported contradiction, or exact next event. When present, it takes the conclusion card's final zone and `discussion_prompt` remains available for the CTA.
- `payoff_callback`: compact opening-promise-to-answer bridge shown above the final fact-stack conclusion card.
- `discussion_prompt`: optional short, topic-specific noun-led question shown after the factual payoff, such as `정상 제품?`. Use it only when the reaction, contradiction, or disputed judgment is supported by the fact sheet; never replace `payoff_title` with a question. When present in noun-phrase mode, narration must state the factual conclusion first and end with the fuller contextual question for Typecast cadence.
- `story_link`: editorial-only `answers` and `next_gap` fields. The hook opens a gap, middle beats answer and hand off, and the payoff answers without opening a new gap.
- `visual_role`: `evidence`, `context`, `explanation`, or `reaction-meme`. A reaction meme is restricted to `context` or `rehook` and is never a fact proof.
- `ticker`: optional two-line news ticker in `broadcast-card`; falls back to `caption`.
- `narration`: spoken text. When `project.json.narration_style` is `cc-helper-conversational`, non-source-video narration uses friend-explainer endings while preserving the same claim IDs and factual qualifiers.
- `voice_delivery`: `auto`, `contrast`, or `verdict`. `auto` keeps Smart Emotion context; `contrast` applies the Typecast `toneup` preset with restrained lift; `verdict` applies `tonedown` with a slightly lower pitch and slower tempo. Version 12+ continuous-flow projects use `auto` for every scene; only legacy scene-based payoff scenes require `contrast` or `verdict`.
- `image`: optional project-relative path.
- `image_fit`: `auto`, `contain`, or `cover`. `auto` and `contain` preserve the full still inside the evidence-safe region over a dim blurred background. `cover` is an explicit full-bleed crop and must be visually approved.
- `video`: optional project-relative clip path for a new retention format. Do not combine it with `image` in the same scene.
- `video_start`: optional non-negative starting second within `video`.
- `audio_mode`: `narration` by default or `source-video` when an explicitly approved local video scene must keep its embedded dialogue. `source-video` requires a video with an audio stream and uses the same `video_start` for picture and sound.
- `render_text_overlay`: optional boolean. Set `false` on a source-dialogue scene to suppress the news headline and lower-caption overlay while retaining compact provenance.
- `external_caption`: optional boolean. Set `false` when the source video already contains synchronized embedded captions so `edit-package/<output-stem>/captions.srt` does not duplicate them.
- `motion`: `zoom-in`, `zoom-out`, or `none`; legacy `slow-zoom` maps to `zoom-in`.
- `motion_start`: scene-relative second when a version 4 zoom begins.
- `motion_duration`: seconds spent zooming, normally `0.35`-`2.5`.
- `motion_emphasis`: the spoken person, object, number, result, context, or scale reveal that justifies the zoom.
- `focus_x`, `focus_y`: normalized `0.0`-`1.0` focal coordinates for still-image motion.
- `zoom_scale`: optional final still-image scale from `1.0` to `1.25`. Keep the default near `1.055`; use about `1.10`-`1.16` for a clearly visible face-centered person zoom.
- `audio`: optional project-relative narration audio.
- `credit`: short source/asset credit.
- `source_label`: short publisher label shown as `뉴스 출처:` near the bottom.
- `source_ids`: one or more IDs from `sources.json` supporting the scene.
- `synthetic`: whether the visual is generated or materially synthetic.

The renderer may extend continuous-flow scene duration when narration audio is longer than requested. Version 12+ continuous-flow generates the complete body narration once, allocates clause-level scene cues, and remuxes the uninterrupted track over hard-cut visuals; scene-level `audio` is rejected. When at least one scene explicitly uses `audio_mode: "source-video"`, continuous-flow switches to the scene-aligned hybrid path: source scenes extract picture and sound from the same `video_start`, while remaining narration scenes use their normal Typecast or configured audio. Version 16 visual-first preserves requested scene durations, requires narration-free visible claims, mixes the generated no-vocal bed, and uses the corner logo with no lead-in. Clip scenes are cropped to 9:16 and trimmed to the rendered scene length. Ordinary clip scenes receive the shared headline/caption hierarchy; `render_text_overlay: false` uses provenance-only overlay instead. Version 4+ stills default to `image_fit: "auto"` and no motion; timed motion affects only the configured emphasis interval below the fixed overlay. Each still-image path may appear in only one scene. Legacy version 3+ fact-stack validation remains available for old projects. Version 4+ rejects unsupported image-fit modes, excessive or unjustified zoom, broken story links, unsafe meme placement, and a missing CTA configuration. Version 5 additionally rejects a missing or generic issue lens, a hook that does not expose the chosen issue, a payoff that does not return to it, or an attention device without a valid scene and reason. Storyboard version 6 with project version 11 rejects a missing or repeated payoff punch or a one-beat payoff narration; continuous-flow keeps the narration rules, while visual-first requires the answer in visible copy. Version 13 checks the designated rehook timing. Version 16 validates corner-logo, first-answer, truth-guard, visual-first pacing, and two-second CTA rules. The default MP4 output is 720x1280 H.264/AAC.

## `source-audio-review.json`

Created by `review-source-audio` whenever one or more storyboard scenes use `audio_mode: "source-video"`. It records the transcript backend, source-relative path and SHA-256, `video_start`, `duration`, expected `narration`, transcript text, optional timestamped segments, text-match scores, edge margins, reasons, and per-scene `status`. It never stores the absolute path of an external transcript file; only its basename and SHA-256 are retained. A transcript is dialogue evidence only and does not prove speaker identity or factual truth.

Draft validation warns when this artifact is missing or stale. Final validation requires a `passed` record for every source-audio scene and invalidates the record after changes to the source bytes, cut timing, or expected dialogue. Timestamp-free transcripts remain `review_required` unless the operator explicitly confirms the cut timing after listening.

## `edit-package/<output-stem>/`

Every render produces a portable, one-way package for CapCut Desktop/Web, Vrew, and other MP4/WAV/SRT editors. `preview.mp4` maps to `edit-package/preview/`; `short.mp4` maps to `edit-package/short/`. A custom render output uses its sanitized filename stem.

```text
<output-stem>/
├── reference.mp4
├── editable.mp4
├── captions.srt
├── timeline.csv
├── edit-manifest.json
├── 사용방법.txt
├── brand-intro.mp4
├── scenes/
│   ├── scene-01.mp4
│   ├── mid-cta.mp4 (version 17에서 선택된 경우)
│   └── cta-tail.mp4
├── audio/
│   ├── scene-01.wav
│   ├── mid-cta.wav (version 17에서 선택된 경우)
│   └── cta-tail.wav
├── overlays/
│   └── scene-01.png
└── metadata/
    ├── storyboard.json
    ├── rights-manifest.json
    ├── sources.json
    └── source-audio-review.json (source-video 장면이 있을 때)
```

`reference.mp4` is the exact plugin render. `editable.mp4` retains narration, intro, CTA, scene timing, crop, and deliberate motion while omitting the fixed news text overlays from current retention scenes. `captions.srt` is UTF-8 and starts the first cue at the actual intro-to-body transition offset. Each scene MP4 contains its matching narration; WAV files provide separable narration audio; transparent PNG overlays preserve the plugin layout when the external editor supports image layers. `timeline.csv` records the overlapping intro transition and exact measured scene boundaries. `edit-manifest.json` maps every exported file back to its storyboard scene and retains an explicit `round_trip_supported: false` boundary. Overlay text remains rasterized; editors can hide the PNG and rebuild editable text from the CSV or SRT. External edits never mutate or synchronize back to `storyboard.json`.

## `rights-manifest.json`

Contains `searches` and `assets`. `searches` records the query, related scenes, timestamp, outcome, selected asset path, and decision note without archiving bulk results. `assets` contains one provenance record for each storyboard image or clip plus any separate thumbnail presenter. Project version 3+ quick-reveals also require `relevance_level` (`direct` or `contextual`) and a specific `relevance_note` for every used scene visual. Hook, evidence, turn, impact, and payoff beats require `direct`; only a context beat may use a merely contextual place or concept image. A version 4+ reaction meme additionally requires `usage_role: "reaction-meme"` and `meme_origin: "licensed"`, `"owned"`, or `"original"`. A company-identifying asset records `company_names`, `company_visual_type` (`logo`, `official-image`, `licensed-photo`, `branded-product`, or `facility-signage`), and `company_identity_reviewed: true`. A named-person asset records `person_names` and `person_identity_reviewed: true`; it must match a `used` entry in `editorial_grounding.people` and may never be synthetic. A separate thumbnail presenter records `usage_role: "thumbnail-presenter"`, `presenter_context_reviewed: true`, and `case_party: false`; it is not evidence and may never substitute for a named case person. A final render rejects visual assets without an approved manifest record, rejects collected web assets without a canonical source page or usage basis, rejects generated images without `visual_quality_reviewed: true`, and requires at least one approved non-synthetic photo with `news_relevance_reviewed: true` in new projects. Version 14 records `media_type` on every used visual and blocks final rendering below the configured real-photo and real-footage ratio. Version 6 also rejects a missing company-mention review or a central company without a qualifying used asset in its declared first-mention scene.

## `publish.json`

Stores the copy-ready YouTube upload package. Version 4 adds link-free description validation and exact title/description character counts. Version 5 separates the title hook from the description answer and keeps hashtags out of the description while retaining older projects:

```json
{
  "version": 5,
  "title": "한 줄 질문 또는 호기심 훅",
  "description": "제목을 반복하지 않는 답·근거·조건·확인사항과 링크 없는 출처명",
  "tags": ["핵심어", "띄어쓰기 변형"],
  "source_lines": ["매체명 — 기사명"],
  "contains_synthetic_media": true,
  "pinned_comment": "확인된 결론을 먼저 적고, 근거 있는 주제 질문으로 마무리",
  "upload_settings": {
    "thumbnail_method": "file_upload",
    "thumbnail_file": "thumbnail.jpg",
    "thumbnail_hook": "이 결정, 시민에게 정말 맞을까?",
    "thumbnail_subhook": "검증된 반전·시민 영향",
    "thumbnail_badge": "지원보다 남은 공백",
    "thumbnail_style": "auto",
    "thumbnail_presenter_file": "",
    "thumbnail_note": "별도 호기심 유도 썸네일 파일: thumbnail.jpg",
    "playlist": "추천 재생목록 또는 선택 안 함",
    "audience": "not_made_for_kids",
    "category": "News & Politics",
    "video_language": "ko",
    "altered_content": "yes",
    "paid_promotion": false,
    "age_restriction": "none",
    "allow_comments": true,
    "visibility": "private",
    "schedule_at": ""
  }
}
```

The displayed title limit is 100 characters and the description limit is 5,000 characters. The deterministic formatter appends up to two normalized values from the front of `tags` to the base title, skips duplicates, and never crosses that title limit. It also prints the full copyable tag list with exactly one leading `#` per item, regardless of whether the stored value already included one. Version 4 descriptions and `source_lines` reject URLs, Markdown links, `www` addresses, and bare domains; descriptions also reject stock-photo provider or license notes, `자료사진` or `해당 단지·사건 사진 아님`, and Typecast, TTS, or synthetic-voice notices. Version 5 additionally rejects description hashtags and a body sentence that duplicates the title. Canonical URLs remain in `sources.json`, asset provenance remains in `rights-manifest.json`, and TTS details remain in `render-report.json`. The formatter displays `current/limit` counts and removes legacy links, production-method boilerplate, description hashtags, and repeated title sentences from copyable output. It refuses to print arbitrary `미작성` or unresolved review placeholders: complete every evidence-derived field and explicit upload decision first. New projects use `thumbnail_method: "file_upload"`; each render creates a dedicated `thumbnail.jpg` from two or three different rights-approved visuals and records its separate-asset and question-led purpose. When those visuals are unavailable, use `thumbnail_status: "blocked_rights"`, leave `thumbnail_file` empty, and state the exact missing rights-approved assets in `thumbnail_note`; the formatter exposes that blocker but final validation remains blocked. The `thumbnail_hook` must be a forceful but supported citizen question; `thumbnail_subhook` carries the verified reversal or consequence; `thumbnail_badge` names one topic-specific tension; and `thumbnail_style` is `auto`, `presenter-led`, or `evidence-led`. A presenter file is optional for `auto`, mandatory for `presenter-led`, forbidden on sensitive stories, and must match a reviewed `thumbnail-presenter` rights record. `video_frame` remains compatible with legacy projects. `playlist` contains a concrete recommendation or `선택 안 함`. `audience` is `made_for_kids` or `not_made_for_kids`. `altered_content` is `yes`, `no`, or the temporary draft value `review_required`; `age_restriction` is `none`, `18_plus`, or `review_required`. A final package must resolve both review states. `visibility` is `private`, `unlisted`, `public`, or `scheduled`; scheduled uploads require an ISO 8601 `schedule_at`. `contains_synthetic_media` records project truth, while `altered_content` records the reviewed YouTube disclosure choice and is not inferred blindly from any use of AI. Keep the pinned comment factual before its discussion question and never manufacture outrage or consensus. Use `upload-package` to render these fields in copy-ready Korean. This is preparation data only; the MVP does not upload, schedule, publish, or post the comment.

## `render-report.json`

Records the rendered video probe, selected TTS provider, Typecast outer-silence trim settings, `narration_style`, delivery timing, `attention_strategy`, `brand_intro`, `audio_bed`, `retention_timing`, CTA, editor package, thumbnail, and scene evidence metadata. `--no-tts` continuous-flow renders record `timing_strategy: "storyboard-requested"`; voiced renders record `narration-weighted`. Report version 3 adds the one-way edit package. Report version 4 adds actual first-answer and truth-guard timing plus generated visual-first background music. Draft and synthetic state are metadata only and do not add on-frame badges. It must never contain the Typecast API key.
