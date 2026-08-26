# Shorts playbook

## Hook engine

Keep the hook separate from the visual format. Choose one primary hook type:

- `counterintuitive`: a verified result that conflicts with ordinary expectations.
- `result-first`: the confirmed outcome before the explanation.
- `comparison-reversal`: two cases that appear similar until one decisive difference is revealed.
- `change-impact`: what just changed and who feels the consequence.
- `numeric-gap`: a meaningful difference between two verified numbers.
- `issue-tension`: a disputed claim or concrete viewer consequence stated in its strongest accurate form, followed quickly by the condition or reversal that resolves it.

The first spoken line and first visible hook must be the same sourced question. Ask what the verified decision, cost, risk, delay, or failure means for citizens or consumers; never start with a greeting, channel logo, broad background, or neutral news summary.

Before drafting hooks, write one issue lens that survives fact checking:

- `issue_focus`: the underlying contradiction, failed expectation, or measure-versus-problem mismatch. A procedural update such as approval, rejection, reconsideration, or announcement is supporting context unless the procedure itself creates the viewer consequence.
- `viewer_stake`: the concrete citizen or consumer cost, inconvenience, safety risk, rights gap, or fairness concern.
- `tension_question`: one topic-specific citizen question the payoff will answer. Reject generic bait such as `이게 맞나?` or `어떻게 될까?`; name the object, affected people, and unresolved problem.

Complete a specificity and accountability gate at the same time:

- Name the verified central place in the first setting beat. Prefer `제주도`, `제주경찰청`, or the confirmed municipality over `한 지역`, `해당 기관`, or a broad stock location. Keep private addresses off screen.
- List central named people and decide whether each actual photo is rights-safe, privacy-excluded, or rights-blocked before the storyboard is written.
- When sources verify misconduct, omission, or a failed control, connect the exact action to the concrete citizen harm or trust failure. Make that `행위·누락 → 결과` chain the strongest accurate impact beat; do not substitute adjectives, insults, or an invented claim that the public is angry.

Write all three hook candidates as questions. The selected hook, first frame, and first narration must expose this same citizen lens and end with `?`. When the facts support it, `좁은 방은 그대로인데, 욕조 하나면 주거 개선인가요?` is stronger than `욕조 허용안 재검토` because it tests the measure against the citizen's actual problem. Do not use that wording when the source does not establish those premises.

For a new `quick-reveal`, write `shorts_profile.hook_stake` as one sourced sentence answering why the opening figure or claim matters. Reuse at least one meaningful term from that sentence in both the first frame and first narration, and link the first scene to the supporting `claim_ids`. Do not leave a number context-free: use `월 3,300만원에도 의료 공백` instead of only `월 3,300만원`. The number earns attention only when the viewer immediately understands the failed expectation, cost, delay, gap, risk, or public consequence behind it.

For a bolder, referral-worthy opening, make the subject and feared consequence immediately recognizable. Prefer a short disputed-claim question such as `45도면 에어컨이 장식품?` over a vague teaser such as `놀라운 사실이 있습니다`. Keep qualifiers that change the truth in the first evidence beat, and earn share value with a practical payoff rather than an unverifiable `모두가 속고 있습니다` or forced share CTA.

## Ten-second retention contract

Assume many viewers decide whether to leave before 10 seconds. Count from the first frame of the fixed intro, not from the first news scene.

- Keep the first news hook scene at 2.5 seconds or less.
- Start the designated `early_rehook_scene_id` by 10.0 seconds including the intro. It must be an `evidence`, `turn`, `impact`, or `rehook` beat linked to at least one verified claim.
- Write its spoken bridge in `midpoint_rehook`. Reveal one new fact or condition that changes the viewer's first assumption; do not use a generic promise that a reveal is coming.
- Put the one answer deliberately delayed until the payoff in `withheld_detail`. The payoff must visibly and audibly recover it.
- Put truth-changing limits, dates, comparison bases, preliminary status, and uncertainty in `truth_guard`, and speak them no later than the designated early rehook.
- Controlled incompleteness is allowed: show enough verified information to make the question concrete, then delay one bounded answer. Factual ambiguity is not allowed: never remove a qualifier to imply a stronger scandal, accusation, certainty, or public consensus.

## Format structures

### `quick-reveal`

- 0-1s: a concrete citizen question built from the result, contradiction, or A/B comparison.
- By 10s including the fixed intro: one verified partial reveal or interpretation change.
- Next: only the minimum context needed to understand the remaining gap.
- Middle: decisive evidence or reversal.
- 18-30s: answer and consequence.
- Optional close: a natural visual or phrase loop only after the answer.
- Use verified tension: a failed expectation, unresolved gap, public cost, delay, or accountability question. Never convert uncertainty into scandal or imply blame that the sources do not establish.

### `fact-stack`

- 0-1s: the strongest verified result.
- 1-8s: why it matters now.
- Proof stack: at least three distinct verified claims, one claim-led beat at a time, visibly numbered `FACT 1/N` through `FACT N/N`.
- Each proof beat identifies its evidence kind and shows a compact source-grounded label or value; do not count a paraphrase as a new fact.
- 35-70%: a `rehook` or `turn` adds a new condition or changes the interpretation instead of repeating the opening.
- Final third: viewer impact or remaining uncertainty, then a factual payoff whose callback explicitly answers the opening promise.
- If fewer than three claims survive verification, switch to `quick-reveal` instead of stretching the runtime.

### `story-explainer`

- 0-2s: show the unusual outcome or mechanism in motion.
- Early: establish who, what, and the minimum necessary context.
- Middle: add verified constraints, evidence, and one meaningful turn.
- Late: explain how or why the outcome happened.
- Final: fully resolve the opening promise; add a loop only when it feels natural.

## Hook selection

Generate three hooks. Score each out of 100:

- Factual accuracy: 30.
- Issue clarity: 20.
- Viewer stake and tension: 15.
- Curiosity: 15.
- Payoff alignment: 10.
- Spoken naturalness: 5.
- Visual potential: 5.

Reject a hook if factual accuracy is below 27, even when its total is highest. Do not use a question that the video never answers. Do not hide a condition that changes the meaning.

When accurate candidates are close, prefer the one with the clearest issue tension, recognizable personal stake, and most useful payoff to pass along. Do not reward anger, blame, or fear that the evidence cannot support.

Record the selected hook, its open loop, the midpoint rehook, `early_rehook_scene_id`, `withheld_detail`, `truth_guard`, and the final payoff in `project.json.shorts_profile`. The hook earns attention; the payoff must justify it with a verified answer, cause, consequence, or meaning that was not already stated. Reject a conclusion that only paraphrases the hook, repeats its number, restates the persistent headline, or ends with an abstract phrase such as `지켜봐야 합니다` or `변화가 시작됩니다`. State the verified current answer and then its consequence or the exact condition that comes next.

## Dialogue relay

Write narration as one conversation carried across scenes, not as isolated news bullets. Each new beat must briefly answer, challenge, or sharpen the previous beat before handing one unanswered point to the next. Use natural spoken connectors such as `잠깐`, `그럼`, `그런데`, `즉`, or `결론은` only where the logic needs them; do not repeat the same connector mechanically.

In storyboard version 4+, externalize that logic in `story_link`: the hook writes `next_gap`, middle beats write both `answers` and `next_gap`, and the payoff writes `answers` with an empty `next_gap`. These fields are editorial metadata and never appear on screen.

- Keep each scene to one or two short spoken sentences.
- Replace long legislative, case, filing, document, notice, and other administrative identifiers with natural references such as `해당 의안` in narration and display copy. Preserve exact identifiers only in evidence and provenance artifacts.
- Prefer question-and-answer, misconception-and-correction, concrete analogy, and a callback to the hook over reaction filler.
- Let the midpoint turn correct what the viewer was likely assuming.
- Make the payoff sound like the final answer to the opening speaker, then add one useful consequence or check and one short retention punch that is not a paraphrase of either.
- Read the full narration aloud in sequence. Rewrite noun lists, abrupt topic jumps, and consecutive sentences that could be rearranged without changing the story.
- Keep humor in the phrasing and reversal. Never trade factual conditions, victim sensitivity, or source meaning for a punchline.

For a 30-second Typecast Short, normally keep the full narration near 170-190 non-whitespace characters. Estimate runtime before synthesis, then use the draft `render-report.json` as the source of truth. Shorten repeated setup before increasing tempo. A requested 3-second scene that Typecast expands to 7 seconds is a 7-second shot and must be rewritten or split.

## Visual rhythm

- Start content on the first frame; omit a logo intro.
- Use one claim per scene.
- Change composition at semantic beats, normally every 2-4 seconds. Let a shot run longer only when the viewer must read or verify something in-frame.
- Use motion footage where it materially proves or explains the claim. Version 4 stills default to `none`. Use `zoom-in` toward one named emphasis or `zoom-out` for a context reveal, with explicit focal coordinates, `motion_start`, `motion_duration`, and `motion_emphasis`. For a primary person photo, use a face-centered `zoom-in` and about `1.10`-`1.16` `zoom_scale` only when that person is spoken.
- A Short may use no zoom. Do not zoom more than half of still scenes or more than two scenes consecutively. Keep documents, tables, and screenshots static when motion would reduce legibility.
- Join scenes with hard cuts. Do not add fades, wipes, flashes, or other decorative transitions.
- Keep on-screen text shorter than narration.
- Keep captions to two lines where practical and protect the lower/right interface areas.
- Return the final phrase or visual to the opening only when the loop is natural.
- Avoid three or more consecutive generated stills. Keep generated scenes at or below the configured production target, normally 40%. When a draft exceeds it, re-check real photos of named people, official documents, reusable footage, maps, charts, and locally authored evidence cards before accepting the remaining fallbacks.
- Before falling back to a pictogram, consider one rights-cleared reaction meme or original meme card for a harmless context or rehook. Mark it as `visual_role: "reaction-meme"`; never use it as proof, on sensitive harm, or without commercial-use rights.
- For every version 5 retention project, select one primary high-attention device: `reaction-meme`, `contrast-composite`, `consequence-photo`, `evidence-closeup`, or `motion-proof`. Record its scene and why it makes `issue_focus` immediately legible. Prefer the device in the hook, rehook, turn, or impact; a reaction meme may appear only in context or rehook. A document can prove a fact but cannot be the only visual rhythm when a rights-cleared consequence, contrast, or reaction device can make the same issue understandable.
- In a new quick-reveal, require a directly matching visual for every `hook`, `evidence`, `turn`, `impact`, and `payoff` beat. A generic location or topic image is only `contextual` and belongs solely in a context beat. Record the decision as `relevance_level` and `relevance_note`; do not approve an asset merely because it shares the city, industry, or mood.
- Judge directness against the spoken verb. An apology scene needs an apology action or statement, a refund scene needs a refund notice or transaction evidence, and an inspection scene needs the object being inspected. When rights prevent documentary reuse, create an anonymous explanatory reenactment and label it honestly; do not fall back to a generic icon board that makes the caption carry the whole meaning.

## Attention continuity

Every scene must do at least one of these jobs: open a gap, add proof, raise the stakes, change the interpretation, or pay off an earlier gap. Remove scenes that only restate the previous beat.

For location-led reporting, the first context scene must say the actual verified place name aloud and show it in one short visible field. When a real person is central, prefer a rights-cleared actual photo at the meaningful mention; when only a contextual person photo is safe, mark it `사건 당사자 아님` and do not imply identity. In accountability stories, the impact beat should expose the verified action or missing control first and immediately connect it to the affected family's, resident's, consumer's, or taxpayer's consequence.

Make the last non-loop scene the payoff and give it a visible, self-contained conclusion card plus a complete narration close. Visible editorial copy is not narration: write `payoff_title`, `payoff_detail`, `payoff_punch`, captions, and headlines as compact noun phrases. Build the close as three distinct jobs: the verified answer, the verified response or consequence, and a final retention punch that challenges the concrete citizen burden or contradiction. Do not turn non-central unknowns into final-card copy, and reject generic endings such as `미확인`, `확인 중`, `아직 없음`, or `지켜봐야`. Preserve any truth-changing qualifier earlier in narration or `truth_guard`, but finish on what the confirmed facts let a citizen question sharply. Do not use the punch for another summary, generic suspense, insults, or unsupported blame. When a discussion question is justified, keep `discussion_prompt` noun-led and short; a version 6 punch occupies the conclusion card's final zone while the question carries into the later comment CTA.

In narration, state the sourced factual answer first and then speak the punch as a separate second beat. If the facts support a concrete contradiction, accountability question, or disputed judgment, a brief contextual challenge may follow. Use `voice_delivery: "verdict"` for a lower, slower factual payoff, especially on sensitive or preliminary reporting. Use `voice_delivery: "contrast"` only for a safe, supported reversal or challenge. These profiles use documented Typecast presets plus restrained pitch and tempo changes; they do not provide word-level emphasis. Never use shouting, insults, unsupported accusations, an angry preset, or an upbeat challenge that exploits victims. Never replace the verified payoff with a bare question or invent consensus. Read the hook and payoff back to back before rendering; if the payoff sounds like the same sentence rewritten, replace it with the missing answer or consequence. For a preliminary or ongoing story, name the current status and the exact event required before the claimed effect can occur.

- End early beats with forward motion such as “그런데 숫자는 달랐습니다” only when the next scene immediately supplies that number.
- Place the strongest new proof or interpretation change around 40-65% of runtime.
- Alternate evidence types when available: footage, photo, map, document, chart, or disclosed reconstruction.
- In a new fact-stack, connect every proof beat to `fact-sheet.json` through `claim_ids`; use the structured fact counter and evidence card so the proof accumulation remains visible with sound off.
- Keep one promise active at a time. Opening multiple unrelated questions weakens focus.
- Prefer conversational Korean with short clauses and audible contrast. Avoid exaggerated reaction words and empty hype.

## High-retention news pattern

- Put the consequence or surprise in the first headline; do not begin with background.
- Keep one persistent headline when the story has a single strong promise, then advance the facts through `eyebrow` and `ticker` text.
- Emphasize only one phrase with the accent color. Color is hierarchy, not decoration.
- Prefer evidence-rich visuals such as documentary footage, CCTV, maps, documents, or clearly disclosed reconstructions.
- Use an answer or reversal around the middle, then close by resolving the opening promise.
- Create entertainment through honest surprise, contrast, escalation, and explanation. On sensitive harm, replace humor with clarity and respectful tension.
- Do not copy another publisher's logo, font treatment, captions, footage, music, or exact composition.

## Feedback loop

After publication is added in a later phase, compare Shorts only with similar Shorts. Track engaged views, viewed-versus-swiped behavior, average view duration, retention dips, replay spikes, and subscriber conversion. Treat editing cadence as a hypothesis to test, not an algorithm guarantee.
