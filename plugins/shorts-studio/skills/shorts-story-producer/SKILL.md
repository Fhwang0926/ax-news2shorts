---
name: shorts-story-producer
description: Produce a Korean character micro-story Short from a rights-approved local video and an already reviewed storyboard. Use for production and packaging, not public-source discovery or downloading.
---

# Shorts Story Producer

권리가 확인된 로컬 영상과 승인된 장면 계획으로 캐릭터형 쇼츠를 제작합니다.

## 필수 경계

- 공개 후보 조사, URL 취득, 기존 플러그인 프로젝트 가져오기를 하지 않습니다.
- 장면의 행동은 실제 원본에서 확인한 `observed_action`으로만 작성합니다.
- `unknown`·`review_required`는 로컬 검토본만, `not_permitted`는 전체 작업을 차단합니다.
- 후보나 스토리를 자동 선택하지 않습니다. 이 스킬은 승인된 입력의 제작만 담당합니다.

## 실행

`python3 <plugin-root>/scripts/shorts_studio.py story ...`를 사용합니다. `init → assets 승인 → content 승인 → 검토 렌더 → publish 승인 → 최종 검증·렌더 → upload-package` 순서를 지킵니다.

최종 음성은 `audio.provider: typecast`인 로컬 WAV가 필요합니다. 실제 업로드는 하지 않습니다.
