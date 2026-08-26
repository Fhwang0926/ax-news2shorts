# news2shorts 태그 단독 실행 개선 완료

## 완료 내용

- 플러그인 버전을 `0.6.2+codex.20260816`으로 올리고 Codex 설치 캐시를 갱신했다.
- `@news2shorts` 태그만 입력된 경우 오늘의 뉴스 후보 수집과 교차검증을 즉시 시작하도록 기본 동작을 추가했다.
- 빈 호출에서 용도를 되묻지 않고 최대 3개 후보와 추천 1개를 제시한 뒤 사용자의 선택을 기다리도록 스킬 규칙을 명시했다.
- 스킬 선택 시 같은 동작을 전달하는 `agents/openai.yaml` 기본 프롬프트를 추가했다.
- URL, 주제 또는 제작 조건이 함께 입력된 경우에는 사용자의 명시 요청을 우선하도록 기존 흐름을 유지했다.

## 변경 파일

- `plugins/news2shorts/.codex-plugin/plugin.json`
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/agents/openai.yaml`
- `plugins/news2shorts/README.md`

## 확인 범위

- 플러그인 매니페스트와 스킬 메타데이터의 기본 호출 문구를 정적으로 확인했다.
- Codex 플러그인 목록에서 설치 버전 `0.6.2+codex.20260816`을 확인했다.
- 자동 테스트와 실제 새 대화 실행은 작업 지침에 따라 수행하지 않았다.
