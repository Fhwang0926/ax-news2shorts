# tiktok2shorts 최소 입력 호출 개선 완료

## 완료 내용

- 플러그인 버전을 `0.3.5+codex.20260816`으로 올렸다.
- `$tiktok2shorts` 단독 호출이나 `찾아줘` 같은 짧은 요청을 화이트보드용 TikTok 동물 후보 조사로 처리하도록 기본 동작을 추가했다.
- 사용자가 다시 적지 않아도 조회수 100만 이상과 보조 지표, 화이트보드 적합도와 필수 하한, 후보 최대 3개, 출처·권리 상태, 선택 전 다운로드 금지 조건을 자동 적용하도록 스킬 규칙을 명시했다.
- 후보 선택은 `1번`처럼 번호만 받아 로컬 다운로드·프레임 검토·분석·요청된 화이트보드 인계까지 이어 가고, 실제 중단 사유가 없으면 같은 진행 확인을 반복하지 않도록 했다.
- 스킬 선택 시 짧은 기본 요청이 채워지도록 `agents/openai.yaml`을 추가하고 플러그인 시작 문구의 첫 항목을 `화이트보드용 동물 영상 찾아줘.`로 줄였다.
- 기존 점수 계산, 권리 판정, 다운로드 차단, 렌더러 코드는 변경하지 않았다.

## 변경 파일

- `plugins/tiktok2shorts/skills/tiktok2shorts/SKILL.md`: 단독 호출과 짧은 요청에 적용되는 기본 조건·번호 선택 계약을 추가했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/agents/openai.yaml`: 스킬 호출 기본 문구와 UI 설명을 추가했다.
- `plugins/tiktok2shorts/.codex-plugin/plugin.json`: 버전, 단독 호출 설명, 짧은 첫 시작 문구를 반영했다.
- `plugins/tiktok2shorts/README.md`: 사용자가 실제로 입력할 최소 문구와 자동 적용 조건을 안내했다.
- `docs/complete/2026-08-16-tiktok2shorts-minimal-invocation.md`: 당일 작업과 검증 범위를 기록했다.

## 검증 범위

- 플러그인 매니페스트 JSON 구문 검사를 통과했다.
- 공식 `quick_validate.py`와 Ruby YAML 검사에서 스킬 frontmatter와 `agents/openai.yaml` 구조가 유효함을 확인했다.
- Codex 로컬 플러그인을 갱신하고 설치·활성화된 버전이 `0.3.5+codex.20260816`임을 확인했다.
- 설치 캐시에서 `$tiktok2shorts` 기본 문구와 최소 입력 계약이 포함된 것을 확인했다.
- 영상 다운로드·프로젝트 생성·렌더링은 수행하지 않았다.
- 프론트엔드 빌드는 수행하지 않았다.
