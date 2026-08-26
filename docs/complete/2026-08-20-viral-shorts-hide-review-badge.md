# 2026-08-20 Viral Shorts 검토용 배지 숨김

## 작업 범위

- 사용자의 명시적 요청에 따라 아이브 쇼츠의 `로컬 검토용` 화면 배지를 숨길 수 있도록 했다.
- 기존 배지 버전은 보존하고 `outputs/review-no-badge.mp4`로 별도 렌더한다.
- `--hide-review-badge`는 비어 있지 않은 `--approval-note`를 필수로 요구한다.
- 화면 배지를 숨겨도 `local_review_only: true`, `publication_ready: false`, 권리 `unknown`을 유지한다.

## 검증 결과

- Python AST, Plugin validator, Skill validator가 통과했다.
- `review-no-badge.mp4`가 39.28초, 720x1280, H.264, AAC, 30fps임을 확인했다.
- 최종 SHA-256은 `b689fc489a3fb614647d320c9620153225a943d99b72141c8b883688c72d38a0`이다.
- 대표 4개 프레임 접촉 이미지에서 검토용 배지가 없고 후킹·자막이 유지되는 것을 시각 확인했다.
- `render-report.json`에 `visible_review_badge: false`, 사용자 요청 메모, `local_review_only: true`, `publication_ready: false`가 기록됐다.
- 프론트엔드 빌드·테스트와 DB 작업은 수행하지 않았다.

## 변경 파일

- `plugins/viral-shorts/scripts/viral_shorts.py`
- `plugins/viral-shorts/skills/viral-shorts/SKILL.md`
- `plugins/viral-shorts/skills/viral-shorts/references/rights-policy.md`
- `plugins/viral-shorts/skills/viral-shorts/references/workflow.md`
- `plugins/viral-shorts/skills/viral-shorts/references/output-contract.md`
- `docs/complete/2026-08-20-viral-shorts-hide-review-badge.md`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/project.json`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/render-report.json`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/outputs/review-no-badge.mp4`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/outputs/review-no-badge-contact-sheet.png`
