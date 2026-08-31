# Shorts Discovery YouTube Data API 옵션 완료

## 완료 내용

- `시니어 쇼츠`의 공개 메타데이터 수집·키체인·TLS 검증 방식을 참고해 `shorts-discovery`에 독립적인 YouTube Data API 옵션을 추가했다.
- 브라우저·공개 웹 조사는 기본 경로로 유지하고 API는 사용자가 요청할 때 쓰는 선택형 신호 수집 경로로 분리했다.
- API 키는 `YOUTUBE_API_KEY` 환경변수를 먼저 사용하고 macOS에서는 `shorts-suite.youtube-data-api-key` 키체인 항목을 두 번째로 사용한다.
- `configure-youtube`는 키를 명령 인자나 로그에 넣지 않고 macOS 키체인의 숨김 입력을 사용한다.
- `doctor --check-youtube --json`은 키 값 없이 구성 출처, 연결 상태, 키체인 조회 제한, TLS CA 경로를 보고한다.
- `youtube-signals`는 검색어별 `search.list` 한 페이지와 배치 `videos.list`를 사용해 다음 공개 메타데이터를 수집한다.
  - 제목, 채널, 게시 시각, 길이
  - 조회수, 좋아요, 댓글 수
  - 시간당 조회 신호, 좋아요율, 댓글률
  - 검색어, API 호출 횟수, 수집 시각
- 결과는 `discovery_lead`, `browser_verification_required: true`, `rights.status: unknown`, `reuse_allowed: false`로 고정한다.
- API 신호와 브라우저 검증을 함께 사용한 후보 배치는 `collection_method: hybrid_youtube_api_browser`를 기록할 수 있게 했다.

## 명령

```text
python3 -B plugins/shorts-suite/scripts/shorts_suite.py discover configure-youtube
python3 -B plugins/shorts-suite/scripts/shorts_suite.py discover doctor --check-youtube --json

python3 -B plugins/shorts-suite/scripts/shorts_suite.py discover youtube-signals \
  --query "unexpected company response" \
  --hours 48 \
  --region-code US \
  --relevance-language en
```

## 변경 파일

- `plugins/shorts-suite/scripts/discover.py`: API 키·키체인·TLS·doctor·공개 메타데이터 신호 수집
- `plugins/shorts-suite/skills/shorts-discovery/SKILL.md`: browser/API/hybrid 조사 모드와 증거 경계
- `plugins/shorts-suite/skills/shorts-discovery/references/youtube-data-api.md`: 설정·수집·출력·보안 계약
- `plugins/shorts-suite/skills/shorts-discovery/references/research-workflow.md`: API 보조 조사 흐름
- `plugins/shorts-suite/skills/shorts-discovery/references/candidate-schema.md`: hybrid 수집 방식
- `plugins/shorts-suite/README.md`, `README.md`: 사용 명령과 현재 역할 안내
- `plugins/shorts-suite/.codex-plugin/plugin.json`: YouTube API 조사 기능 설명

## 보존 경계

- API 신호만으로 후보를 확정하거나 자동 선택하지 않는다.
- API 메타데이터만으로 화면 내용, Shorts 여부, 원본 소유권, Korean Gap, 권리를 확정하지 않는다.
- 영상·썸네일·자막·음성·댓글을 다운로드하지 않는다.
- OAuth, 비공개 계정 데이터, 업로드, 수정, 삭제는 포함하지 않는다.
- API 키를 저장소, URL 쿼리, 프로젝트 JSON, 로그, 대화에 기록하지 않는다.
- TLS 인증서 검증을 끄지 않는다.
- DB, 스케줄러, 렌더링, 업로드는 이번 범위에 포함하지 않았다.

## 공식 API 확인

- Google `search.list`: 공개 검색 결과 ID와 snippet 조회, `publishedAfter`, `regionCode`, `relevanceLanguage`, `maxResults` 지원
- Google `videos.list`: 영상 ID별 snippet, statistics, contentDetails, status 조회
- 2026년 granular quota 전환에 맞춰 고정 unit 합계를 적지 않고 실제 호출 횟수만 결과에 기록한다.

## 검증 범위

- Plugin validator: 통과
- `shorts-discovery` Skill validator: 통과
- `discover.py`, `youtube-signals`, 공통 라우터 도움말: 정상 로딩
- 비연결 doctor: 플러그인 준비 상태 정상, YouTube API 선택 옵션과 TLS CA 경로 확인
- 설치 버전: `shorts-suite@news2shorts-local` `0.1.0+codex.20260828094617`
- 실제 API 요청, API 키 설정, 자동화 테스트, 프론트엔드 빌드, 영상 렌더, 외부 다운로드, DB 작업은 수행하지 않는다.
