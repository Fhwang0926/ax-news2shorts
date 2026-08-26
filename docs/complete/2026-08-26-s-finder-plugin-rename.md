# s-finder 플러그인 이름 변경 완료

## 요청

- 기술 식별자: `s-finder`
- 사용자 표시명: `쇼츠 후보 찾기`

## 변경 내용

- 플러그인 폴더를 `plugins/shorts-scout`에서 `plugins/s-finder`로 변경했다.
- 플러그인 매니페스트 `name`을 `s-finder`로 변경했다.
- 매니페스트와 내부 Skill의 표시명을 `쇼츠 후보 찾기`로 변경했다.
- 내부 Skill 폴더와 Skill 식별자를 `s-finder`로 변경했다.
- CLI 파일명을 `shorts_scout.py`에서 `s_finder.py`로 변경하고 진단 출력 식별자를 `s-finder`로 변경했다.
- Skill 기본 호출 예시에 `$s-finder`를 반영했다.
- `news2shorts-local` 마켓플레이스 항목을 `s-finder`와 `./plugins/s-finder` 경로로 교체했다.
- `s-finder@news2shorts-local`을 설치하고 활성화했다.
- 기존 `shorts-scout@news2shorts-local` 설치와 캐시를 제거했다.

## 현재 주요 경로

- `plugins/s-finder/.codex-plugin/plugin.json`
- `plugins/s-finder/skills/s-finder/SKILL.md`
- `plugins/s-finder/skills/s-finder/agents/openai.yaml`
- `plugins/s-finder/scripts/s_finder.py`
- `.agents/plugins/marketplace.json`

## 확인 결과

- Skill 구조 검증 통과
- Plugin 구조 검증 통과
- 매니페스트와 마켓플레이스 JSON 구문 확인 통과
- 소스 CLI `--help`와 `doctor --json` 실행 확인
- 소스와 설치 캐시의 매니페스트, Skill, CLI SHA-256 일치
- `s-finder@news2shorts-local` 설치 및 활성화 상태 확인
- 기존 소스 폴더와 설치 캐시가 남지 않은 것을 확인
- 과거 완료 문서를 제외한 현재 실행 경로에 `shorts-scout`, `Shorts Scout`, `shorts_scout` 참조가 없는 것을 확인

AGENTS.md 지침에 따라 프론트 빌드와 프로젝트 테스트는 실행하지 않았다. 새 Skill을 적용하려면 새 Codex 작업에서 `쇼츠 후보 찾기` 또는 `$s-finder`로 호출한다.
