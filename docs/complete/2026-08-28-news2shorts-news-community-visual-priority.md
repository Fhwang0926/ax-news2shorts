# News2Shorts 뉴스·커뮤니티 시각자료 우선순위 적용

## 완료 내용

- 새 프로젝트가 일반 스톡이나 생성 이미지보다 현재 뉴스 기사와 로그인 없는 공개 커뮤니티의 직접 관련 이미지를 먼저 찾도록 시각자료 우선순위를 추가했다.
- 기본 우선순위는 `current-news-article → public-community-post → official-primary-media → licensed-media-library → generated-fallback`이다.
- 공개 커뮤니티 이미지는 댓글, 사용자명, 아바타, 프로필 이미지, 비공개 주소, 차량 번호판, 불필요한 인물이 포함되면 수집하지 않도록 규칙을 추가했다.
- 뉴스·커뮤니티 이미지의 권리가 확인되면 `licensed`, `official`, `owned`로 사용할 수 있고, 권리가 불명확하면 `unreviewed`, `approved: false`, `local_review_only: true`로 무배지 로컬 검토본까지만 허용한다.
- 뉴스·커뮤니티 우선순위가 프로젝트 설정에서 변경되거나 개인정보 검토 필드가 빠지면 검증기가 오류를 내도록 추가했다.
- 일반 스톡 라이브러리는 뉴스·커뮤니티·공식 자료 검색이 실패한 뒤에만 사용하고, 생성 이미지는 마지막 보완 수단으로 유지했다.

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
- version: `0.36.5+codex.20260828093835`
- source/cache script, skill, project template SHA-256 일치

## 검증 결과

- Skill quick validation: 통과
- Plugin validation: 통과
- Python syntax validation: 통과
- 프로젝트 템플릿 JSON validation: 통과
- 신규 프로젝트 초기화 점검에서 시각자료 우선순위 5단계와 개인정보 검토 필드 생성 확인
- 설치본 `doctor`에서 동일 우선순위 확인
- `git diff --check`: 통과
- DB 작업 없음
- 프론트엔드 빌드 없음
- 영상 재렌더·업로드 없음

## 적용 경계

- 이 설정은 새로 만드는 프로젝트의 기본값이다.
- 기존 프로젝트는 저장된 `visual_sourcing` 설정을 그대로 유지한다.
- 공개 뉴스·커뮤니티 이미지라는 이유만으로 게시 권한이 생기지 않는다.
- 권리 불명확 자산은 사용자 확인 또는 교체 전까지 최종 렌더에 사용할 수 없다.
