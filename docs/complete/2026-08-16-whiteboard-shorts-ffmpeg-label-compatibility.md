# Whiteboard Shorts FFmpeg 권리 표시 호환성

## 완료 내용

- 시스템 FFmpeg에 `drawtext` 필터가 없어 로컬 검토 영상의 권리 경고 문구 단계가 실패하는 문제를 확인했다.
- 새 시스템 패키지를 요구하지 않고, 격리 렌더 환경의 Pillow로 반투명 경고 이미지를 만든 뒤 FFmpeg 기본 `overlay` 필터로 합성하도록 변경했다.
- 기존 `LOCAL REVIEW` 및 `LOCAL REVIEW - RIGHTS UNCONFIRMED` 문구와 상단 72픽셀 표시 규칙을 유지했다.
- 좁은 미리보기에서도 문구가 잘리지 않도록 사용 가능한 폭에 맞춰 글자 크기를 자동 조정한다.
- 플러그인 버전을 `0.2.1+codex.20260816`으로 올렸다.

## 변경 파일

- `plugins/whiteboard-shorts/scripts/whiteboard_shorts.py`
- `plugins/whiteboard-shorts/.codex-plugin/plugin.json`

## 검증 항목

- Python 구문 검사: 통과
- 플러그인 JSON 구조 검사: 통과
- 격리 렌더 환경에서 540x72 권리 표시 PNG 생성 및 육안 확인: 통과
- Whiteboard Shorts `0.2.1+codex.20260816` 설치 및 활성 상태 확인: 통과
- 실제 장면 검토 영상: 540x960, 15 FPS, H.264, 3초, 무음
- 실제 전체 초안: 1080x1920, 30 FPS, H.264, 15.5초, 무음
- 권리 미확인 표시와 시작·중간·완성 프레임 육안 확인: 통과
