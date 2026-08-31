---
name: romance-shorts-producer
description: Produce a Korean two-person romance-drama Short from an approved script, storyboard, and local or generated scene assets. Use for rendering and packaging, not trend research or YouTube upload.
---

# Shorts Romance Producer

승인된 2인극 대본·스토리보드·장면 자산을 Typecast 음성, 자막과 BGM으로 합성합니다.

## 필수 경계

- 국가별 후보 조사와 성장성 평가를 하지 않습니다.
- 검토되지 않은 립싱크를 만들거나 사용하지 않습니다.
- 합성 장면은 `synthetic: true`로 기록하고 content 승인 때 합성 표시 검토를 확인합니다.
- YouTube OAuth 연결과 직접 업로드를 하지 않습니다.

## 실행

`python3 <plugin-root>/scripts/romance.py romance ...`를 사용합니다. `init → assets 승인 → content 승인 → 검토 렌더 → publish 승인 → 최종 검증·렌더 → upload-package` 순서를 지킵니다.

최종본은 게시 가능한 권리와 `audio.provider: typecast`인 로컬 WAV가 모두 필요합니다.
