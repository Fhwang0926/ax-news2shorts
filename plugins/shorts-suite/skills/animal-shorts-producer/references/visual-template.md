# Visual templates

The output is 720x1280, 30fps, H.264 video and AAC stereo audio. `animal-viral-card-v1` is the fixed geometry and legacy visual preset. New projects default to `observation-contrast-v1`, which keeps the same safe regions and media treatment.

Fixed regions:

- y 0–56: top platform safety
- y 56–264: two-line headline
- y 264–1032: source video
- y 1032–1128: one role-styled scene message
- y 1128–1280: bottom platform safety
- rightmost 86 pixels: no critical text

The legacy card uses warm gray #F5F1EA, black #141414, and accent #C94F3D. Use no copied channel logo, paw motif, proprietary font, copied caption, or decorative AI-style icon.

Portrait media is focus-point cropped. Wide media is shown intact over a blurred background derived from the same frame. Creator and platform appear as small plain source attribution inside the video area.

Headline copy appears from time zero and stays within two lines. Scene messages use no more than two lines and one evidence-supported emphasis phrase. Keep critical lower text within 540 pixels so it does not enter the right-side UI area.

Use question styling for setup, a restrained progress line for build, a pale contrast card for turn, and an inverted dark card for payoff. Font size may rise from 42 to 52 pixels by narrative importance. Do not show literal setup/build/turn/payoff or 기승전결 labels. The renderer changes messages by scene, preserves source motion and source audio, and holds the last reviewed source frame for 0.5–1 second.

## observation-contrast-v1

Keep the fixed two-line headline visible from frame zero. Use the red headline accent and a small yellow contrast marker, then place one compact observation card in the lower safe region. The card contains a colored `subject_label` pill and a separate action caption; it is not a speech bubble. Use yellow accumulation for build, pale red contrast for turn, and a dark payoff card with yellow emphasis.

Every beat requires a 2–12 character `subject_label` that matches the reviewed `source-analysis.subjects` or a referenced observation's subject. Reject dialogue punctuation, exclamations, inferred emotions, intentions, and character roles that are not visually grounded. Keep ordinary scenes at three seconds or less and the final scene at four seconds or less including its 0.5–1 second source-frame hold.

This preset generalizes a fast observation-and-contrast hierarchy. Do not copy a reference channel's logo, font, wording, music, footage, or scene sequence. Existing projects without `visual_preset` fall back to `animal-viral-card-v1` so their prior render appearance does not change.

When reviewed English source captions need localization, use an opaque dark rounded card only for the caption's actual time window. Label literal wording `원문 번역` and playful Korean adaptation `원문 의역`. Keep it inside the source-video and right-side safety regions, and avoid creator attribution and reviewed faces as far as the source-caption placement allows. Draft status belongs in project metadata and reports, not as a visible corner badge.
