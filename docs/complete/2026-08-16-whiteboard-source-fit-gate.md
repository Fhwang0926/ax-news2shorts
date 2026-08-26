# 화이트보드 원본 적합도 선정·사전 검사 개선

## 완료 내용

- 기존 TikTok 기본 후보 점수화는 유지하고 `score --target-format whiteboard` 선택 경로를 추가했다.
- 화이트보드 후보 총점을 검증된 바이럴 25, 첫 2초 훅 20, 서로 다른 행동 20, 추상화 후 결말 20, 윤곽·구도 10, 한국 관련성 5로 분리했다.
- 총점 70점 외에도 훅 12점, 결말 12점, 구도 6점, 서로 다른 행동 3개와 부적합 사유 없음 조건을 모두 통과하도록 했다.
- 선택 결과의 `whiteboard_fit_assessment`를 TikTok2Shorts 프로젝트 `source.json`에 보존하도록 했다.
- Whiteboard Shorts에 `preflight --source-project`를 추가해 가져오기 전에 다음을 검사하도록 했다.
  - 통과한 화이트보드 후보 점수와 원본 후보 근거
  - 다운로드 후 검토 완료 상태
  - 실제 미리보기 프레임 6장 이상과 파일 존재
  - 서로 다른 실제 행동 3개 이상
  - hook, turn/payoff, conclusion 장면 역할
- 사전 검사 결과를 새 화이트보드 프로젝트의 `project.json.source_origin.whiteboard_fit`에 보존하도록 했다.
- 스킬, 후보 스키마, 예시, README, 플러그인 설명과 버전을 새 흐름에 맞췄다.
- 기존 골든리트리버 결과물과 프로젝트 파일은 변경하지 않았다.

## 변경 파일

- `plugins/tiktok2shorts/scripts/tiktok2shorts.py`
- `plugins/tiktok2shorts/skills/tiktok2shorts/SKILL.md`
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/candidate-schema.md`
- `plugins/tiktok2shorts/examples/candidates.sample.json`
- `plugins/tiktok2shorts/README.md`
- `plugins/tiktok2shorts/.codex-plugin/plugin.json`
- `plugins/whiteboard-shorts/scripts/whiteboard_shorts.py`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/SKILL.md`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/agents/openai.yaml`
- `plugins/whiteboard-shorts/README.md`
- `plugins/whiteboard-shorts/.codex-plugin/plugin.json`

## 검증

- 두 Python 스크립트 구문 검사 통과
- 관련 JSON 파일 `jq empty` 통과
- 기본 TikTok 점수화 회귀 통과
- 화이트보드 대상 예시 후보 점수화 통과: 91.13점, 적합 판정
- 화이트보드 근거가 없는 기존 후보 거절 확인
- 점수화 결과가 새 TikTok 프로젝트 `source.json`으로 전달되는 것 확인
- 임시 로컬 fixture에서 `preflight` 통과, Whiteboard Shorts 가져오기와 정적 검증 통과
- 두 스킬의 frontmatter와 `openai.yaml` 구조 검사 통과
- 공식 `quick_validate.py`는 시스템과 작업공간 Python 모두 `PyYAML` 미설치로 실행 불가하여 동일 검사항목을 로컬 Ruby YAML 파서로 확인
- Codex 로컬 플러그인 설치 갱신 확인
  - `tiktok2shorts` `0.3.1+codex.20260816`
  - `whiteboard-shorts` `0.2.0+codex.20260816`
- 프론트엔드 빌드는 수행하지 않음

## 남은 운영 조건

- 새 버전의 Whiteboard Shorts 설치 캐시는 렌더러 격리 환경이 아직 준비되지 않아 `ready_for_render=false`다.
- 후보 조사와 `preflight`는 사용할 수 있으며, 새 영상을 실제 렌더링할 때 사용자의 명시 요청 후 `setup`을 한 번 실행해야 한다.
- 점수와 기술 검증은 바이럴 성과, 게시 권리, 플랫폼 승인 또는 수익화를 보장하지 않는다.
