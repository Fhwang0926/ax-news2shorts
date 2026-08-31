---
name: guided-shorts-producer
description: "Run every new Shorts Suite production through five explicit user gates: source, script, image, voice, and render. At each stage list every currently selectable compatible option with explanations, record the user's option IDs, produce only the selected result, show it, and require result approval before advancing. Use for new guided Shorts creation across Whiteboard, Senior, Animal, Healing, Romance, and Global Reframe modes. Do not auto-select, skip a stage, treat approval as rights clearance, upload, or use this flow to rewrite legacy projects."
---

# Guided Shorts Producer

Use this as the default workflow for every new Shorts Suite project. Direct role skills remain available only for existing projects and advanced compatibility work.

## Non-negotiable sequence

Follow this order exactly:

```text
source → script → image → voice → render → local final
```

At every stage:

1. Generate the current option registry with `guided options`.
2. Show every selectable option and its description, best use, tradeoffs, inputs, time/cost, rights impact, and recommendation flag. Show unavailable options separately with reasons.
3. Wait for the user to choose all required `group=id` values. Never convert a recommendation or score into a selection.
4. Record the choice with `guided select`.
5. Use the selected role skill or renderer to create only the selected result. Do not create samples for unselected options.
6. Register all result files with `guided produce`, then show the result and its digest.
7. Wait for the user's `approve` or `revise` decision. Pass the current result digest to `guided approve`.
8. Advance only after `approve`. A revision or upstream change keeps or returns the workflow to that stage and invalidates downstream approvals.

Read [workflow-contract.md](references/workflow-contract.md) before starting or resuming a guided project.

## Commands

Initialize a new project:

```text
python3 -B <plugin-root>/scripts/shorts_suite.py guided init \
  --project-dir <new-empty-project-dir> \
  --mode auto \
  --title "<working-title>"
```

For each stage:

```text
python3 -B <plugin-root>/scripts/shorts_suite.py guided options \
  --project-dir <project-dir> --stage <stage> [--input <options-json>]

python3 -B <plugin-root>/scripts/shorts_suite.py guided select \
  --project-dir <project-dir> --stage <stage> \
  --option <group=id> [--option <group=id> ...]

python3 -B <plugin-root>/scripts/shorts_suite.py guided produce \
  --project-dir <project-dir> --stage <stage> \
  --producer-role <role> --artifact <project-relative-file> [...] \
  --rights-status <status> [--synthetic] [--note "<summary>"]

python3 -B <plugin-root>/scripts/shorts_suite.py guided approve \
  --project-dir <project-dir> --stage <stage> \
  --decision approve|revise --result-sha256 <current-digest> \
  [--confirm-synthetic-disclosure] [--note "<user decision>"]
```

`produce` registers and hashes role-native artifacts; it does not replace the existing role renderer. Create source evidence, scripts, images, audio, and review MP4 with the matching role skill before registering them.

## Stage requirements

- **Source:** display every eligible candidate from the current discovery batch, capped only by the existing discovery limit of ten. Include source trace, visible-content status, Korean Gap, rights and compatible modes. A selected source with unknown rights can continue to local review but cannot become a clean final.
- **Script:** display every valid role-native story or script option. Produce the full script, storyboard and subtitle draft for only the selected direction.
- **Image:** display every compatible provider, style and renderer input option. Produce the complete scene set and contact sheet for only the selected combination. Synthetic image approval must include synthetic disclosure confirmation.
- **Voice:** display all currently available Typecast, installed Korean macOS, user-file, rights-approved source-audio and supported no-voice options. Never fall back to another provider after failure.
- **Render:** display every compatible renderer, pacing, caption, music and review-size option. Produce a marked review MP4 and QA evidence. After user approval, use the role renderer to create a clean MP4 and pass it to `guided finalize`.

## Final boundary

`guided finalize` requires render approval, a project-local clean MP4, `--confirm-clean-render`, publishable source rights, and reviewed synthetic disclosure when synthetic assets exist. It validates and records the local final but never uploads it. If any requirement is missing, keep the review result and explain the exact blocker.

Never modify or delete a legacy project to adopt this workflow. Use the `whiteboard`, `senior`, `animal`, `healing`, `romance`, or `globalize` compatibility role directly for existing projects.
