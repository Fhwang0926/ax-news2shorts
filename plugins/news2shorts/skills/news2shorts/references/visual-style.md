# Visual style

All new formats use the same mandatory reference-derived composition: a black top quarter with one persistent, large, extra-bold, center-aligned two-line headline, a changing full-height 9:16 evidence image or clip behind it, and a lower yellow outlined caption. This retains the observed information hierarchy without copying another channel's logo, footage, narration, font, music, captions, or shot sequence.

- Set `visual_style.display_headline` to the short factual promise that stays on every scene; it falls back to the project title only when unset.
- Use `visual_style.headline_highlight` for one exact phrase in that fixed headline. The default accent is `#FFF200`.
- New projects use `visual_style.screen_copy_mode: "noun-phrases"`. Write all visible editorial copy as compact noun phrases and keep full Korean sentence endings in narration only. Prefer `제품 굳음 · 원인 미확인` over `제품이 굳었지만 원인은 확인되지 않았습니다`.
- Keep the persistent headline at 22 Korean characters or fewer so the centered headline stays visually dominant without sentence-breaking wraps.
- Keep each ordinary scene at four seconds or less in the storyboard and normally 4.5 seconds or less after Typecast synthesis, so the evidence changes every three to four seconds. Keep the rendered payoff near 3.5-6 seconds.
- Do not add a brand lockup, intro, decorative progress label, draft watermark, or synthetic-media badge to the news layout. The exceptions are the compact `FACT N/N` proof counter and the separate common CTA tail appended only after the completed payoff. Keep synthetic status in the project, rights, publish, and render metadata instead.
- Replace the ordinary outlined caption on the last non-loop payoff with one opaque dark editorial conclusion card. Fully hide background panels, frames, and lines inside its bounds so they cannot read as extra cards. Start directly with the large white `payoff_title`; do not draw a `결론` badge, top accent bar, or other decorative header. Put the practical meaning or next check in a large bold yellow `payoff_detail`, not small footnote text. Give `payoff_title`, `payoff_detail`, divider, and `discussion_prompt` separate reserved vertical zones so no role can overlap another. When sourced public reaction is editorially relevant, add one separate large yellow `discussion_prompt` below the restrained divider; it must follow, not replace, the factual answer. Keep the scene visible for at least 3.5 seconds.
- Show `뉴스 출처: <publisher>` in small type near the bottom of each scene. Keep the asset/license credit separately above it when needed.
- Keep each still's full source visible by default with `image_fit: "auto"`; the renderer places it inside the evidence-safe region over a dim blurred copy of the same source. Use `contain` when edges, text, people, or document bounds must be preserved. Use `cover` only for a deliberate full-bleed crop approved during visual review.
- Use hard cuts between scenes. Do not use fades, wipes, flashes, zoom transitions, or other scene-to-scene effects.

## Composite thumbnail

For every video result, create one dedicated JPG thumbnail that is separate from the MP4 and is never a selected video frame. Combine two or three different rights-approved news visuals, use strong black, yellow, red, and white contrast, and lead with a large concrete citizen question. Add one short topic-specific red badge and a sourced subhook that names the number, condition, contradiction, or citizen consequence without disclosing the entire payoff. Reject generic badges such as `충격`, `속보`, and `이게 맞아?`.

For an ordinary non-sensitive story, prefer `thumbnail_style: "presenter-led"` when a polished rights-approved presenter portrait is available. Use the presenter on one side as a visual narrator and keep the direct news evidence visible on the other side. The presenter must be user-owned, licensed for the intended use, or an original synthetic persona; it must be recorded as `usage_role: "thumbnail-presenter"`, `presenter_context_reviewed: true`, and `case_party: false`. Label it as a presenter image so it cannot be mistaken for the reporter, witness, victim, suspect, official, or other case party. Do not use a broadcaster, celebrity, named-person likeness, unrelated web face, or stock preview. Sensitive stories and projects without a safe presenter use `evidence-led`. `auto` selects presenter-led only when that reviewed asset exists.

A lower-resolution source or generated base is acceptable when it remains clear at Shorts size; the renderer's default output remains 720x1280. The thumbnail may be provocative and click-oriented, but it must not add an unsupported accusation, fake urgency, invented public reaction, unrelated face, or misleading before-and-after pairing. Controlled incompleteness may withhold one bounded answer, but must keep every truth-changing qualifier. Generated visuals remain subject to the same quality and disclosure checks, and all source images must already be approved in `rights-manifest.json`.

## Primary attention device

Every version 5 retention project selects one primary high-attention visual that makes the verified issue lens legible without narration:

- `reaction-meme`: a brief licensed, owned, or original reaction on a harmless context or rehook beat; never factual proof.
- `contrast-composite`: two rights-approved visuals combined to show the failed expectation or before-versus-result contrast.
- `consequence-photo`: a directly relevant, rights-cleared photo that shows who or what bears the practical impact.
- `evidence-closeup`: a deliberate crop or timed close inspection of the decisive object, number, document detail, or condition.
- `motion-proof`: rights-cleared footage whose movement proves the mechanism, mismatch, or consequence.

Record the type, scene ID, and editorial reason in `shorts_profile`. Put non-meme devices on a hook, rehook, turn, or impact beat. Do not treat a generic location, decorative pictogram, bland press document, unrelated reaction face, or ambient zoom as the primary device. A document remains useful evidence, but pair it with a consequence or contrast visual when the story's issue would otherwise feel procedural and emotionally flat.

## `quick-reveal` + `continuous-flow` (new projects)

Use for a single comparison, reversal, or answer that can pay off quickly.

- Target 12-35 seconds and 4-9 scenes.
- Put the result or visible contradiction in the first frame.
- Fill `shorts_profile.hook_stake` with the sourced reason the opening figure or claim matters. The first display copy and first narration must share a meaningful term from it, and the first scene must link its supporting `claim_ids`. Never show a context-free number as the whole promise.
- Use the shared lower outlined caption and no more than one primary idea per scene.
- Keep ordinary scenes at four seconds or less.
- Stop after the answer; do not pad the runtime with background facts.
- End on a visible answer, cause, consequence, or meaning; never repeat the opening claim as the payoff.
- Use `relevance_level: "direct"` visuals on hook, evidence, turn, impact, and payoff beats. Reserve `contextual` place or concept imagery for a context beat only, and add a specific `relevance_note` to every used asset.
- Match visuals to the scene's predicate, not merely its topic noun. Write `subject + action + visible result` in `relevance_note`, then confirm the frame communicates all three without the caption. Prefer a visible apology, refund notice, inspection action, changed menu, damaged object, named person, or direct comparison over an icon grid that only suggests the category. If no reusable documentary image is permitted, use an anonymous original/generated explanatory scene with clear disclosure and no real-person implication.

## `fact-stack`

Use for current updates, verified number sequences, and proof-led news.

- Target 20-55 seconds and 6-12 scenes.
- Keep one factual promise active in `visual_style.display_headline`.
- Use at least three proof beats linked to three distinct fact-sheet claims. Number every proof beat consecutively from `1/N` through `N/N`; the renderer draws a compact `FACT N/N` pill.
- Give every proof beat an `evidence_kind` and `evidence_label`. Add `evidence_value` when a number or comparison is the proof; the renderer replaces the ordinary lower caption with a structured evidence card.
- Keep `caption_focus` to one exact phrase inside `caption` when a compact factual phrase needs yellow emphasis. Do not tint the whole sentence.
- Put a real change of interpretation in a `rehook` or `turn` scene around 35-70% of runtime.
- Add `payoff_callback` to the last non-loop payoff so the conclusion card visibly reconnects the opening promise to the answer. Place the callback completely above the card with at least a small safe gap; no callback glyph or background pill may touch or sit behind the opaque card.
- Keep ordinary scenes at four seconds or less.

## `story-explainer`

Use for mechanisms, reconstructions, escalating incidents, and stories whose answer needs context.

- Target 35-120 seconds and 8-20 scenes.
- Show the unusual result or mechanism before explaining it.
- Advance through context, evidence, turn, impact, and payoff; do not front-load background.
- Keep ordinary scenes at four seconds or less.
- Use moving footage when it proves the action and stills when the viewer must inspect a detail.

Configure a new format in `project.json`:

```json
{
  "shorts_profile": {
    "hook_type": "counterintuitive",
    "hook": "자동주차보다 한 단계 더 갔습니다.",
    "hook_stake": "주차 공간 부족을 차량 이동 방식 자체로 줄이는 기술입니다.",
    "issue_focus": "주차 공간 부족을 운전자 이동이 아니라 차량 운반으로 줄이는 발상입니다.",
    "viewer_stake": "주차 대기와 이동 불편을 줄일 수 있는지가 핵심입니다.",
    "tension_question": "로봇이 차를 옮기면 주차 공간 부족이 실제로 줄어드나요?",
    "visual_attention_device": "motion-proof",
    "visual_attention_scene_id": "scene-03",
    "visual_attention_reason": "두 로봇이 차량을 들어 옮기는 동작이 주장과 차이를 직접 증명합니다.",
    "open_loop": "차를 옮기는 방법은 예상과 다릅니다.",
    "midpoint_rehook": "그런데 로봇 한 대가 움직이는 게 아닙니다.",
    "payoff": "두 대가 한 조로 차를 들어 옮깁니다.",
    "loop_close": "그래서 주차장이 차를 직접 옮긴다는 말이 나옵니다."
  },
  "visual_style": {
    "template": "fact-stack",
    "brand_name": "",
    "accent_color": "#FFF200",
    "display_headline": "주차장 운반 로봇",
    "headline_highlight": "운반 로봇",
    "screen_copy_mode": "noun-phrases",
    "show_fact_stack_index": true,
    "show_payoff_label": true,
    "payoff_panel_style": "editorial-card",
    "show_source_label": true
  }
}
```

Configure each beat in `storyboard.json`:

```json
{
  "id": "scene-03",
  "duration": 3.0,
  "beat": "evidence",
  "progress": "",
  "fact_index": "1/3",
  "eyebrow": "첫 근거",
  "headline": "주차장 운반 로봇",
  "headline_highlight": "운반 로봇",
  "caption": "운반 로봇 2대",
  "caption_focus": "운반 로봇",
  "claim_ids": ["claim-01"],
  "evidence_kind": "video",
  "evidence_label": "공식 시연",
  "evidence_value": "2대 1조",
  "payoff_title": "",
  "payoff_detail": "",
  "payoff_callback": "",
  "discussion_prompt": "",
  "story_link": {
    "answers": "로봇 수량",
    "next_gap": "차량 이동 방식"
  },
  "visual_role": "evidence",
  "narration": "먼저 차량 아래로 들어가는 로봇은 두 대가 한 조입니다.",
  "image": "",
  "image_fit": "auto",
  "video": "assets/collected/official-demo.mp4",
  "video_start": 2.4,
  "motion": "none",
  "motion_start": 0,
  "motion_duration": 0,
  "motion_emphasis": "",
  "focus_x": 0.52,
  "focus_y": 0.48,
  "zoom_scale": 1.0,
  "audio": "",
  "credit": "출처와 사용 근거를 짧게 표시",
  "source_label": "제조사 공식 자료",
  "source_ids": ["source-01"],
  "synthetic": false
}
```

Only proof beats use the fact counter and evidence card; hook and payoff scenes may leave those fields empty. `claim_ids` must reference existing `fact-sheet.json` claims, and the counter must be a complete sequence such as `1/3`, `2/3`, `3/3`. Keep `evidence_label`, `evidence_value`, and `payoff_callback` as short noun phrases. Version 1-2 storyboards keep their legacy rendering behavior.

Use exactly one of `image` or `video` per scene. Every still image must be unique within the Short; a copied file, alternate crop, or generated derivative of an already used still does not count as a new visual. `video_start` is the starting second within a local clip. The renderer crops footage to 720x1280, trims it to the scene duration, freezes the last frame when necessary, and discards the clip's original audio in favor of the configured narration.

When a central politician or public official is named, prefer a rights-cleared real photo at that person's first meaningful mention. Do not generate a likeness of a named public figure. If no asset-specific reusable photo exists, keep the person off-screen and use a relevant official document, chart, footage, or clearly explanatory graphic with the failed search recorded.

For version 4+ still images, default to `motion: "none"`. A zoom is optional and must be a timed emphasis, not ambient motion. When a real person is the primary subject and their identity or reaction is spoken, use `zoom-in`, focus near the face, and normally set `zoom_scale` around `1.10`-`1.16`:

- `zoom-in`: emphasize a specific person, object, number, or consequence.
- `zoom-out`: reveal surrounding context or scale.
- `none`: preserve documents, charts, screenshots, maps, and other evidence that must remain legible.
- `slow-zoom`: legacy alias for `zoom-in`.

Use normalized `focus_x` and `focus_y` values from `0.0` to `1.0` to keep the motion centered on the relevant subject. Use `zoom_scale` from `1.0` to `1.25`; keep ordinary explanatory images near the `1.055` default and reserve stronger values for a deliberate subject push-in. The renderer moves only the evidence image; the top headline, lower caption, and credit remain fixed. Draft and synthetic state are kept in metadata rather than on-frame badges. Generated stills and final MP4 output default to 720x1280.

Every version 4+ zoom also sets `motion_start`, `motion_duration`, and `motion_emphasis`. The image stays static before `motion_start`, moves only for `motion_duration`, and then holds. `motion_emphasis` names the matching spoken person, number, object, result, context, or scale reveal. Do not zoom more than half of still scenes or more than two scenes consecutively.

After the payoff, version 4+ renders append one common CTA tail. It uses the same restrained black and yellow hierarchy, contains no news claim or source label, and does not reduce the payoff's required reading time. The same selected Typecast voice says `구독과 좋아요 누르면, 빠른 소식 전해드릴게요.`; measured speech may extend the tail up to six seconds. An explicit `--no-tts` review render retains the visual tail with the built-in cue only.

In noun-phrase mode, keep the headline at 22 Korean characters or fewer and captions at 24 or fewer. Use `headline_highlight` for one exact phrase only. Put credits and the small news-source label on screen. The source label identifies the reporting evidence; the credit identifies who owns or licensed the visual. Because no synthetic badge is drawn, generated scenes must remain clearly illustrative and their disclosure metadata must be complete.

For the payoff card, keep `payoff_title` under 22 Korean characters and write the verified answer as a noun phrase. Keep `payoff_detail` under 34 characters and use a second noun phrase for the viewer consequence or verified response. Use `payoff_punch` for a concrete contradiction or citizen burden such as `정보 오류, 소비자 부담?`, not a generic uncertainty label such as `미확인`, `확인 중`, `아직 없음`, or `지켜봐야`. Keep `discussion_prompt` under 14 characters and noun-led; put the full contextual challenge in narration after the factual answer. Do not use a context-free `이게 맞나?`, imply that all citizens agree, or let the question replace the factual answer. Do not combine these fields into one long sentence; the renderer assigns them separate visual hierarchy.

## Legacy layouts

- `broadcast-card`: retained for older broadcast-card projects. It uses a persistent headline, center image, and ticker band.
- `classic-card`: retained only for older full-background card projects.

Legacy layouts accept image scenes only. New clip scenes require `quick-reveal`, `fact-stack`, or `story-explainer`.
