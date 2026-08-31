# Editorial workflow

## Candidate gate

With no supplied topic, use a 48-hour discovery window and return at most three candidates. A candidate must make `who`, `what happened`, and `why people reacted` concrete. Rank recency first, then event clarity, surprise or tension, observable reaction, and usable visual evidence. Article text and still images are sufficient; an original video is optional.

Search snippets and ranking pages are discovery leads. Open the canonical article, post, broadcast page, or official statement before recording a fact. Stop after the shortlist until the user selects a Candidate ID.

## Title and story

Use a curiosity gap instead of stating the whole conclusion. Useful shapes include:

- `요즘 ○○한다는 ○○`
- `○○가 쉽지 않은 이유`
- `○○에서 반응 좋다는 ○○`
- `너무 비교된다는 ○○`
- `○○하다 걸린 ○○`
- `의외라는 ○○ 근황`

Split the title into a white context line and a yellow withheld result, emotion, or key phrase. Target 8–14 Korean characters per line and never exceed 16.

Write one message in 7–10 spoken beats. With `narration_flow_mode: conversational-chain`, assign `flow_role` in nondecreasing `hook → setup → trigger → explanation → reaction → response → consequence → resolution → aftermath` order. Keep 15 structural scene and caption slots, but default to one stable visual per beat with `pacing_mode: narration-hold`. A beat may own one to three consecutive slots according to its spoken clause count; every slot in that beat repeats the first slot's asset and base visual geometry. When deterministic person motion is enabled, the move continues across those slots without restarting at the caption boundary. Use this timing shape as guidance:

- 0–2s: hook
- 2–7s: event introduction
- 7–18s: background
- 18–30s: central issue
- 30–45s: result, reaction, and current state

Narration should sound like one friend explaining the sequence to another, not like a news anchor reading copy. Do not end narration with formal `합니다`, `했습니다`, `입니다`, or similar honorific report style. Match the connective ending to the beat:

- hook: `했다는데`, `라고 함`
- background: `였는데`, `하게 됐고`
- turn: `말했지만`, `했는데`
- reaction: `라는 반응이 이어졌고`, `라는 말이 나왔는데`
- result: `했다고 함`, `이름이 빠졌다고 함`

Vary the endings so every line does not mechanically end in `함`. Adjacent `~데/~는데` endings and a final `~함 → ~함` pair are invalid. Narration is friend-style editorial commentary, not a transcript of verified facts. It may infer intent, exaggerate a reaction, or use metaphor and slang even when the source does not use that exact expression. For example, `비판이 이어짐` may become `커뮤니티가 난리였고`, and `공식 명단에서 이름이 빠짐` may become `서울시가 박위를 손절했다고 함`. Keep `research.json` as the separate record of sourced facts; narration does not need a one-to-one factual match. When the user supplies a specific punch line or slang expression, retain its meaning and intensity and limit corrections to grammar, spacing, or spoken flow unless the user asks for a rewrite.

Legacy scenes remain within 1–4 seconds. Narration-hold scenes may run 1–7 seconds, and the effective visual hold should normally last about 3.5–6 seconds. When a reviewed WAV exists, end the video with the narration instead of forcing a fixed 43-second runtime. Scene 1 uses the fixed top title without a lower caption. Scenes 2–15 use one or two short lower-caption lines that change by spoken clause while the image stays stable inside the same beat. In `caption_sync_mode: clause`, target 1.3–3.2 seconds per lower caption and never exceed 4.5 seconds.

Write the spoken beat first, split it into consecutive scene narration clauses, and then compress each current clause into its caption. Record an opening `caption_anchor` that begins in the first or second spoken word; the caption must start with that anchor. Preserve the clause's last connective or ending such as `했지만`, `이어지자`, `예고했고`, or `했다고 함` so the on-screen phrase follows the same spoken direction instead of turning into an unrelated noun label. The normalized concatenation of every scene narration in one beat must equal the narration text that is actually handed to TTS. A caption may shorten only the middle of the current clause; it must not summarize a later result, introduce the next beat, or weaken a user-specified colloquial phrase.

When timing a reviewed WAV, place a same-beat follower caption on the first clear spoken-phrase onset, not at the beginning of the preceding silence or a low-level tail. Record the spoken prefix and measured strong-speech onset in that scene's `narration-timing.json` cue. The selected 30fps scene start and measured onset must differ by no more than one frame.

## Visual decisions

For concrete-claim scenes, choose usable incident evidence, official evidence, or a genuine source capture before portraits or contextual imagery. Explicitly set each scene's `visual_requirement` instead of inferring it from structural `role`: an incident trigger may still occupy a background slot. Use `direct_incident` for a concrete event, announcement, cancellation, filing, or official-list change; `direct_subject` for a public-figure identity visual; `contextual` for explanation or transition; and `symbolic_allowed` only when a non-evidence mood or transition image is genuinely intended. In legacy pacing, do not repeat a normalized asset. In narration-hold pacing, consecutive slots in the same beat repeat one asset; cross-beat, non-adjacent, and non-contiguous beat repeats remain invalid.

Open every selected source and normalized file before review. Content approval means the visible subject or statement matches the scene's linked facts without implying that a generated scene is real evidence. Quality approval means the main subject remains identifiable, the important area survives 9:16 normalization, and genuine attribution, original text, and watermarks remain readable at a 360×640 preview. Record `display_focus: subject | source_text | mixed`, preview approval, normalized SHA-256, and for text evidence both readable anchor terms and explicit readability approval. Low-resolution genuine evidence produces a warning rather than forcing an HD synthetic replacement. A review approval is not a rights approval.

The CapCut template is the only layer for editorial titles and lower captions. Never bake a summary, sentence, date badge, category label, source footer, or other newly written copy into a scene image. Genuine article, broadcast, social, or official-page captures may retain their original text, attribution, and watermarks because those are source evidence rather than duplicate editorial copy. Synthetic images must be entirely text-free, including letters, numbers, logos, pseudo-text, dates, labels, and watermarks, and must be visually inspected before registration with `--synthetic --text-free`.

For wide photos or video frames, keep the meaningful image centered and use an enlarged blurred copy as the 9:16 background. A community capture is different: automatically use `community-capture-safe`, or explicitly pass `collect-assets --community-capture` for an unrecognized host. It keeps the entire original capture inside a centered 1000×1056 maximum foreground box that survives the CapCut template crop. Never use `portrait_fill`, edge crop, or a zoomed partial screenshot for a community capture. Recollecting an existing asset in this mode regenerates its normalized PNG and invalidates its quality/readability approval until it is reviewed again. Do not use the wide-photo treatment for document, article, post, or official-page text that must be read. For those screens, crop only original pixels into a 1000×720 white readable-source card with `compose-readable-source`; omit irrelevant navigation, surveys, ads, and faces, but keep the source context and required anchor phrases. Never retype or regenerate source text and never recreate a fake article screenshot.

The final CapCut review is a separate proof level from static validation. Inspect one actual player frame at every beat midpoint. Both title lines must remain visible through the end, scene 2–15 captions must be present, and text-evidence anchors must be readable at player size. Same-beat followers must share both base segment geometry and video-material crop. Public-figure editorial animations additionally require player-size confirmation of the obvious stylization, visible horizontal eye-band, and ruler ticks. Capture the start and end of every motion beat, plus the frame immediately before and after every split-slot motion boundary; approve slow movement, face-safe framing, title/caption clearance, exact continuity, no black frame, and no visual jump. Record the screenshots and current semantic visual-timeline, storyboard, and capcut-map hashes in `handoff/final-visual-qc.json`; any later change requires a fresh review.

With `person_visual_mode: stylize-or-remove`, a visible public figure must use a text-free `editorial_animation` made directly from a reviewed non-synthetic `source_photo`, `official_evidence`, or `source_capture`. Preserve identity, clothing, expression, location, and factual context; do not add an unobserved action or relationship. With `public_figure_style_mode: obvious-editorial-eye-band`, the derivative must be clearly stylized at 360×640 preview size and carry a visible horizontal `editorial-ruler-eye-band`. Record `portrait_style_strength: obvious-editorial`, `portrait_eye_motif: editorial-ruler-eye-band`, and review approvals for obvious style, motif presence, visible ruler ticks, and its editorial-only meaning. The eye-band does not make the person non-identifying and does not provide consent, licence, or portrait/publicity-right clearance; never mark it `non_identifying` or change `rights_status` because of the motif. Crop incidental faces completely out of article and official-page captures. Private people, minors, victims, and staff never receive a recognizable synthetic likeness or the eye-band treatment; use a reviewed `non_identifying_fallback` with an explicit reason. Record the displayed result as `editorial_animation`, `cropped_out`, `non_identifying`, or `none_visible`; keep the original evidence asset separately.

With `person_motion_mode: subtle-deterministic`, build a hash-stable motion plan only for storyboard-selected assets whose `evidence_role` is `editorial_animation`. Choose a slow zoom in/out, left/right pan, or restrained combined move; limit zoom to about 4% and horizontal travel to about 1.5% per side. Keep source-text cards, incident evidence, contextual screens, and `non_identifying_fallback` screens static. For a beat split across multiple slots, interpolate one motion across the whole beat so the follower starts at the leader's exact end value. Preserve the canonical template crop and base geometry, and verify the generated root/template/mini keyframes rather than adding motion manually to the reusable base template.

## YouTube copy handoff

With `project.json.youtube_upload_mode: copy-handoff`, write the upload copy after the research, storyboard, and visual treatment are settled. Keep this project-level so upload-copy edits do not invalidate storyboard-bound visual QC. Keep the upload title within 100 characters and the description within 5,000 characters. Produce one to five compact hashtags, separate search tags without `#`, a conversational pinned comment, the matching white/yellow thumbnail lines, category, Korean language, audience choice, altered-content choice and reason, recommended visibility, and one to five representative `research.json` source IDs. If `publish_blocked` is true, recommend `private` and label the copy as a local draft rather than publication-ready. The audience and altered-content choices must be explicit; do not silently inherit them from a channel default.

Write both `handoff/youtube-upload.json` and a copy-friendly `handoff/youtube-upload.md`. The Markdown file separates public title/description/comment text from internal upload settings and source evidence. In the final result, show every field instead of returning only a path. Creating upload copy does not authorize rendering, account access, upload, scheduling, visibility changes, or publication.

## Sound handoff

Use five to eight SFX cues across the hook, turn, key evidence, reveal, and ending. Leave ordinary explanation scenes silent. `init` creates seven short local SFX presets; the human editor places them from `handoff/sfx-cues.csv`.

The default BGM mode is `none`. A user-supplied `--bgm-file` is copied into the project but not inserted into native CapCut audio JSON.

cc-helper does not generate TTS. With `narration_performance_mode: reviewed-external`, the editor supplies an externally generated Typecast WAV and `handoff/narration-performance.json`. The performance file binds `handoff/narration-typecast.txt`, the WAV, and `handoff/narration-timing.json` by path and SHA-256, and separately binds the ordered storyboard beat narration. Its beat list must exactly match the storyboard beat order; for the current 10-beat project this means 10 performance rows. Every row records `emotion_type`, optional `emotion_preset`, `tempo`, `pause_after_seconds`, and `measured_pause_after_seconds`. Validation derives pause length again from the WAV at -40 dB with a 0.08-second minimum. Tempo must stay within 0.90–1.10, non-final pauses within 0.12–0.40 seconds and within 0.10 seconds of the plan, the recorded measurement within 0.04 seconds of the WAV, and the final pause must be zero. The timing source may be `typecast_timestamp_review` or `capcut_waveform_review`.

Record measured integrated loudness and true peak, then re-measure the current WAV during validation. Accepted audio is -18 to -14 LUFS with true peak at or below -1 dBTP. An automated review may approve only profile variation, measured pauses, timestamp alignment, loudness, and true peak; it leaves a human-listening warning. Human listening approval separately covers naturalness, dynamics, breathing, pronunciation, pace, and absence of audio artifacts. Both review kinds bind script/audio/timing hashes and the storyboard-narration hash. Replacing any bound input makes the review stale. This validation contract does not turn cc-helper into a Typecast client and does not authorize narration generation.
