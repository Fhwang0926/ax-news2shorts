# 임장비 cc-helper 첫 이미지·음성 개선 완료

> 2026-08-31 완료. 상세 기록은 `docs/complete/2026-08-31-cc-helper-first-image-voice.md`에 정리했다.

## 요청

- 기존 CapCut 복사본의 첫 이미지 깨짐 개선
- 내레이션 음성 추가

## 확인 결과

- 최신 대상은 `cc-20260830-120742-real-estate-showing-fee-debate-v5`다.
- 첫 이미지 원본·복사본 SHA-256은 동일해 파일 손상은 아니었다.
- 기사 카드 하단 설명이 잘린 상태로 크게 확대된 화면 구성이 깨져 보이는 원인이었다.
- 프로젝트와 CapCut 초안에는 내레이션 WAV와 오디오 트랙이 모두 없다.
- Typecast API 키는 macOS 키체인에서 사용 가능하다.

## 반영 완료

- 하단 설명 잘림을 제거하고 제목·핵심 요약·부동산 사진만 정돈한 `asset-ff462f44d52f`를 만들었다.
- `storyboard.json`의 scene-01을 새 에셋으로 교체했다.
- 다음 최종 복사본 목적지를 `cc-20260830-120742-real-estate-showing-fee-debate-v6`로 준비했다.
- `handoff/narration-typecast.txt`에 현재 10비트 내레이션을 기록했다.
- `validate --stage assets`를 통과했다.

## 대기 항목

- Typecast 생성은 내레이션 전문을 외부 Typecast API에 전송하는 작업이라 사용자 명시 승인이 필요하다.
- 승인 후 Daeun 음성, tempo 1.10으로 WAV를 생성하고 실제 길이·LUFS·피크·타이밍을 검수한다.
- 음성과 수정 이미지를 함께 반영한 v6 CapCut 복사본을 만들고 player-check 및 `validate --stage capcut`을 수행한다.

## 경계

- 승인 전 Typecast 요청을 재시도하지 않는다.
- macOS `say` 등 임의 로컬 TTS로 대체하지 않는다.
- 기존 v5 초안은 변경하지 않고 보존한다.
- 외부 자료 권리는 계속 `unreviewed`, 프로젝트는 `local_review_only`, `publish_blocked: true`다.
