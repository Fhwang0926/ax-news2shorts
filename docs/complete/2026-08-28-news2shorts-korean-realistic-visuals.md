# News2Shorts 한국 이미지 전용·사실적 시각 규칙

## 완료 내용

- 새 news2shorts 프로젝트의 모든 장면을 `ko-KR` 한국 이미지 전용으로 설정했다.
- 해외 표지판, 경찰·응급복, 차량 번호판, 도로 표시, 건축, 상점 언어, 통화, 차량 환경이 보이는 자산은 차단한다.
- 한국 언론사·커뮤니티에서 가져온 이미지라도 실제 픽셀에 해외 배경이 보이면 사용할 수 없도록 했다.
- 각 자산은 `visual_locale: "ko-KR"`, `korean_context_reviewed: true`, `korean_context_note`를 기록해야 한다.
- 이미지 수집 명령에 `--visual-locale ko-KR`, `--confirm-korean-context`, `--korean-context-note`를 추가했다.
- 새 프로젝트의 생성 보완 기본 스타일을 `korean-editorial-realism`으로 변경했다.
- 생성 보완은 현재 한국 아파트·도로·사무실·상가·공공시설과 자연광·현실 재질을 사용하도록 규칙화했다.
- 생성 이미지가 읽을 수 있는 가짜 표지판·로고·번호판·정부 표식·제복을 만들거나 실제 사건 사진처럼 보이게 하는 것은 금지했다.
- 현실적 표현이 실제 사건으로 오인될 때는 한국 맥락의 설명용 문서·도표를 사용하도록 했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/references/rights-policy.md`
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`
- `plugins/news2shorts/README.md`
- `plugins/news2shorts/.codex-plugin/plugin.json`

## 설치 상태

- marketplace: `news2shorts-local`
- installed plugin: `news2shorts@news2shorts-local`
- version: `0.36.5+codex.20260828124534`
- source/cache script, skill, project template SHA-256 일치

## 검증 결과

- Skill quick validation: 통과
- Plugin validation: 통과
- Python syntax validation: 통과
- 프로젝트 템플릿 JSON validation: 통과
- 신규 프로젝트 초기화에서 `ko-KR`, `blocked`, `korean-editorial-realism` 생성 확인
- 이미지 수집 CLI의 한국 배경 확인 옵션 노출 확인
- 설치본 `doctor`에서 한국 이미지 기본값과 뉴스·커뮤니티 우선순위 확인
- `git diff --check`: 통과
- DB 작업 없음
- 프론트엔드 빌드 없음
- 기존 프로젝트 영상 재렌더 없음

## 적용 경계

- 한국 이미지 전용 규칙은 새 프로젝트의 기본값이다.
- 기존 프로젝트는 저장된 설정을 유지하며 자동으로 해외 자산을 교체하지 않는다.
- 공개된 한국 이미지도 게시 권리를 자동으로 획득하지 않는다.
- 권리 불명확 자산은 무배지 로컬 검토본에서만 사용할 수 있고 게시 전 확인 또는 교체가 필요하다.
