# Motion2D Studio 입력 기반 모션과 음성 타임라인 개선

## 문제와 원인

- 기존 실제 프로젝트 초기화는 빈 계약만 만들고, 바로 렌더 가능한 결과는 `--demo`의 고정 7장면뿐이라 예제가 실사용 기본값처럼 보일 수 있었다.
- 장면 음성 뒤 여유는 0.35초였지만 다음 장면 전환은 최대 0.45초였다. 일부 장면에서는 마지막 약 0.1초가 다음 장면 음성과 교차해 중복되거나 잘린 것처럼 들릴 수 있었다.
- 기존 프로젝트에서 대본만 바꾸면 스토리보드와 모션 계획을 함께 다시 만드는 명시적 명령이 없었다.

## 완료 내용

- `init --script-file`로 UTF-8 대본을 입력받아 빈 줄 또는 줄 단위로 장면을 생성하도록 추가했다.
- `init --flow-file`로 장면별 내레이션, 역할, 화면 문구, 시각 포인트, 전환과 근거 ID를 입력받도록 추가했다.
- 입력 원본을 프로젝트 `inputs/`에 복사하고 SHA-256, 입력 모드와 대본 출처를 기록한다.
- 대본의 위치, 비교·과정·시스템·수치 키워드에서 장면 역할을 추론하고 실제 문구에 맞는 모션 계획을 생성한다.
- `hero`, `problem-solution`, `system-map`, `process`, `metric-focus`, `metric-grid`, `explainer`, `end-card` 역할별 레이아웃과 모션을 지원한다.
- 입력 기반 프로젝트에는 `motion-plan.json generation.mode: input-driven`과 storyboard hash를 기록하고 검증한다.
- `--demo`만 기존 Hydro Hawk 고정 예제를 사용하도록 유지하고, blank/script/flow 모드에서는 데모 플래너를 호출하지 않는다.
- 기존 프로젝트의 입력 변경용 `plan --script-file` 또는 `plan --flow-file`을 추가했다. 새 입력은 브리프, 스토리보드, 역할별 모션과 후속 TTS 캐시를 변경하며 기존 결과 파일은 삭제하지 않는다.
- 장면 음성은 진입 전환이 끝난 뒤 0.18초 후 시작한다.
- 장면 끝에는 음성 종료 후 0.25초와 다음 장면 전환 길이를 모두 확보한다.
- 장면 보고서에 음성 시작, 종료, 앞뒤 전환, 꼬리 여유와 `transition_safe`를 기록한다.
- 한국어 제목만 있는 프로젝트도 같은 slug로 충돌하지 않도록 제목 해시 기반 slug fallback을 적용했다.
- 플러그인 버전을 `0.1.0+codex.20260817145933`으로 갱신해 재설치하고 installed/enabled 상태를 확인했다.

## 변경 파일

- `plugins/motion2d-studio/scripts/motion2d_studio.py`: 입력 파서, 역할 추론, 동적 모션 플래너, `plan`, 전환 안전 음성 타임라인과 검증
- `plugins/motion2d-studio/skills/motion2d-studio/templates/project.template.json`: 입력 모드 기본값
- `plugins/motion2d-studio/skills/motion2d-studio/templates/post-production.template.json`: 음성 lead-in과 tail-gap
- `plugins/motion2d-studio/skills/motion2d-studio/templates/script-input.example.txt`: 대본 입력 예시
- `plugins/motion2d-studio/skills/motion2d-studio/templates/flow-input.example.json`: 영상 흐름 입력 예시
- `plugins/motion2d-studio/skills/motion2d-studio/references/input-contract.md`: 입력·재계획·데모 분리 계약
- `plugins/motion2d-studio/skills/motion2d-studio/references/motion-schema.md`: input-driven 생성 메타데이터
- `plugins/motion2d-studio/skills/motion2d-studio/references/output-contract.md`: 입력 원본과 음성 타임라인 보고 계약
- `plugins/motion2d-studio/skills/motion2d-studio/references/visual-playbook.md`: 입력별 역할 선택 규칙
- `plugins/motion2d-studio/skills/motion2d-studio/references/workflow.md`: 입력 보존과 검토 시점
- `plugins/motion2d-studio/skills/motion2d-studio/SKILL.md`: Codex 실행 순서와 실사용·데모 경계
- `plugins/motion2d-studio/README.md`: 사용자용 입력, 재계획과 음성 설명
- `projects/2026-08-17-motion2d-studio-demo/`: 전환 안전 구간으로 다시 렌더한 검토본

## 검증 결과

- Plugin validator와 Skill validator 통과
- Python 구문, 11개 JSON 계약, CLI 도움말과 `git diff --check` 통과
- 대본 입력 프로젝트와 영상 흐름 입력 프로젝트가 각각 input-driven 5장면으로 생성되고 render-ready 검증 통과
- 두 입력의 storyboard hash와 motion-plan hash가 서로 다름을 확인
- 대본 입력 역할: hero, problem-solution, process, metric-grid, end-card
- 영상 흐름 입력 역할: hero, system-map, explainer, metric-focus, end-card
- 두 입력을 실제 960x540, 15 FPS, H.264/AAC 검토본으로 렌더
- 모든 장면에서 음성 종료가 `장면 길이 - 다음 전환 - 0.25초` 이전이고 `transition_safe: true`임을 확인
- 수정 대본을 `plan`으로 다시 입력한 뒤 장면 수가 5개에서 4개로, 역할과 모션 hash가 변경되고 TTS settings hash도 변경됨을 확인
- 작업공간 데모 검토본도 동일한 안전 타임라인으로 다시 렌더하고 모든 장면의 `transition_safe: true` 확인
- 설치 캐시의 `init`, `plan`, `doctor` 실행과 installed/enabled 상태 확인

## 범위와 제한

- 텍스트 입력의 역할 추론은 키워드와 위치 기반 초안이며, Codex와 사용자가 스토리보드·모션 계획을 검토한 뒤 승인해야 한다.
- 동적 모션은 역할별 레이아웃 라이브러리를 사용하지만 문구, 포인트, 장면 수, 역할, 전환과 TTS는 입력을 따른다.
- 로컬 macOS TTS는 검토용이며 최종 공개본에는 권리와 품질을 확인한 음성이 필요하다.
- 임시 QA 렌더만 승인 관문을 우회했으며 `/private/tmp` 밖의 플러그인과 사용자 프로젝트에는 우회 설정을 넣지 않았다.
- 사용자 지침에 따라 프론트엔드 빌드는 수행하지 않았고 DB는 조회·변경하지 않았다.
