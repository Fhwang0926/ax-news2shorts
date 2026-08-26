# news2shorts 시민 질문형 전개 및 별도 썸네일 개선 완료

## 요청 사항

- 뉴스 요약문처럼 전개하지 않고 시민·소비자의 관점에서 `이게 맞는가?`를 묻는다.
- 첫 화면과 첫 내레이션을 반드시 훅 질문으로 시작한다.
- 최종 영상 제작 시 영상과 별도의 호기심 유도 썸네일 이미지를 생성한다. 저해상도와 자극적인 표현은 허용한다.

## 반영 내용

- 신규 프로젝트 계약을 v9로 올리고 시민의 비용·안전·생활·권리 중 구체적인 이해관계를 필수로 만들었다.
- 선택 훅, 첫 화면 문구, 첫 내레이션을 질문형으로 검증하며 뉴스 요약형 도입은 차단한다.
- 질문에서 제기한 문제를 근거와 반전을 거쳐 답하도록 이슈 질문과 훅의 연결을 검증한다.
- 최종 영상용 썸네일은 영상 프레임과 별도의 파일 업로드 이미지로 만들고 질문형 문구를 필수로 한다.
- 썸네일 결과와 렌더 리포트에 `dedicated-curiosity-thumbnail`, `separate_asset`, `question_led` 정보를 기록한다.
- 썸네일은 낮은 해상도와 자극적인 표현을 허용하되 확인되지 않은 사실·비난·공포를 새로 만들지는 않도록 기존 사실 검증 경계를 유지했다.
- 플러그인 버전 `0.29.0+codex.20260824090820`을 로컬 마켓플레이스 설치본에 반영했다.

## 변경 파일

- `plugins/news2shorts/.codex-plugin/plugin.json`
- `plugins/news2shorts/README.md`
- `plugins/news2shorts/scripts/news2shorts.py`
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/agents/openai.yaml`
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`
- `plugins/news2shorts/skills/news2shorts/references/upload-package.md`
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`
- `plugins/news2shorts/skills/news2shorts/templates/storyboard.template.json`

## 검증

- Python 구문 검사 및 CLI 도움말 확인 완료
- Skill 구조 검증 완료
- 플러그인 매니페스트와 프로젝트·스토리보드 템플릿 JSON 파싱 완료
- 신규 v9 정상 질문형 프로젝트 검증 통과
- 뉴스 요약 도입, 평서문 첫 내레이션, 평서문 썸네일의 차단 확인
- 별도 썸네일 이미지 생성 및 화면 확인 완료
- 기존 v8 프로젝트 검증 통과로 하위 호환성 확인
- 소스와 설치 캐시의 핵심 파일 SHA-256 일치 확인
- `git diff --check` 통과

## 작업 범위

- 기존 제작 프로젝트와 완성 MP4는 다시 렌더하지 않았다.
- Typecast 호출과 YouTube 업로드는 수행하지 않았다.
- 프론트엔드 빌드 대상 작업은 없다.
