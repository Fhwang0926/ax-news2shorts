# healing2shorts 대화형 힐링 썰 v3 개선 완료

## 개선 배경

- 기존 `story-01`은 한 사건을 설명하는 기사형 미담이어서 두 인물의 대화와 감정 누적이 부족했다.
- 힐링쇼츠의 신규 기본값을 기사 요약이 아닌 `대사가 오가는 약간 긴 익명 썰`로 수정했다.
- 기존 v1·v2 프로젝트는 다시 열 수 있게 유지하고 신규 후보만 v3 계약을 사용한다.

## 신규 스토리 계약 v3

- `mode=anecdote`만 신규 힐링 후보로 허용한다.
- 2~3명의 화자가 10~14개 대사를 주고받아야 한다.
- 연속 대사 사이 화자 교대가 7회 이상이어야 한다.
- 대화문이 전체 내레이션 글자의 60% 이상이어야 한다.
- 7개 비트마다 실제 대사를 하나 이상 연결하고 전체 대사를 원래 순서대로 한 번씩 사용한다.
- 첫 장면은 내레이터의 기사형 질문 대신 인물의 말로 시작한다.
- 기본 길이는 42초이며 v3 프로젝트는 40~45초만 허용한다.
- 자료에 없는 대사를 사실처럼 만들지 않는다. 창작 대사는 `fictionalized`와 `창작·재구성한 익명 사연` 표시가 필요하다.
- 기존 기사형 v2와 기존 6비트 v1은 호환 입력으로만 유지한다.

## 변경 파일

- `plugins/healing2shorts/scripts/healing2shorts.py`: v3 후보·대사 수·화자 수·교대 횟수·대화 비중·대사 순서·40초 최소 길이 검증과 v1/v2 호환을 추가했다.
- `plugins/healing2shorts/tests/test_healing2shorts.py`: 대화형 후보 성공, 기사 요약 모드 차단, 대사 부족 차단, 짧은 길이 차단과 전체 스토리보드 검증을 추가했다.
- `plugins/healing2shorts/skills/healing2shorts/SKILL.md`: 신규 기본 후보와 제작 흐름을 대화형 익명 썰 중심으로 변경했다.
- `plugins/healing2shorts/skills/healing2shorts/references/story-patterns.md`: 대화형 최소 조건과 7비트 대화 흐름을 기록했다.
- `plugins/healing2shorts/skills/healing2shorts/references/candidate-contract.md`: story candidates v3와 `dialogue_turns`, `dialogue_turn_ids` 계약을 기록했다.
- `plugins/healing2shorts/skills/healing2shorts/references/output-contract.md`: v3 40~45초 타임라인과 기존 계약 호환 범위를 기록했다.
- `plugins/healing2shorts/skills/healing2shorts/templates/story-candidates.template.json`: 신규 후보 버전을 3으로 변경했다.
- `plugins/healing2shorts/skills/healing2shorts/agents/openai.yaml`, `plugins/healing2shorts/README.md`, `plugins/healing2shorts/.codex-plugin/plugin.json`: 사용자 표시와 기본 호출 문구를 대화형 힐링 썰 기준으로 갱신했다.
- `docs/complete/2026-08-25-healing2shorts-story-01-review.md`: 기존 검토본을 최종 진행하지 않는 재작업 대상으로 표시했다.

## 검증 결과

- Python 구문 검사: 통과
- 표준 라이브러리 단위 테스트 14개: 통과
- story template·plugin manifest JSON 검사: 통과
- Skill quick validator: 통과
- Plugin validator: 통과
- 설치본 Skill·Plugin validator: 통과
- 설치 상태: `healing2shorts@news2shorts-local 0.4.0+codex.20260825113823` installed, enabled
- 프론트엔드 빌드: 수행하지 않음

## 제작 경계

- 기존 `story-01` 검토본은 삭제하지 않고 실패 원인 확인용 로컬 기록으로 보존했다.
- 신규 대화형 영상은 후보를 자동 선택하지 않고 최대 3개를 비교한 뒤 사용자의 선택을 받아 제작한다.
- v3 형식 검증은 스토리 구조를 확인하지만 실제 사연의 사실성, 동의, 플랫폼 승인 또는 수익화를 보장하지 않는다.
