# 2026-08-21 K-Export Shorts 한국 원천 멀티플랫폼 탐색 개선

## 작업 범위

- K-Export Shorts의 소스 없는 기본 호출을 특정 연예인 YouTube 긴 영상 탐색에서 최근 한국 원천 숏폼 탐색으로 변경했다.
- 기본 탐색 플랫폼을 YouTube Shorts, TikTok, Instagram Reels로 확장했다.
- 한국어 자막이 붙은 해외 원본, 해외 워터마크 크롭, 모음 계정, 비공식 재업로드를 기본 후보에서 제외하도록 했다.
- 기존 특정 한국 연예인·그룹의 YouTube 긴 원본 탐색과 이후 장면·콘셉트 선택 흐름은 호환용으로 유지했다.
- 버전을 `0.7.0+codex.20260821`로 올리고 로컬 marketplace에 재설치했다.

## 기본 탐색·점수 계약

- 기본 탐색 기간은 최근 30일이며 필요하면 `--max-age-days`로 1~90일 사이에서 조정할 수 있다.
- 세 플랫폼은 후보가 없거나 공개 화면 접근이 막혀도 `ok`, `blocked`, `unavailable` 중 하나로 확인 기록을 남긴다.
- 후보마다 한국 기획·촬영·프로그램 맥락 근거 2개와 원제작자·공식 방송사·소속사 계정 근거 2개를 요구한다.
- `visible_reach 25`, `current_velocity 25`, `engagement_strength 15`, `korean_originality 20`, `overseas_fit 15`로 비교한다.
- 해외 원본과 비공식 재업로드는 점수와 무관하게 제외한다.
- 같은 장면의 플랫폼 간 중복이 확인되면 `content_fingerprint`로 묶고 높은 점수 후보만 유지한다.
- 최대 3개만 제시하고 기존처럼 사용자의 Candidate ID 선택 전에는 프로젝트를 초기화하지 않는다.

## 제작·권리 경계

- 선택된 공개 YouTube 소스만 기존 no-login, no-cookie, no-API 로컬 검토 취득 흐름을 사용할 수 있다.
- TikTok·Instagram 후보는 자동 다운로드하지 않으며 제작에는 사용 권한이 있는 로컬 원본이 필요하다.
- 공개 조회수와 점수는 수집 시점의 편집 우선순위 증거이며 바이럴 성과, 게시 권리, 수익화 가능성을 보장하지 않는다.

## 공개 화면 확인

- YouTube 공개 검색 화면에서 한국 예능 Shorts 제목과 조회수 표시를 확인했다.
- Instagram 공개 검색 그리드와 Reel 링크 노출을 확인했다.
- TikTok 공개 검색은 이번 확인 시 서버 오류 화면을 반환했다. 따라서 플러그인은 플랫폼 누락을 숨기지 않고 `blocked`로 기록하도록 했다.
- 이번 화면 확인은 플랫폼 탐색 가능성 검토이며 실제 제작 후보의 최근 게시일, 공식 계정, 원본성, 권리를 확정한 결과가 아니다.

## 검증 결과

- Python AST와 plugin/marketplace JSON 파싱을 통과했다.
- Skill validator와 Plugin validator가 통과했다.
- 새 `rank-viral-sources` 샘플에서 한국 원천 YouTube·TikTok 후보 2개가 통과했다.
- 더 높은 조회수를 가진 샘플 Instagram 후보는 해외 워터마크·비공식 재업로드 조건으로 제외되었다.
- TikTok 후보를 선택해 만든 프로젝트의 구조 검증이 오류 0건으로 통과했고, `acquire`가 권한 있는 로컬 원본을 요구하며 중단되는 것을 확인했다.
- 기존 아이브 YouTube 긴 영상 `rank-sources` 샘플은 후보 3개를 그대로 생성했다.
- 설치 소스와 캐시 전체가 일치했고, 캐시의 `doctor`와 Skill validator가 통과했다.
- `viral-shorts@news2shorts-local`은 `0.7.0+codex.20260821` installed, enabled 상태다.
- 프론트엔드 빌드·테스트, DB 작업, 대표 영상 렌더, 실제 업로드는 수행하지 않았다.

## 변경 파일

- `README.md`
- `plugins/viral-shorts/.codex-plugin/plugin.json`
- `plugins/viral-shorts/README.md`
- `plugins/viral-shorts/scripts/viral_shorts.py`
- `plugins/viral-shorts/skills/viral-shorts/SKILL.md`
- `plugins/viral-shorts/skills/viral-shorts/agents/openai.yaml`
- `plugins/viral-shorts/skills/viral-shorts/references/workflow.md`
- `plugins/viral-shorts/skills/viral-shorts/references/source-candidate-schema.md`
- `plugins/viral-shorts/skills/viral-shorts/references/scoring.md`
- `plugins/viral-shorts/skills/viral-shorts/references/rights-policy.md`
- `plugins/viral-shorts/skills/viral-shorts/references/output-contract.md`
- `docs/complete/2026-08-21-viral-shorts-korean-native-multiplatform-discovery.md`
