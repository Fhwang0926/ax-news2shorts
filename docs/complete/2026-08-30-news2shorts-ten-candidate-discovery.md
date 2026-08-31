# news2shorts 후보 10개 고정 탐색

## 완료 일자

- 2026-08-30

## 완료 내용

- URL이나 단일 주제가 없는 뉴스 탐색은 검증된 후보를 정확히 10개 제시하도록 변경했다.
- 후보 10개를 `1`부터 `10`까지 한 목록으로 모두 표시하고, 추천 1개를 표시하되 자동 선택하지 않는다.
- 첫 탐색에서 10개가 채워지지 않으면 남은 검색 레인, 원문 언론사 검색, 24~30시간 범위를 계속 확인한다.
- 시민 영향, 기존 주제 제외, 원문·독립 출처 검증 기준은 후보 수를 채우기 위해 낮추지 않는다.
- 외부 접근 제한으로 10개를 검증하지 못하면 `후보 조사 미완료: N/10`으로 보고하고 제작을 진행하지 않는다.
- CLI의 `--candidates`는 10만 허용한다.
- CLI 결과에 `required_candidate_count`, `discovery_complete`, `candidate_shortfall`을 추가하고 결과 버전을 6으로 올렸다.
- 검증 후보가 10개보다 적으면 결과 JSON을 남기되 종료 코드 2를 반환하도록 했다.
- `doctor` 결과에 `required_discovery_candidate_count: 10`을 추가했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/references/discovery-policy.md`
- `plugins/news2shorts/skills/news2shorts/agents/openai.yaml`
- `plugins/news2shorts/.codex-plugin/plugin.json`
- `plugins/news2shorts/README.md`
- `docs/complete/2026-08-30-news2shorts-ten-candidate-discovery.md`

## 설치 및 검증

- 설치 플러그인: `news2shorts@news2shorts-local`
- 설치 버전: `0.36.5+codex.20260829152818`
- 작업본 Skill validator: 통과
- 작업본 Plugin validator: 통과
- 설치본 Skill validator: 통과
- 설치본 Plugin validator: 통과
- Python 구문 확인: 통과
- 플러그인 JSON 구문 확인: 통과
- 변경 파일 공백 검사: 통과
- 작업본과 설치 캐시의 manifest, script, README, SKILL, 발견 정책, UI 메타데이터: 일치
- 설치본 `doctor --json`: `required_discovery_candidate_count: 10` 확인
- 설치본 `discover --help`: `--candidates {10}` 확인

## 재조사

- 뉴스픽 공개 뉴스와 실시간 키워드, NAVER News, 원문 웹 검색, 공식 자료를 다시 확인했다.
- 기존 프로젝트와 같은 뉴스 군집을 제외한 검증 후보 10개를 제시했다.
- 후보 선택 전 프로젝트 생성, 대본, 이미지, 음성, 영상 렌더는 수행하지 않았다.

## 수행하지 않은 작업

- 프론트엔드 빌드와 자동화 테스트는 수행하지 않았다.
- DB 조회·초기화·리셋 작업은 수행하지 않았다.
- YouTube 업로드, 예약, 게시, 댓글 등록은 수행하지 않았다.
