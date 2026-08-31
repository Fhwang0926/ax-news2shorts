---
name: global-shorts-producer
description: Discover selectable candidates from the Brainbulb channel Shorts tab, then turn one chosen Korean YouTube Shorts signal into a source-verified, original en-US Shorts script, storyboard, subtitles, asset search plan, and CapCut handoff manifest. Use for 뇌전구 Shorts discovery, Korean-viral-to-global reframing, or Shorts Globalizer requests. Do not use for automatic selection, channel monitoring, translation overlays, media downloads, TTS, rendering, CapCut draft edits, or upload.
---

# Shorts Globalizer

Use a Korean Shorts URL as a topic signal, not as reusable footage or factual proof. The result is an editable, publication-blocked English production draft.

## Start

Run the local preflight:

```text
python3 <plugin-root>/scripts/globalize.py doctor --json
```

Read [workflow.md](references/workflow.md) before research or English writing. Read [project-contract.md](references/project-contract.md) before editing project JSON or packaging. Read [editorial-and-rights.md](references/editorial-and-rights.md) for origin, sensitive-topic, originality, and rights decisions.

## Workflow

1. If the user asks to get a topic from the 뇌전구 channel and has not supplied a Shorts URL, run:

   ```text
   python3 <plugin-root>/scripts/globalize.py discover
   ```

   Show up to three candidates from channel ID `UCbr855WAFQvAX-An7IcHFXg`'s `/shorts` tab and stop for one explicit selection. Do not rank or auto-select by recency or views. Discovery is one-time and must not create a project, schedule, or monitor.
2. Accept the selected or user-supplied single public YouTube Shorts URL. Initialize the project:

   ```text
   python3 <plugin-root>/scripts/globalize.py init --url <url>
   ```

   The URL itself counts as topic selection. The command collects public metadata and Korean captions without downloading video or using cookies/login.
3. Caption HTTPS requests must retain certificate verification. The CLI uses Python's trusted CA first and an installed `certifi` CA only when the default CA file is unavailable; never disable TLS checks. If the result is `transcript_pending`, re-running the same `init` may resume only that exact pending project when a verified public caption or user-authorized UTF-8 transcript is now available. Other existing project states remain overwrite-protected. If captions are still unavailable, stop and request an authorized transcript file; never install ASR, download the video, or use an unrelated transcript.
4. Analyze the transcript into event facts and functional beats, then research canonical sources. The signal Short is never one of the fact sources. Write `source-analysis.json`, `sources.json`, and `fact-sheet.json` according to the contract.
5. Validate and score:

   ```text
   python3 <plugin-root>/scripts/globalize.py validate --project-dir <dir> --stage research
   python3 <plugin-root>/scripts/globalize.py score --project-dir <dir>
   ```

   `GLOBAL_REPOST` and `SKIP` stop here. `REVIEW`, `HOLD`, and every sensitive topic require explicit research approval before writing English content.
6. When research approval is required, show the verified event, origin, score, uncertainties, and sources. After explicit approval run:

   ```text
   python3 <plugin-root>/scripts/globalize.py approve --project-dir <dir> --stage research --confirm
   ```

7. Reframe rather than translate. Create three angles, five titles, three hooks, one 80–120 word en-US script, and eight to ten scenes totaling 30–40 seconds. Link every paragraph and scene to usable claim IDs. Assets remain search plans with empty paths.
8. Complete `originality.json`. Use the ordered claim IDs and beat roles for the deterministic structure score. Compare hook, conclusion, information order, and expression semantically. Rewrite until `validate --stage script` passes with `originality.decision: PASS`.
9. Present the script and scene plan, then stop for explicit script approval. After approval run:

   ```text
   python3 <plugin-root>/scripts/globalize.py approve --project-dir <dir> --stage script --confirm
   python3 <plugin-root>/scripts/globalize.py package --project-dir <dir>
   python3 <plugin-root>/scripts/globalize.py validate --project-dir <dir> --stage package
   ```

10. Return the project path, score/decision, source confidence, package files, asset rights warnings, and `preview_approved: false`, `publish_blocked: true`.

## Boundaries

- Do not copy or translate the source transcript sentence-by-sentence, preserve its information order, or reuse its visuals, captions, audio, thumbnail, or branding.
- Do not fetch the channel's Videos tab, auto-select a candidate, or turn one-time discovery into monitoring.
- Do not invoke or modify `cc-helper`, `news2shorts`, or their CapCut templates. `capcut-manifest.json` is a logical slot handoff only.
- Do not create TTS audio, media files, a CapCut draft, a preview, a render, an upload package, or a publication claim.
- Do not bypass login, CAPTCHA, paywall, DRM, region controls, deleted content, or unavailable captions.
- Scores rank editorial suitability; they do not establish facts, rights, monetization, future views, or publication readiness.
