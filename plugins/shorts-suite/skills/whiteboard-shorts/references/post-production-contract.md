# Post-production contract

Use `post-production.json` to keep captions, music licence and attribution, and purposeful zooms explicit and reviewable.

```json
{
  "version": 1,
  "captions": {
    "enabled": true,
    "style": "viral-punch",
    "items": [
      {
        "scene_id": "scene-01",
        "text": "잠깐… 위에 뭐야?\n보더콜리 레이더 켜짐",
        "position": "top",
        "beat": "hook"
      }
    ]
  },
  "music": {
    "enabled": true,
    "mode": "licensed_catalog",
    "vocals": false,
    "volume": 0.85,
    "fade_in_seconds": 0.04,
    "fade_out_seconds": 0.3,
    "asset_path": "assets/audio/monkeys-spinning-monkeys.mp3",
    "track_id": "monkeys-spinning-monkeys",
    "title": "Monkeys Spinning Monkeys",
    "artist": "Kevin MacLeod",
    "bpm": 144,
    "start_seconds": 0.0,
    "loudness_target_lufs": -14.0,
    "true_peak_db": -1.5,
    "segments": [
      {"scene_id": "scene-01", "profile_id": "tension", "impact": false},
      {"scene_id": "scene-02", "profile_id": "playful", "impact": true}
    ],
    "license_name": "Creative Commons Attribution 4.0 International",
    "license_url": "https://creativecommons.org/licenses/by/4.0/",
    "source_page": "https://incompetech.com/music/royalty-free/?isrc=USUAN1400011",
    "attribution": "Monkeys Spinning Monkeys by Kevin MacLeod is licensed under CC BY 4.0. https://creativecommons.org/licenses/by/4.0/",
    "rights": {
      "permission_status": "licensed",
      "note": "제작자 공식 파일을 CC BY 4.0 조건과 필수 크레딧으로 사용합니다."
    }
  },
  "motion": {
    "enabled": true,
    "items": [
      {
        "scene_id": "scene-02",
        "type": "punch-in",
        "start_scale": 1.0,
        "end_scale": 1.12,
        "focus_x": 0.52,
        "focus_y": 0.24
      }
    ]
  }
}
```

## Caption rules

- Create exactly one item for every scene when captions are enabled.
- Use `top`, `middle`, or `bottom` after inspecting the image and avoiding the main subject.
- Use `viral-punch` for yellow-first-line, white-second-line, heavy-outline captions. Retain `comic-observation` only for quieter material.
- Keep each `viral-punch` caption at 36 Korean characters or fewer and visually to two lines.
- Assign `hook`, `setup`, `rehook`, `escalation`, or `payoff`; the first must be a hook, a middle scene must rehook, and the last must land the observed payoff.
- Follow [caption-writing.md](caption-writing.md). Prefer spoken Korean rhythm and short contrast words such as `근데` or `반전:`. Do not add facts, diagnoses, intentions, jobs, or feelings that are not visible.

## Music rules

- Create exactly one scene segment record when music is enabled; keep `gentle`, `tender`, `tension`, `relief`, or `playful` as the scene mood evidence.
- For comic, mistake, awkward-observation, or reveal clips, select a fitting entry from [shorts-music-catalog.json](shorts-music-catalog.json), copy its metadata exactly, and use `music-fetch` to obtain and hash-check the official recording.
- Use `synthetic_ambient` for tender or sensitive clips. `synthetic_public_domain_remix` remains a compatibility fallback, not the default for a user asking for an actually common Shorts track.
- Normalize to `-14 LUFS` with `-1.5 dB` true-peak protection; keep configured ranges within -18~-10 LUFS and -3~-0.5 dB.
- Keep `vocals: false`. Catalog audio must be `licensed` and `synthetic: false`; generated audio must be `owned` and `synthetic: true`.
- Preserve the exact attribution. The renderer writes `delivery-note.md`; it does not publish or insert credits automatically.
- Commercial platform songs must be added through the official Shorts music picker after upload, never embedded by this plugin.

## Motion rules

- Motion items are optional; do not add movement merely to fill the contract.
- Use `punch-in` for a visible reveal or payoff, `zoom-in` for attention guidance, and `zoom-out` only when revealing wider context.
- Keep `start_scale` and `end_scale` between `1` and `1.2`, and `focus_x`/`focus_y` between `0` and `1`.
- Focus on the inspected subject coordinates. Captions remain fixed while the drawing moves.
