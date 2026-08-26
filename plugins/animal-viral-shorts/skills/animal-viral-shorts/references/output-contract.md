# Output contract

Project status:

    source_selected
    source_pending
    source_acquired
    source_review_ready
    source_reviewed
    stories_ready
    story_selected
    composed
    render_ready
    rendered_draft
    draft_approved
    rendered_local

Core project files are project.json, source.json, source-analysis.json, story-options.json, story-options.md, selection.json, script.json, storyboard.json, music-plan.json, rights-manifest.json, edit-plan.md, draft-render-report.json, draft-review.json, render-report.json, delivery-note.md, youtube-upload.json, and youtube-upload.md.

Media and preview assets stay under assets. Rendered media stays under outputs. Project-relative paths may not escape the project root. Existing generated files require --overwrite.

Final validation requires:

- explicit user source and story selections;
- exactly three passing story options;
- actual observation IDs for every scene and payoff;
- setup, build, turn, and payoff in order; a turn before 75 percent; and a real payoff last;
- a separate evidence score and entertainment score of at least 75;
- at most 59.5 seconds and 4–12 scenes; archetype duration ranges are not hard gates;
- one emphasized lower message and one scene music cue per scene;
- a supported visual preset, with project, selected story, and storyboard values kept consistent;
- for `observation-contrast-v1`, one reviewed-subject label per scene, ordinary scenes at most three seconds, and a final scene at most four seconds;
- source excerpt and local-review rights limits;
- TTS, narration, and vocals disabled;
- a valid scene-aware synthetic or licensed no-vocal music plan;
- only supported renderer-generated no-vocal `question_pop`, `soft_whoosh`, or `bass_drum` SFX at valid scene times;
- reviewed, time-bounded, right-safe Korean source-caption overrides marked as non-observation;
- a final 0.5–1 second held source frame;
- one 1.8-second silent subscribe/like CTA shot after the conclusion, included in the 59.5-second limit.

render --draft creates rendered_draft. approve-draft records story-fit and music-fit; both must pass to enter draft_approved. Only then can a non-draft render create rendered_local.

Final render proof covers codec, dimensions, duration, audio presence, frame rate, nonblack ending, generated SFX events, and translation-override counts. It also writes editable YouTube upload information with a creator-neutral public description and review-required audience, altered-content, promotion, age, and rights fields. Creator provenance remains in internal source and rights files plus on-video attribution. Draft approval records a user's editorial and listening decision but does not establish rights, fact truth, welfare expertise, publication, monetization, or performance. No upload is performed.
