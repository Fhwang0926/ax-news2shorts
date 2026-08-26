# news2shorts 직접 시민 영향 관문 개선

## 완료 일자

- 2026-08-25

## 반영 범위

- 뉴스 후보가 추천 목록에 들어가기 전에 영향받는 시민 집단과 직접 비용·안전·권리·공공서비스 결과를 함께 확인하는 관문을 추가했다.
- `누가 무엇을 얼마나 잃거나 위험해지는가`를 출처로 뒷받침되는 한 문장으로 설명하지 못하면 최종 후보에서 제외하도록 스킬과 발견 정책을 보강했다.
- 외부 시민 결과가 없는 조직 내부 성과급·임원·주주 이슈와 시민 피해가 없는 정치 공방·절차 발표는 점수가 높아도 추천되지 않도록 했다.
- 자동 발견 결과에서 통과 후보는 `candidates`, 탈락 후보와 사유는 `rejected_candidates`로 분리했다.
- 플러그인 버전을 `0.34.0+codex.20260825144543`으로 갱신했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 직접 시민 영향 분류와 추천 후보 필터.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 후보의 필수 시민 결과 문장과 탈락 규칙.
- `plugins/news2shorts/skills/news2shorts/references/discovery-policy.md`: 점수보다 먼저 적용하는 시민 영향 관문.
- `plugins/news2shorts/README.md`: `candidates`와 `rejected_candidates` 동작 설명.
- `plugins/news2shorts/.codex-plugin/plugin.json`: 설명과 버전.

## 검증 결과

- Python AST, 스킬 구조, 플러그인·마켓플레이스 JSON 검사를 통과했다.
- 합성 사례에서 시민 비용·안전·근로자 권리 후보는 통과하고, 조직 내부 성과급과 시민 결과 없는 정당 공방은 탈락했다.
- `news2shorts@news2shorts-local` `0.34.0+codex.20260825144543` 설치·활성화를 확인했다.
- 설치본 `doctor --json`은 `ok: true`였고, 원본과 설치 캐시의 스크립트·스킬·발견 정책이 일치했다.
- 프론트엔드 빌드, DB 작업, 외부 게시와 영상 렌더는 수행하지 않았다.
