# Observation and story inputs

## Reviewed observations

The observe input requires summary, species, subjects, at least two observed_behaviors, at least two timed observations, sensitive review, source-caption regions, protected regions, and a reviewer note.

Each observation contains:

    {
      "id": "obs-01",
      "start_seconds": 0.0,
      "end_seconds": 2.4,
      "subject": "앞쪽 개",
      "action": "장애물 앞에서 멈춘다",
      "visible_evidence": "앞발을 고정하고 장애물을 바라본다",
      "confidence": "observed"
    }

confidence is observed, caregiver_report, or inference.

Protected and caption regions use normalized x, y, width, and height. Caption regions also have an ID and radius from 4 to 40. A caption region must not overlap watermarks, animal_faces, or human_faces.

Sensitive rescue, illness, abuse, injury, death, or treatment requires two fact_sources, each with url and supports.

## Story options

The stories input is an array or object with exactly three stories. Each option requires:

- id and one supported archetype;
- hook and headline line1, line2, accent_phrase;
- perspective, viewer_question, one fun_mechanism, and relationship_roles;
- narrative_arc with setup, build, turn, and payoff text;
- 4–12 beats containing setup, build, turn, and payoff in order;
- turn and payoff;
- duration_target_seconds at or below 59.5 seconds; archetype ranges are guides only;
- music_mood;
- risk note and false invented_dialogue / unsupported_emotion flags;
- all six evidence score components and all six entertainment score components.

Each beat requires id, role, act, source_start_seconds, source_end_seconds, output_duration_seconds, caption, caption_style, emphasis_phrase, observation_ids, focus_point, continuous_action, visual_change_count, music_cue, music_mood, and source_audio_priority. source_caption_region_id, source_caption_overrides, and sfx_events are optional. `subject_label` is conditionally required by `observation-contrast-v1`.

For `observation-contrast-v1`, every beat's `subject_label` must be a 2–12 character noun phrase that matches `source-analysis.subjects` or the subject of an observation referenced by that beat. Do not use dialogue punctuation, an exclamation, inferred emotion, intent, or an unsupported character role. Ordinary beats are at most three seconds and the final beat is at most four seconds including its held frame. The normalized story records the project visual preset; input authors do not override the project preset per story.

Each source_caption_overrides item requires source_text, Korean text, a local start_seconds/end_seconds window, a canvas-normalized canvas_region, reviewed_safe true, and not_observation true. Use `원문 번역` for literal wording or `원문 의역` for natural, playful Korean wording that preserves the same event and meaning without adding identity, motive, or outcome. The renderer shows it only during that window. Each sfx_events item uses question_pop, soft_whoosh, or bass_drum with a scene-local offset_seconds and gain_db from -24 through 0. Use bass_drum only for a reviewed weighty entrance, contest turn, or payoff.

act is setup, build, turn, or payoff. caption_style is question, buildup, turn, or payoff. emphasis_phrase must occur in caption. music_cue is intro, build, steady, drop, impact, or release. source_audio_priority is high, normal, or low.

The first beat is a setup hook and the last beat is payoff or conclusion. Include a turn beat early enough to start before 75 percent of the output. Source excerpts are at most eight seconds each. For a scene over five seconds, continuous_action must be true and visual_change_count at least two.

The selected story's beat durations must sum to duration_target_seconds within 0.75 seconds. The final beat must reserve 0.5–1 second beyond its usable source input so the renderer can hold a reviewed final frame.

Evidence score components and maxima:

- evidence_grounding: 25
- first_1_5s_hook: 20
- state_change_density: 20
- payoff_clarity: 15
- relationship_roles: 10
- loopability: 10

The total must be at least 75. All observation IDs must exist in source-analysis.json.

Entertainment score components and maxima:

- hook_curiosity: 15
- build_escalation: 20
- rehook_strength: 15
- turn_surprise: 20
- payoff_satisfaction: 20
- replay_comment_potential: 10

The entertainment total must also be at least 75. The three options must use three different fun_mechanism values from race-comparison, escalating-wait, delayed-reveal, synchronized-reaction, rule-break, callback, and before-after-contrast. Scores are editorial comparisons, not performance predictions.
