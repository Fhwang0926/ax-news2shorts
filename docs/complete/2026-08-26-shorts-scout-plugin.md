# Shorts Scout 플러그인 구현 완료

## 요청

- 브라우저로 공유된 `원본 음성 출처 비교` 대화의 Shorts Scout 개발 계획을 참고한다.
- 해외 바이럴 영상 중 한국어 설명형 Shorts로 발전시키기 좋은 원본 후보를 조사하는 Codex 플러그인을 만든다.

## 반영 범위

- 사용자 노출명 `Shorts Scout`, 기술 식별자 `shorts-scout`를 유지했다.
- 최근 48시간 공개 영상 조사와 사용자 제공 URL 비교 모드를 정의했다.
- YouTube Shorts, TikTok, Instagram Reels, X, Reddit 및 기타 공개 출처를 후보 플랫폼으로 지원한다.
- Early Viral, Hook, Story/Twist, Korean Gap, Explainability, Visual Clarity, Source Traceability, Editability의 100점 평가 계약을 구현했다.
- Korean Gap은 유사 한국 결과 수, Source Traceability는 원출처 상태에서 결정적으로 계산한다.
- 고정 위험 감점, 공개 확인·정확한 지표·관찰 장면·시간 범위·권리 상태의 적격성 게이트를 구현했다.
- URL과 실제 사건 지문으로 중복 후보를 제거하고 최대 3개만 반환한다.
- 결과는 항상 `awaiting_user_selection`, `automatic_selection: false`, `publication_ready: false`로 유지한다.
- `unknown`, `repost_only`, `not_permitted` 등 출처·권리 상태를 임의 승격하지 않는다.
- 로컬 마켓플레이스 `news2shorts-local`에 등록하고 Codex에 설치했다.

## 최소 구현 결정

공유 계획의 장기 항목 중 플랫폼 API 자격증명, SQLite/PostgreSQL, 스케줄러, Chrome 확장 프로그램, 대량 다운로드, 전 후보 Vision 분석, 피드백 학습, 영상 제작·업로드 파이프라인은 이번 MVP에 넣지 않았다.

현재 버전은 다음 두 구성만 사용한다.

1. 공개 근거를 조사하고 후보를 기록하는 Codex Skill
2. Python 표준 라이브러리만 사용하는 검증·랭킹 CLI

## 변경 파일

- `.agents/plugins/marketplace.json`: `shorts-scout` 로컬 플러그인 항목 추가
- `plugins/shorts-scout/.codex-plugin/plugin.json`: 플러그인 메타데이터, UI 이름, 기본 요청, 버전 정의
- `plugins/shorts-scout/skills/shorts-scout/SKILL.md`: 조사 흐름, 최대 3개 비교, 사용자 선택, 접근·권리 경계 정의
- `plugins/shorts-scout/skills/shorts-scout/agents/openai.yaml`: Skill 표시 정보 정의
- `plugins/shorts-scout/skills/shorts-scout/references/research-workflow.md`: 공개 근거 조사, 원출처 추적, Korean Gap, 결과 표시 절차
- `plugins/shorts-scout/skills/shorts-scout/references/candidate-schema.md`: 조사 후보 JSON 입력 계약
- `plugins/shorts-scout/skills/shorts-scout/references/scoring.md`: 점수, 감점, 적격성, 중복 제거 계약
- `plugins/shorts-scout/scripts/shorts_scout.py`: `doctor`, `validate`, `rank` 명령 구현

## 확인 결과

- Skill 구조 검증 통과
- Plugin 구조 검증 통과
- 매니페스트와 마켓플레이스 JSON 구문 확인 통과
- 소스 CLI `--help`와 `doctor --json` 실행 확인
- 설치 캐시 CLI `--help`와 `doctor --json` 실행 확인
- 소스와 설치 캐시의 매니페스트, Skill, CLI SHA-256 일치
- `shorts-scout@news2shorts-local` 설치 및 활성화 상태 확인

AGENTS.md 지침에 따라 프론트 빌드와 프로젝트 테스트는 실행하지 않았다. 실제 최신 후보 리서치, 로그인된 플랫폼 화면 확인, 외부 API 연동, 영상 다운로드·제작·업로드는 이번 작업의 검증 범위가 아니다.
