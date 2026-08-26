# 2026-08-19 Viral Shorts 브라우저 영상 후보 탐색 작업 완료

## 작업 범위

- 영상이 없는 요청에서도 특정 연예인 또는 그룹명을 기준으로 YouTube 긴 영상 후보를 찾도록 Skill 흐름을 확장했다.
- 후보 탐색은 Codex Browser Use의 YouTube 검색·watch 화면만 사용하고, YouTube Data API와 API key 입력을 사용하지 않도록 고정했다.
- Shorts, 타깃 불일치, 재생 불가, 중복 영상을 제외하고 최대 3개만 비교하도록 했다.
- 타깃 적합성, 사건 밀도 예상, 긴 영상 적합성, 맥락 독립성, 화면에 표시된 관심 신호를 합산하는 Source Candidate Score를 추가했다.
- 브라우저 근거 JSON을 검증·점수화하는 `rank-sources` 명령과 `source-candidates.json`, `source-candidates.md` 출력을 추가했다.
- 사용자가 Candidate ID를 선택한 뒤에만 `init --source-candidate-file --candidate-id`로 프로젝트를 만들고 `source-selection.json`에 선택을 보존하도록 했다.
- 로컬 재생·분석 모드에서는 제작자 출처와 권리 근거를 필수로 요구하지 않되, 운영상 다시 열기 위한 watch URL은 보존하도록 했다.
- 로컬 모드가 다운로드·편집·게시·수익화 권한을 뜻하지 않는다는 경계를 유지했다.
- 기존 로컬 영상, 직접 URL, 자막 가져오기, Moment Score, 사용자 구간 선택 흐름은 유지했다.

## 브라우저 확인

- Codex 인앱 Browser Use에서 `프로미스나인 예능 인터뷰 비하인드`로 YouTube 검색 화면을 열었다.
- 검색 결과에 긴 `/watch` 영상과 Shorts가 섞여 있고, 제목·채널·길이·조회수·게시 시점·자막 표시를 화면에서 수집할 수 있음을 확인했다.
- 대표 긴 영상 watch 페이지를 열어 재생 페이지 접근, 타깃명이 포함된 영상 제목, 여러 챕터 제목을 확인했다.
- API key, 로그인, 쿠키, CAPTCHA, 외부 검색 API는 사용하지 않았다.

## 검증 경계

- Python 소스를 AST로 정적 파싱했다.
- Plugin manifest와 marketplace JSON 형식을 정적 확인했다.
- Skill validator와 Plugin validator가 통과했다.
- 소스와 설치 캐시의 `viral_shorts.py` SHA-256이 일치했다.
- `viral-shorts@news2shorts-local` 0.2.0 버전이 설치·활성화된 것을 확인했다.
- CLI 명령의 기능 테스트, 실제 후보 JSON 실행, 영상 다운로드, 자막 분석, 렌더링, 프론트엔드 빌드·테스트, DB 작업은 수행하지 않았다.

## 변경 파일

- `README.md`
- `plugins/viral-shorts/.codex-plugin/plugin.json`
- `plugins/viral-shorts/README.md`
- `plugins/viral-shorts/scripts/viral_shorts.py`
- `plugins/viral-shorts/skills/viral-shorts/SKILL.md`
- `plugins/viral-shorts/skills/viral-shorts/agents/openai.yaml`
- `plugins/viral-shorts/skills/viral-shorts/references/source-candidate-schema.md`
- `plugins/viral-shorts/skills/viral-shorts/references/workflow.md`
- `plugins/viral-shorts/skills/viral-shorts/references/rights-policy.md`
- `plugins/viral-shorts/skills/viral-shorts/references/output-contract.md`
- `docs/complete/2026-08-19-viral-shorts-browser-source-discovery.md`
