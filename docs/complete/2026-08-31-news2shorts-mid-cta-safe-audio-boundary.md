# 2026-08-31 news2shorts 중간 CTA 음성 안전 경계 개선

## 문제

- 기존 continuous-flow 렌더러는 본문 전체 Typecast 음성을 한 번 생성한 뒤 글자 수 비례 시간으로 장면 WAV를 나눴다.
- 중간 CTA 선택이 장면 분할 뒤에 이뤄져 활성 음성 조각 사이에 CTA가 삽입될 수 있었다.
- 기존 네팔 터널 검토본에서는 CTA 직전 0.2초가 평균 -16.3dB로 측정돼 음성이 끝나기 전에 CTA가 시작된 상태였다.

## 변경

- `plugins/news2shorts/scripts/news2shorts.py`
  - 중간 CTA 장면 경계를 Typecast 생성 전에 선택한다.
  - CTA가 없으면 기존처럼 본문 TTS 한 요청을 사용한다.
  - CTA가 있으면 앞 본문과 뒤 본문을 각각 완전한 Typecast 요청으로 생성한다.
  - 앞 본문 WAV, CTA WAV, 뒤 본문 WAV를 연결한 뒤 영상에 다시 입혀 음성 중간 절단과 CTA 길이 누락을 막는다.
  - 렌더 보고서에 `body_tts_requests: 2`, `mid_cta_two_part: true`, `boundary_preserves_complete_utterances: true`를 기록한다.
  - 검증기가 위 기록이 없는 중간 CTA 렌더를 오류로 차단한다.
  - `thumbnail_status: blocked_rights`인 로컬 초안은 썸네일 권리 차단 상태를 유지하면서 렌더 보고서를 완성한다.
- `plugins/news2shorts/tests/test_retention_v16.py`
  - 중간 CTA가 scene 경계에서 앞뒤 두 TTS 그룹으로 나뉘는지 확인한다.
  - 두 요청의 오디오 경로가 서로 달라 덮어쓰지 않는지 확인한다.
  - 본문 TTS 한 요청 또는 안전 경계 기록 누락을 검증기가 거부하는지 확인한다.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`, `plugins/news2shorts/README.md`
  - 중간 CTA의 두 요청 생성 규칙과 안전 경계 검증 계약을 문서화했다.

## 검증

- Python 구문 검사 통과.
- 중간 CTA 안전 경계 회귀 검사 통과.
- 네팔 터널 프로젝트를 Typecast `Seohyeon`으로 다시 렌더했다.
- 새 검토본은 25.239초이며 `preview.mp4`와 편집 패키지 `reference.mp4`의 SHA-256이 일치한다.
- CTA 앞뒤 결합 무음은 각각 0.128초와 0.263초이며 활성 음성 절단은 확인되지 않았다.
- 검은 화면과 0.5초 이상 내부 무음은 없고, 통합 음량은 -13.9 LUFS, true peak는 -2.5dBFS다.
- 플러그인·스킬 검증과 전체 `RetentionV16Tests` 19건이 통과했다.
- 캐시버스터를 `0.36.5+codex.20260831064428`로 갱신하고 `news2shorts@news2shorts-local`을 재설치했다.
- 설치 캐시의 렌더러, `SKILL.md`, 플러그인 manifest SHA-256이 소스와 일치한다.
- 프론트엔드 빌드는 수행하지 않았다.
