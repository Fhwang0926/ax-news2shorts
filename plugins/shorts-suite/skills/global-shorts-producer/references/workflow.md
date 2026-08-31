# Workflow

## 1. Brainbulb candidate discovery

When no URL is supplied and the user asks to use the 뇌전구 channel, read only `https://www.youtube.com/channel/UCbr855WAFQvAX-An7IcHFXg/shorts`. Return up to three candidates in the channel Shorts-tab order, then stop for selection. Do not use the channel Videos tab, search by name, rank by views, auto-select, create projects, or schedule repeated checks.

## 2. Signal and ingest

Accept one public YouTube Shorts URL. The URL is a topic signal, not permission to reuse the creator's script or media. Initialize with the bundled CLI. Prefer manual Korean subtitles, then automatic Korean subtitles. Caption TLS verification uses the Python default CA or, when that file is unavailable, an already installed `certifi` CA bundle. Never disable certificate verification. If neither caption source is available, stop at `transcript_pending` unless the user provides an authorized transcript file.

The same `init` may resume an existing destination only when it is the exact same video and URL, remains `transcript_pending`, has an empty transcript, and has no research, script, or preview approval. A successful resume updates ingest metadata and transcript files in place. Every other existing destination remains protected from overwrite.

## 3. Research and verification

Summarize the source into these functional fields:

- beats: `hook`, `context`, `problem`, `twist`, `reaction`, `ending`
- event: `who`, `event`, `cause`, `result`, `controversy`

Research the underlying event independently. Give each source a stable `source_id` and each factual statement a stable `claim_id`. The signal Short cannot be listed as a fact source.

## 4. Origin and score

Choose one origin only:

- `KR_ORIGINAL`: independently evidenced Korean-origin event or format
- `GLOBAL_ORIGINAL`: independently evidenced non-Korean original
- `KPOP`: K-pop is the central subject
- `KOREAN_CULTURE`: Korean culture or social context is the central subject
- `GLOBAL_REPOST`: the signal primarily republishes an earlier foreign viral work
- `UNKNOWN`: available evidence does not establish origin

Complete the fixed score inputs. The CLI computes the score and applies origin overrides. Never manually change the computed total or decision.

## 5. Editorial gate

- `MAKE`: non-sensitive material may proceed to an English draft.
- `REVIEW`, `HOLD`, or any sensitive topic: stop until research approval is recorded.
- `SKIP`: do not draft or package.

Research approval confirms the evidence may be used to draft. It is not script, asset, render, upload, or publication approval.

## 6. English reframe

Draft three substantially different angles, five titles, and three hooks. Select one of each and record a plain-language reason. Then create:

- `en-US` narration of 80–120 words
- target duration of 30–40 seconds
- eight to ten scenes
- paragraph and scene `claim_ids`
- scene role, narration, normal caption, highlight caption, duration, asset type, search query, rights status

Do not translate line by line. Change the hook, payoff, explanation device, and information-reveal order when needed to create a genuinely new editorial work.

## 7. Asset plan

Every scene is a search plan only. Keep `asset_path` empty. Use one of the contract asset types and leave rights status as `planned` until a later, separately authorized workflow verifies an asset.

## 8. Originality and approvals

Record source and output claim/beat orders, run deterministic structure comparison, and complete the semantic review. If either review says rewrite, revise before asking for script approval. Package only after an explicit script approval.

Script approval allows creation of text and JSON handoff files only. The resulting package remains preview-unapproved and publication-blocked.
