# News2Shorts 결론·CTA 규칙 개선 및 길막 주차 재렌더

## 완료 내용

- 새 퀵리빌 결론 카드가 앞 장면의 완성된 자막·금액을 그대로 반복하면 draft 경고, final 오류가 되도록 검증 규칙을 추가했다.
- `오늘부터`, `다음 달부터`처럼 게시일에 따라 틀릴 수 있는 상대 시행 시점 문구를 검증 경고 대상으로 추가했다.
- 출처가 즉시 견인을 보장하지 않는데 `신고하면 바로 견인`, `즉시 견인`으로 축약하는 문구를 검증 경고 대상으로 추가했다.
- Typecast WAV의 시작·종료 외곽 무음만 정리하고 문장 내부 호흡은 유지하도록 렌더러를 개선했다.
- 새 프로젝트의 기본 CTA 테일을 2.7초로 줄이고, 실제 음성이 더 길면 기존처럼 필요한 길이까지 자동 확장하도록 유지했다.
- 길막 주차 프로젝트 후반을 `시행 중 → 관리자 알림 → 불응 시 지자체 견인 요청 → 의견 질문`으로 다시 구성했다.
- 시행 장면의 해외 견인차 반복 이미지를 별도의 라이선스 주차장 출입구 사진으로 교체했다.
- 공개 설명에서 정확한 시행일을 반복하지 않고 `개정 주차장법 시행`이라는 오래 사용할 수 있는 문구로 바꿨다. 정확한 날짜는 내부 출처·팩트 기록에 유지했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
  - 결론 자막 중복 검증
  - 상대 시행 시점·즉시 견인 문구 경고
  - Typecast 외곽 무음 정리
  - 기본 CTA 2.7초
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`
- `plugins/news2shorts/README.md`
- `projects/2026-08-28-parking-blocking-fine/project.json`
- `projects/2026-08-28-parking-blocking-fine/script.md`
- `projects/2026-08-28-parking-blocking-fine/storyboard.json`
- `projects/2026-08-28-parking-blocking-fine/rights-manifest.json`
- `projects/2026-08-28-parking-blocking-fine/publish.json`
- 프로젝트 렌더·썸네일·편집 패키지 결과물

## 설치 상태

- marketplace: `news2shorts-local`
- installed plugin: `news2shorts@news2shorts-local`
- version: `0.36.5+codex.20260828091859`
- source/cache `news2shorts.py` SHA-256 일치
- source/cache `SKILL.md` SHA-256 일치

## 검증 결과

- Skill quick validation: 통과
- Plugin validation: 통과
- 프로젝트 draft validation: 오류 0, 경고 0
- `git diff --check`: 통과
- 실제 검토 영상: 28.123초, 720x1280, 30fps, H.264/AAC, 영상·음성 스트림 확인
- Typecast 결론 장면: 5.876초
- 결론→CTA 경계 무음: 약 0.23초
- 최종 정지 여백: 약 0.40초
- Typecast 문장 내부 호흡 유지
- `preview.mp4` 및 `editable.mp4` 전체 디코딩 확인
- DB 작업 없음
- YouTube 업로드·게시 없음
- 프론트엔드 빌드 없음

## 결과물

- `projects/2026-08-28-parking-blocking-fine/preview.mp4`
- `projects/2026-08-28-parking-blocking-fine/thumbnail.jpg`
- `projects/2026-08-28-parking-blocking-fine/render-report.json`
- `projects/2026-08-28-parking-blocking-fine/edit-package/preview/editable.mp4`
- `projects/2026-08-28-parking-blocking-fine/edit-package/preview/captions.srt`
- `projects/2026-08-28-parking-blocking-fine/edit-package/preview/timeline.csv`

## 남은 승인 경계

- 프로젝트는 `rendered_draft` 상태다.
- `editorial_reviewed`, `rights_reviewed`, `synthetic_disclosure_reviewed`는 사용자 최종 확인 전까지 `false`로 유지한다.
- 최종 `short.mp4` 생성과 업로드는 수행하지 않았다.
