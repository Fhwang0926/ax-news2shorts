# 2026-08-21 BTS 쇼츠 원본 후보 탐색

## 작업 범위

- BTS를 대상으로 YouTube 장편 예능·인터뷰·비하인드 후보를 탐색했다.
- Codex Browser Use의 YouTube 검색 및 watch 화면만 사용했다.
- Shorts, 팬 재편집본, 멤버 단독 중심 영상은 후보에서 제외했다.
- 공식 BANGTANTV 영상 중 형식이 다른 후보 3개를 비교하고 Source Candidate Score를 생성했다.
- 사용자가 Candidate ID를 선택하기 전이므로 프로젝트 초기화, 영상 확보, 장면 분석, 쇼츠 렌더링은 수행하지 않았다.

## 후보 결과

- `bts-run-telepathy-002`: 97.8점
- `bts-trip-ep1-001`: 96.8점
- `bts-behind-interview-003`: 90.8점

## 선택 후 장면 분석

- 사용자가 1번 `bts-run-telepathy-002`를 명시적으로 선택했다.
- 프로젝트를 `projects/viral-shorts/2026-08-21-bts-run-telepathy`에 초기화했다.
- 한국어 자막, 메타데이터, 공개 스토리보드를 확보하고 21개 시각 근거 프레임을 검토했다.
- 일반 공개 다운로드는 YouTube HTTP 403으로 실패했으며 승인되지 않은 원격 EJS는 사용하지 않았다.
- 이후 사용자가 원격 EJS 사용을 명시적으로 승인해 승인 문구를 `source.json`에 기록했다.
- 승인된 원격 EJS와 공개 Safari HLS 대체 경로까지 다시 시도했으나 두 영상 경로 모두 HTTP 403으로 실패했다.
- 자막·메타데이터·스토리보드는 보존됐지만 원본 MP4가 없어 렌더링은 로컬 영상 제공 전까지 진행할 수 없다.
- 자막과 검토한 스토리보드 근거를 바탕으로 장면 후보 3개를 점수화했다.
- `bts-telepathy-001-saru-reveal`: 91.9점
- `bts-telepathy-002-choreo-eye-contact`: 87.9점
- `bts-telepathy-003-pc-power-reaction`: 87.2점
- 사용자가 Moment Candidate ID를 선택하기 전이므로 장면 확정, 해외 트렌드 조사, 콘셉트 작성과 렌더링은 수행하지 않았다.

## 검증 경계

- 세 영상 모두 로그인 없이 watch 페이지가 열리는 것을 확인했다.
- 화면에 표시된 제목, 채널, 길이, 조회수, 게시일, 좋아요 수를 기록했다.
- API key, YouTube Data API, 로그인, 쿠키, CAPTCHA 우회는 사용하지 않았다.
- 원본 권리와 게시·수익화 가능 여부는 확인되지 않았으며 현재 결과는 로컬 검토용이다.
- 원본 MP4가 없어 공개 스토리보드만으로 세부 표정과 연속 동작을 확정할 수 없으며, 렌더 전 영상 확보가 필요하다.
- 프론트엔드 빌드·테스트와 DB 작업은 수행하지 않았다.

## 생성 파일

- `projects/viral-shorts/discovery/2026-08-21-bts-fun-edit/browser-candidates.json`
- `projects/viral-shorts/discovery/2026-08-21-bts-fun-edit/source-candidates.json`
- `projects/viral-shorts/discovery/2026-08-21-bts-fun-edit/source-candidates.md`
- `projects/viral-shorts/2026-08-21-bts-run-telepathy/project.json`
- `projects/viral-shorts/2026-08-21-bts-run-telepathy/source-selection.json`
- `projects/viral-shorts/2026-08-21-bts-run-telepathy/source.json`
- `projects/viral-shorts/2026-08-21-bts-run-telepathy/transcript.json`
- `projects/viral-shorts/2026-08-21-bts-run-telepathy/moments-input.json`
- `projects/viral-shorts/2026-08-21-bts-run-telepathy/candidates.json`
- `projects/viral-shorts/2026-08-21-bts-run-telepathy/candidates.md`
- `projects/viral-shorts/2026-08-21-bts-run-telepathy/assets/source/source.info.json`
- `projects/viral-shorts/2026-08-21-bts-run-telepathy/assets/source/source.ko.vtt`
- `projects/viral-shorts/2026-08-21-bts-run-telepathy/assets/source/storyboard.mhtml`
- `projects/viral-shorts/2026-08-21-bts-run-telepathy/assets/evidence/storyboard-evidence.json`
- `docs/complete/2026-08-21-bts-source-candidates.md`
