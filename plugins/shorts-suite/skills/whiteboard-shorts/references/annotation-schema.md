# Annotation contract

Create one annotation beside each scene PNG:

```text
scenes/scene-01.png
scenes/scene-01.annotation.json
```

## Required shape

```json
{
  "sceneId": "scene-01",
  "canvas": {"width": 1080, "height": 1920},
  "storyBasis": "해당 장면의 사건 요약",
  "sceneDurationMs": 9000,
  "elements": [
    {
      "id": "setting",
      "label": "배경",
      "sequence": 1,
      "narrativeRole": "이야기의 공간을 먼저 제시",
      "subtitle": "해당 객체와 연결된 실제 SRT 문장",
      "type": "structure",
      "region": {"x": 40, "y": 120, "width": 1000, "height": 620},
      "reveal": {
        "direction": "top_to_bottom",
        "startMs": 200,
        "durationMs": 2400,
        "maskPaddingPx": 20,
        "protectedRegions": []
      },
      "handPath": {
        "start": [540, 140],
        "end": [540, 720],
        "easing": "easeInOut"
      }
    }
  ]
}
```

## Rules

- Inspect the actual PNG before assigning regions.
- Use original-image integer pixels. `canvas` must equal the PNG dimensions.
- Make `sequence` continuous from 1. Keep drawing intervals serial and non-overlapping.
- Leave at least 500 ms between the final element end and `sceneDurationMs`.
- Keep every region, protected region, and hand-path point inside the canvas.
- Use `protectedRegions` when an early region overlaps an object that must appear later.
- Use the SRT text connected to the visible object; do not invent dialogue or events.
- `direction` and `handPath` drive the rectangular preview. The final stream path is calculated by the renderer.
