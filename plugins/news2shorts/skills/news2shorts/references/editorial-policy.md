# Editorial policy

## Evidence threshold

- Normal news: at least two independent sources.
- Politics, elections, disasters, crime, health, finance, war, and minors: one primary or official source plus two independent sources.
- A syndicated copy is not an independent source.
- A claim reported by a source remains an attributed claim unless independently established.

## Claim handling

For every factual sentence record a claim ID, the exact supported statement, source IDs, status, and confidence. Use `confirmed`, `attributed`, `disputed`, or `unknown` for status. Never flatten `attributed`, `disputed`, or `unknown` into a confirmed statement in the narration.

For breaking news, preserve an `as_of` timestamp in Asia/Seoul and say when figures may change. If a later correction changes the story, mark the script and rendered output stale before rerendering.

## Language

- Be neutral, direct, and specific.
- Avoid unsupported superlatives and emotional labels.
- Distinguish event time, publication time, and update time.
- Prefer primary documents for numbers, schedules, official decisions, and quotations.
- Do not identify private people beyond what is necessary and responsibly reported.

## Approval

A local draft may be rendered before approval without an on-frame review watermark. Keep its review state in the `preview.mp4` filename, `project.json`, and `render-report.json`. A final local render requires editorial, rights, and synthetic disclosure review flags. Publication remains outside this MVP.
