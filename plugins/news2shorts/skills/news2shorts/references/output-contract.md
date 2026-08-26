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
└── edit-package/
    ├── preview/
    └── short/
```

## `project.json`

Tracks topic, source URL, timezone, status, target length, sensitive-topic classification, retention profile, visual style, fixed quick-reveal format, continuous delivery, mandatory brand intro, alternating CTA tail, and review flags. New version 13 projects always use `quick-reveal` with `delivery_mode: "continuous-flow"`, apply the citizen-question and ten-second retention contracts, and record the evidence-based angle in `format_selection`. `fact-stack`, `story-explainer`, `broadcast-card`, and `classic-card` remain available only when rendering an existing legacy project. Final rendering requires:

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
    "duration": 4.0,
    "headline": "빠른 소식 계속",
    "prompt": "구독 · 좋아요",
    "narration": "구독과 좋아요 누르면, 빠른 소식 전해드릴게요.",
    "comment_headline": "여러분의 판단",
    "comment_prompt": "댓글로 한마디",
    "comment_narration": "여러분의 생각을 댓글로 남겨주세요.",
    "voice_enabled": true,
    "style": "common-dark-yellow"
  }
}
```

Version 7 adds the mandatory pre-news intro. The renderer also supplies these defaults to older projects that omit the object, so rerendering with the current plugin still prepends the same clip:

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

The packaged 3.15-second 720x1280 `news-hanmyeon-channel` intro shows the user-provided 뉴스한면 logo and the fixed slogan `세상의 이슈를 모아 / 우리 삶의 문제를 짚습니다`, while retaining its embedded audio. Only the intro-to-first-news-frame boundary uses the 0.25-second video transition and matching audio crossfade. News scenes remain hard cuts. The fixed output order is `brand intro → news scenes → payoff → CTA tail`; the CTA still appears exactly once. Existing projects that explicitly store `oldman-korea-map` remain renderable as a legacy asset, but all new projects use `news-hanmyeon-channel`.

Version 8 adds automatic CTA variation. Sensitive news always selects `subscribe`. A safe, verified payoff `discussion_prompt` selects `comment` and becomes the comment tail headline, while the narration uses `여러분의 생각을 댓글로 남겨주세요.`. When there is no topic-specific prompt, ordinary projects use a stable SHA-256 two-bucket fallback with an editorial 50:50 subscribe/comment distribution. The same project always keeps the same bucket. This is a production allocation, not an engagement-performance claim. `render-report.json` records the selected variant, reason, strategy, optional distribution and bucket, and the actual screen and narration copy.

Version 9 makes the citizen-question contract mandatory for new projects. `viewer_stake` identifies a concrete citizen or consumer consequence, `tension_question` supplies the opening question, and the selected hook, first visible headline or caption, and first narration all end with `?`. A neutral news-summary lead is invalid. Every video render also creates a separate question-led thumbnail asset and records `purpose: "dedicated-curiosity-thumbnail"`, `separate_asset: true`, and `question_led: true` in `render-report.json`. Older projects remain compatible.

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

New version 13 projects always record `quick-reveal`; legacy projects retain their original selection. The CTA is a renderer-level tail, not a news scene; it follows the complete payoff exactly once.

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
    "generated_image_size": "720x1280",
    "generated_style": "editorial-realism-or-pictogram"
  }
}
```

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
- `narration`: spoken text.
- `voice_delivery`: `auto`, `contrast`, or `verdict`. `auto` keeps Smart Emotion context; `contrast` applies the Typecast `toneup` preset with restrained lift; `verdict` applies `tonedown` with a slightly lower pitch and slower tempo. Version 12+ continuous-flow projects use `auto` for every scene; only legacy scene-based payoff scenes require `contrast` or `verdict`.
- `image`: optional project-relative path.
- `image_fit`: `auto`, `contain`, or `cover`. `auto` and `contain` preserve the full still inside the evidence-safe region over a dim blurred background. `cover` is an explicit full-bleed crop and must be visually approved.
- `video`: optional project-relative clip path for a new retention format. Do not combine it with `image` in the same scene.
- `video_start`: optional non-negative starting second within `video`.
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

The renderer may extend scene duration when narration audio is longer than requested. Version 12+ continuous-flow generates the complete body narration once, allocates clause-level scene cues, and remuxes the uninterrupted track over hard-cut visuals; scene-level `audio` is rejected. Clip scenes are cropped to 9:16, trimmed to the rendered scene length, and overlaid with the same headline and caption hierarchy as image scenes. Version 4+ stills default to `image_fit: "auto"` and no motion; timed motion affects only the configured emphasis interval below the fixed overlay. Each still-image path may appear in only one scene. Legacy version 3+ fact-stack validation remains available for old projects. Version 4+ rejects unsupported image-fit modes, excessive or unjustified zoom, broken story links, unsafe meme placement, and a missing CTA configuration. Version 5 additionally rejects a missing or generic issue lens, a hook that does not expose the chosen issue, a payoff that does not return to it, or an attention device without a valid scene and reason. Storyboard version 6 with project version 11 rejects a missing or repeated payoff punch or a one-beat payoff narration; legacy scene-based projects also require explicit payoff delivery. Version 13 rejects a first scene longer than 2.5 seconds in final validation and checks the designated rehook against both requested and measured Typecast timing. Version 7 requires the fixed enabled intro and supported transition configuration. The default MP4 output is 720x1280 H.264/AAC.

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
│   └── cta-tail.mp4
├── audio/
│   ├── scene-01.wav
│   └── cta-tail.wav
├── overlays/
│   └── scene-01.png
└── metadata/
    ├── storyboard.json
    ├── rights-manifest.json
    └── sources.json
```

`reference.mp4` is the exact plugin render. `editable.mp4` retains narration, intro, CTA, scene timing, crop, and deliberate motion while omitting the fixed news text overlays from current retention scenes. `captions.srt` is UTF-8 and starts the first cue at the actual intro-to-body transition offset. Each scene MP4 contains its matching narration; WAV files provide separable narration audio; transparent PNG overlays preserve the plugin layout when the external editor supports image layers. `timeline.csv` records the overlapping intro transition and exact measured scene boundaries. `edit-manifest.json` maps every exported file back to its storyboard scene and retains an explicit `round_trip_supported: false` boundary. Overlay text remains rasterized; editors can hide the PNG and rebuild editable text from the CSV or SRT. External edits never mutate or synchronize back to `storyboard.json`.

## `rights-manifest.json`

Contains `searches` and `assets`. `searches` records the query, related scenes, timestamp, outcome, selected asset path, and decision note without archiving bulk results. `assets` contains one provenance record for each storyboard image or clip plus any separate thumbnail presenter. Project version 3+ quick-reveals also require `relevance_level` (`direct` or `contextual`) and a specific `relevance_note` for every used scene visual. Hook, evidence, turn, impact, and payoff beats require `direct`; only a context beat may use a merely contextual place or concept image. A version 4+ reaction meme additionally requires `usage_role: "reaction-meme"` and `meme_origin: "licensed"`, `"owned"`, or `"original"`. A company-identifying asset records `company_names`, `company_visual_type` (`logo`, `official-image`, `licensed-photo`, `branded-product`, or `facility-signage`), and `company_identity_reviewed: true`. A named-person asset records `person_names` and `person_identity_reviewed: true`; it must match a `used` entry in `editorial_grounding.people` and may never be synthetic. A separate thumbnail presenter records `usage_role: "thumbnail-presenter"`, `presenter_context_reviewed: true`, and `case_party: false`; it is not evidence and may never substitute for a named case person. A final render rejects visual assets without an approved manifest record, rejects collected web assets without a canonical source page or usage basis, rejects generated images without `visual_quality_reviewed: true`, and requires at least one approved non-synthetic photo with `news_relevance_reviewed: true` in new projects. Version 6 also rejects a missing company-mention review or a central company without a qualifying used asset in its declared first-mention scene.

## `publish.json`

Stores the copy-ready YouTube upload package. Version 4 adds link-free description validation and exact title/description character counts while keeping version 1, 2, and 3 projects compatible:

```json
{
  "version": 4,
  "title": "검색 핵심어와 사실에 맞는 100자 이하 제목",
  "description": "5,000자 이하의 사실 요약, 링크 없는 출처명, 절제된 해시태그",
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

The displayed title limit is 100 characters and the description limit is 5,000 characters. The deterministic formatter appends up to two normalized values from the front of `tags` to the base title, skips duplicates, and never crosses that title limit. Version 4 descriptions and `source_lines` reject URLs, Markdown links, `www` addresses, and bare domains; descriptions also reject stock-photo provider or license notes, `자료사진` or `해당 단지·사건 사진 아님`, and Typecast, TTS, or synthetic-voice notices. Canonical URLs remain in `sources.json`, asset provenance remains in `rights-manifest.json`, and TTS details remain in `render-report.json`. The formatter displays `current/limit` counts and removes legacy links and production-method boilerplate from copyable output. New projects use `thumbnail_method: "file_upload"`; each render creates a dedicated `thumbnail.jpg` from two or three different rights-approved visuals and records its separate-asset and question-led purpose. The `thumbnail_hook` must be a forceful but supported citizen question; `thumbnail_subhook` carries the verified reversal or consequence; `thumbnail_badge` names one topic-specific tension; and `thumbnail_style` is `auto`, `presenter-led`, or `evidence-led`. A presenter file is optional for `auto`, mandatory for `presenter-led`, forbidden on sensitive stories, and must match a reviewed `thumbnail-presenter` rights record. `video_frame` remains compatible with legacy projects. `playlist` contains a concrete recommendation or `선택 안 함`. `audience` is `made_for_kids` or `not_made_for_kids`. `altered_content` is `yes`, `no`, or the temporary draft value `review_required`; `age_restriction` is `none`, `18_plus`, or `review_required`. A final package must resolve both review states. `visibility` is `private`, `unlisted`, `public`, or `scheduled`; scheduled uploads require an ISO 8601 `schedule_at`. `contains_synthetic_media` records project truth, while `altered_content` records the reviewed YouTube disclosure choice and is not inferred blindly from any use of AI. Keep the pinned comment factual before its discussion question and never manufacture outrage or consensus. Use `upload-package` to render these fields in copy-ready Korean. This is preparation data only; the MVP does not upload, schedule, publish, or post the comment.

## `render-report.json`

Records the rendered video probe, selected TTS provider, model, Voice ID, `voice_name`, automatic/manual `voice_selection` profile, reason, strategy, popularity basis and source, optional `distribution`, `distribution_basis`, and `distribution_bucket`, the project `attention_strategy` issue lens and visual device, administrative-identifier suppression fields, `synthetic_badge: "hidden"`, `scene_transition: "cut"`, `brand_intro`, draft status, narrated `cta_tail`, `editor_package`, the generated thumbnail path, copy, topic badge, source assets, composition, resolved thumbnail style, presenter use and context review, `purpose`, `separate_asset`, and `question_led`, and each scene's timing, `payoff_punch`, `voice_delivery`, and evidence metadata. Report version 3 adds the edit-package path, reference/editable videos, SRT, CSV, scene count, compatibility targets, and the one-way round-trip boundary. Version 9 final validation requires the dedicated question-led thumbnail record; version 13 also requires attention-first style and presenter review metadata when used. Draft and synthetic state are metadata only and do not add on-frame badges. It must never contain the Typecast API key.
