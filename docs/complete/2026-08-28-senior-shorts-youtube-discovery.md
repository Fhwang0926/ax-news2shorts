# 시니어 쇼츠 YouTube 소재 발굴 개선 완료

## 완료 범위

- `senior-shorts`에 YouTube Data API v3 공개 메타데이터 기반 `discover` 명령을 추가했다.
- 기본 90일, 한국어 검색어 3개, 검색어당 10개를 한 페이지씩 조회하며 180초 이하 영상만 중복 제거해 소재 신호로 기록한다.
- 조회 속도, 댓글 참여율, 최신성, 시니어 관련 제목 표현을 합산한 내부 적합도 점수를 추가했다.
- 영상 제목, 채널, 게시 시각, 길이, 조회·좋아요·댓글 수와 canonical URL만 기록하고 영상, 썸네일, 댓글, 자막은 다운로드하지 않는다.
- 공개 메타데이터를 사용 허가로 해석하지 않고 모든 신호에 `signal_only`, `reuse_allowed: false`, `pattern_only` 경계를 기록한다.
- YouTube 신호에서 정확히 3개의 독립 창작 후보를 작성하는 템플릿과 계약을 추가했다.
- 후보를 자동 선택하지 않고 사용자가 지정한 후보 ID만 `select` 명령으로 `selection.json`에 기록한다.
- 기존 `init`에 `--selection` 입력을 추가하고 선택 기록을 프로젝트 `discovery/selection.json`에 보존한다.
- 공개 데이터 API 키를 `YOUTUBE_API_KEY` 환경변수 우선, macOS 키체인 후순위로 읽도록 구현했다.
- `configure-youtube`가 키를 명령 인자에 넣지 않고 macOS 키체인의 숨김 password 입력으로 저장·교체하도록 구현했다.
- API 키는 URL 쿼리 대신 `X-Goog-Api-Key` 헤더로 전달하며 파일과 로그에 값을 남기지 않는다.
- `doctor --check-youtube --json`에 키 설정 출처, 키체인 접근 제한, API 연결 상태와 설정 명령을 추가했다.

## 의도적으로 제외한 범위

- YouTube 영상·썸네일·댓글·자막 다운로드
- 기존 영상의 대사, 사건 순서, 반전, 결말 재사용
- 후보 자동 선택과 사용자 선택 전 대본·이미지·음성 생성
- OAuth 2.0, 비공개 채널 데이터, YouTube Analytics, 업로드·수정·삭제
- 네이버 데이터랩 API, Google Trends API, 커뮤니티 자동 수집

## 검증 경계

- Plugin manifest, Skill 구조, JSON 파일 파싱, CLI 로딩, `doctor --json`, `git diff --check`만 확인한다.
- `senior-shorts@news2shorts-local`을 `0.1.0+codex.20260828091501`로 설치했고 소스와 설치 캐시의 manifest, CLI, Skill, discovery 계약, 후보 템플릿, README SHA-256 일치를 확인했다.
- 현재 Codex 실행은 macOS 키체인 확인 제한 상태이므로 실제 키 미설정으로 단정하지 않는다.
- 사용자의 API 키를 받거나 노출하지 않았고 실제 YouTube API 요청은 수행하지 않는다.
- 사용자 지침에 따라 단위 테스트, 영상 렌더, 프론트엔드 빌드는 수행하지 않는다.

## 변경 파일

- `plugins/senior-shorts/scripts/senior_shorts.py`: 키체인 설정, API 진단, YouTube 소재 신호 수집, 후보 선택, 선택 기반 초기화를 구현했다.
- `plugins/senior-shorts/skills/senior-shorts/SKILL.md`: 소재가 없을 때 3개 창작 후보를 제시하고 선택을 기다리는 흐름을 추가했다.
- `plugins/senior-shorts/skills/senior-shorts/references/discovery-contract.md`: API 키, 신호, 창작 후보, 권리 경계를 정의했다.
- `plugins/senior-shorts/skills/senior-shorts/references/output-contract.md`: discovery 선택 기록과 검증 단계를 추가했다.
- `plugins/senior-shorts/templates/story-candidates.template.json`: 정확히 3개인 창작 후보 형식을 추가했다.
- `plugins/senior-shorts/README.md`: Google Cloud API 키 발급, 키체인 저장, 소재 발굴 사용법을 추가했다.
- `plugins/senior-shorts/.codex-plugin/plugin.json`: YouTube 소재 발굴 기능과 기본 프롬프트를 반영했다.
- `docs/complete/2026-08-28-senior-shorts-youtube-discovery.md`: 당일 개선 범위와 검증 경계를 기록했다.
