# news2shorts 불투명 단일 결론 카드 개선 완료

## 요청

- 결론 카드 아래 원본 일러스트의 네모 패널 두 개가 비쳐 여러 카드처럼 보이는 문제를 제거한다.

## 완료 내용

- 편집형 결론 카드의 배경 알파를 `226`에서 `255`로 바꿔 카드 내부를 완전 불투명하게 처리했다.
- 바깥 결론 카드 한 개의 둥근 테두리와 내부 정보 위계는 유지했다.
- 플러그인 Skill과 시각 스타일 규칙에 배경 패널·프레임·선이 카드 안에 비치지 않아야 한다는 기준을 추가했다.
- 플러그인 버전을 `0.11.1+codex.20260817`로 올리고 로컬 Codex 캐시에 설치·활성화했다.
- 현재 황희 버스하우스 프로젝트를 `preview-v5.mp4`로 다시 렌더했다.

## 검증

- 단일 payoff PNG를 육안 확인해 카드 내부의 두 패널이 완전히 가려진 것을 확인했다.
- 전체 영상의 21초 프레임을 다시 추출해 같은 결과를 확인했다.
- `preview-v5.mp4`: 720x1280, H.264/AAC, 25.214초, Typecast 서현, 경고 0건.
- 프로젝트 초안 검증: 오류 0건, 경고 0건.
- 원본·설치본 렌더러 SHA-256 일치.
- 설치된 Skill 빠른 검증 통과, `doctor` 정상, 플러그인 설치·활성화 확인.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 결론 카드 배경 완전 불투명화
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 단일 불투명 카드 규칙 추가
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`: 배경 패널 비침 금지 기준 추가
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전과 설명 갱신
- `plugins/news2shorts/README.md`: 사용자 기능 설명 갱신
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/preview-v5.mp4`: 새 편집 검토본
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/render-report.json`: 새 렌더 보고서
- `docs/todo/2026-08-17-hwang-hee-bus-house-final-review.md`: 최신 검토본 상태 갱신

## 미실행 범위

- 정치 소재 사용자 편집 승인 전이므로 최종 `short.mp4`는 만들지 않았다.
- 업로드·게시, 프론트엔드 빌드, DB 작업은 수행하지 않았다.
