---
name: whiteboard-shorts
description: Select a proven-viral and whiteboard-fit TikTok animal source, then turn its downloaded and reviewed TikTok2Shorts project into a local whiteboard animation Short with five-beat Korean viral captions, verified licensed short-video music or safe generated no-vocal music, purposeful zooms, a final subscribe-like CTA, and YouTube upload information while preserving URL, creator, source-video hash, evidence, attribution, and rights state. Use for TikTok candidate selection, source-fit preflight, Korean scene import, 9:16 scene PNG preparation, annotation validation, caption, music and motion planning, music acquisition, region previews, local review rendering, or rights auditing. Local SRT input remains a compatibility path. Do not acquire TikTok directly, run ASR, upload, or decide publication rights.
---

# Whiteboard Shorts

Create a TikTok-grounded drawing animation. Use `$tiktok2shorts` first to qualify, compare, select, download, and inspect the public TikTok original. Treat the imported TikTok frames, source evidence, generated SRT, and inspected scene image as the basis for every drawing decision. Keep the workflow local and interactive by default.

## Locate the tool

Resolve the plugin root as the directory two levels above this skill directory. Run:

```text
python3 <plugin-root>/scripts/whiteboard_shorts.py doctor --json
```

`doctor` is read-only. Run `setup` only when the user explicitly asks to install the isolated renderer dependencies.

## Workflow

1. Read [rights-policy.md](references/rights-policy.md) before copying, generating, previewing, or rendering source or scene images.
2. If no selected TikTok2Shorts project is supplied, invoke `$tiktok2shorts`: research candidates with `score --target-format whiteboard`, show no more than three that pass the 70-point score and every component floor, include the fit evidence and rights state, and wait for the user to choose. Do not rank by original reach alone or silently select a candidate.
3. Use `$tiktok2shorts` to initialize, download, preview, and inspect the selected original. Fill the reviewed analysis and source-grounded storyboard. Do not bypass login, cookies, CAPTCHA, DRM, or access controls.
4. Run the low-cost source preflight before creating a whiteboard project:

   ```text
   python3 <plugin-root>/scripts/whiteboard_shorts.py preflight \
     --source-project <tiktok2shorts-project>
   ```

   Stop if the scored candidate proof is missing, the score is below 70, the downloaded preview has fewer than six frames, review is incomplete, or the storyboard lacks three distinct actions plus hook, change/payoff, and conclusion roles.
5. Import the reviewed project:

   ```text
   python3 <plugin-root>/scripts/whiteboard_shorts.py init \
     --project-dir <project> --source-project <tiktok2shorts-project>
   ```

   This copies the downloaded TikTok source and source/storyboard snapshots, generates `input/story.srt` from reviewed Korean scene narration, and links every whiteboard scene to its TikTok `source_evidence`. It inherits the original rights state without accepting a manual upgrade.
6. Read `scene-plan.json` and the generated `scenes/scene-XX.json` files. Inspect the imported source media or preview frames, present the TikTok-grounded drawing strategy, and stop for user confirmation before creating images.
7. Read [visual-style.md](references/visual-style.md). Prepare one `1080x1920` PNG per scene at the exact project-relative path in its scene JSON. Base it only on the linked observed action. Do not place text in a source image.
8. Inspect each actual scene image. Do not create annotation from narration alone. Read [annotation-schema.md](references/annotation-schema.md) and write the matching `scene-XX.annotation.json` with integer source-image coordinates.
9. Update `rights-manifest.json` for every scene image. Preserve `unknown` or `review_required`; never infer permission from a local file, public URL, credit, or transformation.
10. Read [caption-writing.md](references/caption-writing.md), [shorts-music-catalog.json](references/shorts-music-catalog.json), and [post-production-contract.md](references/post-production-contract.md). For TikTok imports, refine the generated `post-production.json`: shape the scene captions as hook, setup, rehook, escalation, and payoff; keep every claim grounded in the visible action; and focus each zoom on the observed subject. For comic, mistake, awkward-observation, or reveal-heavy clips, use the matching verified licensed catalog track. Use `synthetic_ambient` for tender, sensitive, or low-energy behavior.
11. Fetch the selected catalog track from its official source. This verifies the downloaded file hash and updates the rights manifest:

   ```text
   python3 <plugin-root>/scripts/whiteboard_shorts.py music-fetch \
     --project-dir <project>
   ```

   Skip this command for generated music. Never substitute a same-title file from a streaming or repost site.
12. Run static validation. Use `--render-ready` only after every image and annotation exists:

   ```text
   python3 <plugin-root>/scripts/whiteboard_shorts.py validate --project-dir <project>
   python3 <plugin-root>/scripts/whiteboard_shorts.py validate --project-dir <project> --render-ready
   ```

13. Create the numbered region image first. This does not render video:

   ```text
   python3 <plugin-root>/scripts/whiteboard_shorts.py preview \
     --project-dir <project> --scene scene-01 --regions-only
   ```

14. Show the region image and stop for user confirmation. Revise only the rejected scene.
15. After approval, create a `540x960`, 15 FPS local review clip by omitting `--regions-only`. A review clip is not publication evidence.
16. Read [output-contract.md](references/output-contract.md). Render `--draft` before any clean final. Unknown or review-required TikTok rights are allowed only for a labelled local draft. `render --all` burns the planned captions, applies purposeful scene zooms, mixes the verified or generated AAC background music, and writes a required-credit delivery note for catalog music.
17. Render a clean `1080x1920`, 30 FPS H.264 result only after the TikTok source and every scene image use `owned`, `licensed`, or `permission_confirmed`, all final approvals are true, and a draft was reviewed. A full `--all` render appends one separate `다음 반전도 계속 / 구독 · 좋아요` shot after the payoff.
18. Run `upload-package --project-dir <project>` and include the complete YouTube upload information after every full draft or final render.

## Commands

```text
python3 <plugin-root>/scripts/whiteboard_shorts.py doctor [--json]
python3 <plugin-root>/scripts/whiteboard_shorts.py setup [--check]
python3 <plugin-root>/scripts/whiteboard_shorts.py preflight --source-project <tiktok2shorts-project>
python3 <plugin-root>/scripts/whiteboard_shorts.py init --project-dir <project> --source-project <tiktok2shorts-project>
python3 <plugin-root>/scripts/whiteboard_shorts.py init --project-dir <project> --srt <file> --rights-status <status>
python3 <plugin-root>/scripts/whiteboard_shorts.py validate --project-dir <project> [--render-ready] [--final]
python3 <plugin-root>/scripts/whiteboard_shorts.py music-fetch --project-dir <project> [--track <id>]
python3 <plugin-root>/scripts/whiteboard_shorts.py preview --project-dir <project> --scene <id> [--regions-only]
python3 <plugin-root>/scripts/whiteboard_shorts.py render --project-dir <project> (--scene <id> | --all) [--draft]
python3 <plugin-root>/scripts/whiteboard_shorts.py upload-package --project-dir <project>
```

Use `--overwrite` only when the user explicitly asks to replace an existing generated output. Use `--ink-path skeleton` only for clean line art; otherwise retain the stable `grid` default.

## Boundaries

- Do not fetch a TikTok video or reuse browser credentials in this plugin. Use `$tiktok2shorts`, require user selection, and import only its downloaded and reviewed project.
- Do not import a candidate that lacks a passing `whiteboard_fit_assessment`; verified original reach is necessary but not sufficient.
- Do not run ASR, synthesize narration, add vocals, copy audio from TikTok or streaming services, use an unverified external track, embed a commercial platform-library song, or upload an output. Add a commercial song only through the platform's official Shorts music picker after upload.
- Use `viral-punch` captions with one beat, at most 36 Korean characters, and at most two lines per scene. Open with a concrete hook, place a rehook before the reveal, and land the final observed payoff. Do not present an inferred job, intention, diagnosis, or emotion as fact.
- Use `punch-in` on a reveal or payoff, and restrained `zoom-in` elsewhere only when it clarifies the observed subject. Keep scale at or below 1.2 and never move the caption with the image.
- Do not infer drawing content from captions alone. Preserve and use each imported TikTok scene's observed-action evidence.
- Do not create an annotation without both the corresponding subtitle text and an inspected image.
- Do not mark a clean final eligible because rendering succeeded.
- Treat `youtube-upload.json` and `youtube-upload.md` as preparation only; surface every unresolved upload setting and do not upload or schedule the video.
- Report project validation, rendered-file properties, rights review, publication permission, and platform acceptance as separate proof levels.
