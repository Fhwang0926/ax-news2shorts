# news2shorts 결론 콜백 겹침 수정 완료

## 요청

- 팩트스택 결론 장면에서 `payoff_callback` 문구가 불투명 결론 카드 뒤로 가려지는 레이아웃 깨짐을 수정한다.
- 같은 제주 실종사건 검토 영상을 다시 렌더해 실제 프레임으로 확인한다.

## 원인

- 콜백 배경의 하단 좌표가 결론 카드 상단보다 14~28픽셀 아래에 있었다.
- 콜백을 먼저 그리고 불투명 카드를 나중에 그려 겹친 부분이 카드에 가려졌다.

## 반영 내용

- 결론 카드 위치를 먼저 계산한다.
- 콜백 높이와 안전 간격을 기준으로 콜백을 카드 위에 배치한다.
- `discussion_prompt`가 없는 결론은 20픽셀, 있는 결론은 24픽셀의 간격을 둔다.
- 콜백과 카드가 맞닿거나 겹치지 않아 레이어 순서와 관계없이 문구가 온전히 보인다.
- 제작 지침과 시각 스타일 문서에 콜백 안전 여백 규칙을 추가했다.
- 플러그인 버전을 `0.30.1+codex.20260824103655`로 올렸다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 콜백과 결론 카드 좌표 계산 수정.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 콜백 전체 노출 규칙 추가.
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`: 카드 위 안전 여백 규칙 추가.
- `plugins/news2shorts/README.md`: 결론 카드 안전 여백 기능 설명.
- `plugins/news2shorts/.codex-plugin/plugin.json`: 플러그인 버전 갱신.

## 검증

- Python 구문 검사, Skill 빠른 검증, JSON 파싱과 `git diff --check`를 통과했다.
- 설치 캐시와 소스의 스크립트·SKILL SHA-256이 일치한다.
- `news2shorts 0.30.1+codex.20260824103655` 설치와 활성화를 확인했다.
- Typecast `Seohyeon` 음성을 유지한 `preview-v3.mp4`를 재렌더했다.
- 영상은 H.264/AAC 720×1280, 35.462초다.
- 실제 결론 프레임에서 콜백 배경과 카드 사이의 여백, 문구 전체 노출, 제목·상세·질문 간 비겹침을 육안 확인했다.
- 홍석기 본부장 실사진 권리 장애, 모든 근거 장면이 정지 이미지라는 권고, 일반 장면 세 개의 4.5초 권장치 초과는 이번 레이아웃 수정 범위 밖의 기존 권고로 유지했다.
