# news2shorts cc-helper 대화형 말투 옵션 추가 완료

## 요청

- `news2shorts`에서 `cc-helper`처럼 친구에게 설명하는 말투를 선택할 수 있게 개선
- 뉴스 출처·truth guard·민감 주제·payoff 검증은 유지

## 반영 내용

- `project.json.narration_style`에 `standard | cc-helper-conversational`을 추가했다.
- 신규 프로젝트 기본값은 호환성을 위해 `standard`로 유지했다.
- `init --narration-style cc-helper-conversational`로 선택할 수 있다.
- `cc_helper 말투`, `cc-helper 말투`, `친구 설명형` 요청을 이 필드로 매핑하도록 스킬 계약을 추가했다.
- 비원본 내레이션에서 `합니다`, `했습니다`, `입니다` 종결을 거부한다.
- 인접한 장면의 `~데/~는데` 반복과 마지막 두 장면의 `~함 → ~함` 반복을 거부한다.
- `audio_mode: source-video` 장면은 실제 대사를 보존해야 하므로 말투 검증에서 제외한다.
- `visual-first`는 내레이션이 없어 `cc-helper-conversational`을 거부한다.
- 출처에 없는 의도·과장·속어·비난·여론 추정은 계속 금지한다.
- `render-report.json`에 실제 사용한 `narration_style`을 기록한다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
- `plugins/news2shorts/README.md`
- `plugins/news2shorts/.codex-plugin/plugin.json`

## 검증·설치

- Python 문법 검사 통과
- 프로젝트 템플릿 JSON 구문 검사 통과
- news2shorts 스킬 정적 검증 통과
- 플러그인 매니페스트 검증 통과
- 사용자 지침에 따라 테스트·빌드는 실행하지 않음
- 설치 버전: `0.36.5+codex.20260831062430`
- 설치 경로: `/Users/hdh/.codex/plugins/cache/news2shorts-local/news2shorts/0.36.5+codex.20260831062430`
- 소스·설치본 `news2shorts.py` SHA-256 일치: `6148bb121e2fa9ac262791c4c56af13415dfe41dd3601564e6c3b2d5f0a223e7`
