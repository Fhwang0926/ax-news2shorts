# Research workflow

## Selection gate

Accept only a Candidate ID that the user explicitly selected from a `shortlist.json` artifact. A score, rank, prior assistant recommendation, or available source URL is not a selection.

## Source graph

Start from the selected candidate post, then add only directly inspected or independently corroborated nodes. Use edges such as `published_by`, `reports`, `reposts`, `quotes`, `responds_to`, and `contains_asset`. Keep origin `unknown` or `probable_original` when authorship cannot be established.

For every source record the public URL, publisher, source type, event and publication time when known, collection time, evidence, rights state, and optional SHA-256 and archived paths. Do not treat the earliest surviving post as automatically original.

## Browser evidence

Use the cheapest reliable surface:

1. Purpose-built connector, API, RSS, or direct public document.
2. Browser DOM and exact visible element inspection.
3. Browser or Computer Use for dynamic comments, video positions, infinite scroll, or state that cannot be verified structurally.

Capture page or element evidence only for the selected story. Store the surrounding context separately from any production crop. Do not archive unrelated account or page data.

## Claims

Use these statuses:

- `verified`: sufficiently established by the required sources.
- `likely`: supported but not fully established; narration must preserve the qualifier.
- `unconfirmed`: insufficient evidence.
- `contradicted`: credible sources conflict.
- `opinion`: interpretation rather than fact.
- `reaction_only`: public reaction or comment evidence.

Only `verified` and `likely` claims may be linked to factual narration. Health, crime, death, disaster, finance, politics, war, or minors require one primary or official source plus two independent sources before marking a claim `verified`.

## Assets and comments

Keep raw and derived assets separate. Record source IDs, original URL, creator when known, retrieval time, SHA-256, dimensions or duration, watermark state, relevance, derivation, local paths, and rights status.

Comments are optional. Prefer a representative reaction, official reply, or research lead. Raw evidence should retain enough context to show where the comment appeared. Production derivatives should mask ordinary usernames and profile photos unless their identity is necessary, public, and reviewed.

## Story and timeline

Generalize the reference channel's structure rather than copying its wording:

1. Recognizable subject or abnormal signal.
2. Necessary situation.
3. Escalation or failed expectation.
4. Direction-changing fact.
5. Verified payoff or official response.
6. Short grounded close.

Every factual narration segment links to claim IDs. Every scene links to its narration segments and relevant claims, sources, assets, and optional comments. Use renderer-neutral properties only; do not write CapCut, Remotion, or FFmpeg-specific commands into `timeline.json`.
