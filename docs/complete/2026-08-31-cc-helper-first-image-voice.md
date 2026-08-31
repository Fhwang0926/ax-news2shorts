# 임장비 cc-helper 첫 이미지·Typecast 음성 개선 완료

## 요청

- 깨져 보이는 첫 이미지 정리
- 음성이 없던 CapCut 초안에 Typecast TTS 추가

## 완료 내용

- 하단 설명 잘림을 제거하고 기사 제목·핵심 요약·부동산 사진만 정리한 `asset-ff462f44d52f`로 scene-01을 교체했다.
- 클리앙을 논란의 시작으로 표현하지 않도록 10개 비트 내레이션을 압축·교정했다.
- 사용자 승인 후 Typecast `Daeun`(`ssfm-v30`, tempo `1.10`)으로 음성을 생성했다.
- 문장별 파형 경계와 0.15초 간격을 사용해 15개 장면·자막을 30fps 기준으로 다시 맞춰다.
- 최종 WAV는 44.4886초, -16.03 LUFS, -4.47 dBTP다.
- 최종 CapCut 초안은 `cc-20260830-120742-real-estate-showing-fee-debate-v7`이며 음성 트랙은 0초부터 시작하고 전체 타임라인은 44.5초다.
- 10개 비트의 CapCut player 화면을 다시 확인했고 `validate --stage capcut` 결과는 `valid: true`다.
- 수정 전 v5와 중간 v6는 복구용으로 보존했다.

## 변경 파일

- `projects/cc-helper/2026-08-30/CCH-20260830-01-real-estate-showing-fee/storyboard.json`: scene-01 에셋, 압축 내레이션, 자막, 44.5초 타이밍
- `projects/cc-helper/2026-08-30/CCH-20260830-01-real-estate-showing-fee/project.json`: Typecast 제공자·음성·CapCut 트랙 ID와 v7 목적지
- `projects/cc-helper/2026-08-30/CCH-20260830-01-real-estate-showing-fee/handoff/narration-typecast.txt`: Typecast 전송 대본
- `projects/cc-helper/2026-08-30/CCH-20260830-01-real-estate-showing-fee/handoff/narration-timing.json`: 비트·장면 파형 타이밍
- `projects/cc-helper/2026-08-30/CCH-20260830-01-real-estate-showing-fee/handoff/narration-performance.json`: Typecast 메타데이터·음량·정지 구간 검증
- `projects/cc-helper/2026-08-30/CCH-20260830-01-real-estate-showing-fee/handoff/final-visual-qc.json`: v7 player 검수 해시
- `projects/cc-helper/2026-08-30/CCH-20260830-01-real-estate-showing-fee/handoff/player-qc-v7/`: 10개 최종 player 스크린샷
- `projects/cc-helper/2026-08-30/CCH-20260830-01-real-estate-showing-fee/assets/audio/`: Typecast 원본·문장별·마스터 WAV

## 남은 경계

- 내레이션은 자동 파형·음량 검수만 완료했다. 게시 전 사람 청취 승인이 필요하다.
- 외부 자료 권리는 `unreviewed`를 유지하며 프로젝트는 `local_review_only`, `publish_blocked: true`다.
- 일부 자막은 3.2초 권장을 넘지만 5.233초 이하로 음성 호흡과 함께 검수를 통과했다.
