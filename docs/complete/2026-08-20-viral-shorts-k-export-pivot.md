# 2026-08-20 Viral Shorts K-Export 피벗

## 작업 범위

- 기존 `viral-shorts` 기술 식별자와 소스 탐색·취득·장면 정규화·선택 흐름을 유지하면서 사용자 노출명을 `K-Export Shorts`로 변경했다.
- 특정 한국 연예인·그룹의 선택 장면을 영어권 `en-US`와 일본어권 `ja-JP`용으로 각각 재구성하는 흐름을 추가했다.
- API key 없이 Codex Browser Use로 시장별 Shorts 참고 패턴을 1~3개 수집하고 검증하는 `trend-pack` 명령을 추가했다.
- 영어·일본어 후킹, 제목, 설명, 해시태그, 컷, 자막, 사운드 큐를 독립적으로 포함한 정확히 3개 콘셉트를 비교하는 `export-concepts`와 명시적 사용자 선택용 `select-export`를 추가했다.
- 원본 한국어 오디오를 유지하면서 시장별 멀티컷·속도·줌·후킹·자막 스타일을 적용해 두 MP4를 따로 만드는 `render-export`와 양언어 결과 검증용 `validate-export`를 추가했다.
- 강한 어그로, POV, `w`, 인터넷 밈과 코믹 과장은 허용하되 선택 영상이 후킹을 회수하도록 했다. 조작된 대사·관계·동기·사건은 사실처럼 사용할 수 없고, 허구는 양언어에 패러디 표시가 있어야 렌더 선택할 수 있다.
- 해외판 화면에는 `로컬 검토용` 배지를 표시하지 않는다. 권리 미확인 결과는 JSON에 `local_review_only: true`, `publication_ready: false`를 유지한다.
- 자동 음원 다운로드, 업로드, API key, DB, 웹 UI는 추가하지 않았다.

## 아이브 Browser Use 적용

- 영어권 참고 Shorts 1개와 일본어권 아이브 참고 Shorts 1개를 YouTube 화면에서 확인했다.
- 화면에 보인 제목, 조회수·좋아요·댓글 텍스트, 첫 화면의 후킹·자막 계층, 확인 가능한 사운드 정보만 `trend-pack-input.json`에 기록했다.
- 참고 영상의 미디어·워터마크·브랜딩·음원·정확한 편집 순서는 재사용하지 않고 구조적 패턴만 기록했다.
- 기존 아이브 장원영 선택 장면에 대해 영어·일본어 독립 처리된 역수출 콘셉트 3개를 생성했다.
- 실제 사용자 프로젝트에는 콘셉트를 자동 선택하지 않았으며 현재 상태는 `export_concepts_ranked`이다.

## 검증 결과

- Python AST, JSON 파싱, Plugin validator, Skill validator, CLI `--help`, `doctor`를 통과했다.
- 기존 아이브 프로젝트의 `validate`가 오류 0건으로 통과해 이전 소스·장면·한국어 렌더 흐름이 유지됨을 확인했다.
- 임시 검증 프로젝트에서 1위 콘셉트를 선택해 영어판과 일본어판을 각각 실제 렌더했다.
- 두 결과 모두 17.7초, 720x1280, H.264, AAC, 30fps였고 `validate-export`가 오류 0건으로 통과했다.
- 영어·일본어 후킹과 자막 배치를 대표 프레임으로 시각 확인했다. 영어 컬러 이모지가 시스템 글꼴에서 네모로 보인 문제는 영상 오버레이에서 `T_T`, `LOL` 등 읽을 수 있는 텍스트로 대체하도록 보완했다.
- 임시 검증본의 영어 SHA-256은 `e86c537107e5ef6249ff65fb5b365210a43963859ac720a6d1c69c1dafbc5ed5`, 일본어 SHA-256은 `d1add530ba2a597e9f0cd6ef706c89fcf3c7fcfe740430c191b7b2a4e5dee2eb`이다.
- 원본 권리는 `unknown`으로 유지되어 렌더 검증은 게시·수익화 권리 증명이 아니다.
- 프론트엔드 빌드·테스트와 DB 작업은 수행하지 않았다.
- 소스와 설치 캐시의 핵심 파일 SHA-256이 일치하는 `0.4.0+codex.20260820083158`을 `news2shorts-local`에 재설치했다.

## 변경 파일

- `README.md`
- `plugins/viral-shorts/.codex-plugin/plugin.json`
- `plugins/viral-shorts/README.md`
- `plugins/viral-shorts/scripts/viral_shorts.py`
- `plugins/viral-shorts/skills/viral-shorts/SKILL.md`
- `plugins/viral-shorts/skills/viral-shorts/agents/openai.yaml`
- `plugins/viral-shorts/skills/viral-shorts/references/workflow.md`
- `plugins/viral-shorts/skills/viral-shorts/references/rights-policy.md`
- `plugins/viral-shorts/skills/viral-shorts/references/output-contract.md`
- `plugins/viral-shorts/skills/viral-shorts/references/scoring.md`
- `plugins/viral-shorts/skills/viral-shorts/references/export-schema.md`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/project.json`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/trend-pack-input.json`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/trend-pack.json`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/trend-pack.md`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/export-concepts-input.json`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/export-concepts.json`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/export-concepts.md`
- `docs/complete/2026-08-20-viral-shorts-k-export-pivot.md`
