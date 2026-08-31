# Shorts Globalizer 뇌전구 Shorts 후보 조회 작업 완료

## 완료 내용

- `shorts-globalizer`가 뇌전구 채널의 일반 동영상 탭이나 이름 검색 결과가 아니라, 확인된 채널 ID `UCbr855WAFQvAX-An7IcHFXg`의 공개 `/shorts` 탭만 조회하도록 `discover` 명령을 추가했다.
- `discover`는 기본 3개, 선택적으로 최대 10개 후보의 제목·공개 조회수·Shorts URL을 반환한다.
- 후보를 최신순이나 조회수로 자동 선택하지 않고 항상 `selection_required: true`로 중단한다.
- 조회는 일회성으로만 수행하고 `monitoring_enabled: false`를 기록한다. 스케줄러, 채널 모니터링, 프로젝트 자동 생성은 추가하지 않았다.
- 사용자가 후보 하나를 선택한 이후에만 기존 단일 URL `init --url` 흐름으로 이어지도록 스킬 계약을 수정했다.
- 원 Shorts가 사실 출처나 재사용 가능한 영상·음성·자막·브랜딩이 아니라는 기존 경계를 유지했다.
- 로컬 플러그인 캐시 버전을 `0.1.0+codex.20260828012215`로 갱신하고 `news2shorts-local` 마켓플레이스에서 설치했다.

## 변경 파일

- `plugins/shorts-globalizer/.codex-plugin/plugin.json`
- `plugins/shorts-globalizer/README.md`
- `plugins/shorts-globalizer/scripts/shorts_globalizer.py`
- `plugins/shorts-globalizer/skills/shorts-globalizer/SKILL.md`
- `plugins/shorts-globalizer/skills/shorts-globalizer/agents/openai.yaml`
- `plugins/shorts-globalizer/skills/shorts-globalizer/references/workflow.md`
- `plugins/shorts-globalizer/skills/shorts-globalizer/references/project-contract.md`
- `plugins/shorts-globalizer/tests/fixtures/brainbulb-shorts.jsonl`
- `plugins/shorts-globalizer/tests/test_shorts_globalizer.py`

## 검증 결과

- Python 단위·전체 흐름 테스트 12개 통과
- Python 구문 검사 통과
- 플러그인 validator 통과
- 스킬 validator 통과
- `doctor --json`: 뇌전구 채널 ID·Shorts 탭, `channel_monitoring: false`, 기존 비렌더링 경계 확인
- `--help`: `discover` 명령 노출 확인
- 라이브 `discover --limit 3`: 뇌전구 Shorts 탭 후보 3개, 올바른 채널 ID, `selection_required: true`, `monitoring_enabled: false` 확인
- 설치 캐시의 manifest·CLI·SKILL 파일을 저장소 소스와 대조해 일치 확인
- 프론트엔드 변경과 DB 작업은 없으며 프론트엔드 빌드는 수행하지 않았다.

## 제한 사항

- 공개 조회수와 Shorts 탭 순서는 실행 시점마다 달라질 수 있다.
- 후보 제목과 원 Shorts는 트렌드 신호일 뿐 사실 근거가 아니다. 선택 후 독립 출처 검증이 별도로 필요하다.
- `discover`는 로그인·쿠키 없이 공개 Shorts 탭만 읽으며, 삭제·비공개·지역 제한 콘텐츠를 우회하지 않는다.
- 영상 다운로드, TTS, 렌더링, CapCut draft 수정, 업로드·게시 기능은 추가하지 않았다.
- 작업 시작 전부터 존재한 다른 플러그인과 문서 변경은 보존했다.
