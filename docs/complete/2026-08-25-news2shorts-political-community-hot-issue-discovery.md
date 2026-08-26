# news2shorts 정치·커뮤니티 핫이슈 탐색 개선

## 완료 일자

- 2026-08-25

## 반영 범위

- 기본 뉴스 검색을 정치·경제·사회·IT의 넓은 레인과 정치 책임, 시민 부담, 세금·물가·주거·연금, 안전·관리 부실, 소비자 피해·개인정보 레인으로 구성했다.
- 최근 6시간의 독립 보도 확산, 출처 다양성, 시민 민감도, 정치 관련성, 책임 이슈, 검증 준비도를 분리한 후보 우선순위 점수를 추가했다.
- 시민 민감도는 생활비, 주거·금융, 안전·건강, 교육·노동, 권리·정보, 공공서비스로 분류한다.
- 로그인 없이 확인한 공개 커뮤니티의 제목·커뮤니티명·URL만 최대 50개까지 입력할 수 있게 했다.
- 한 커뮤니티는 점수에 반영하지 않고, 서로 다른 2곳 이상에서 같은 검증 뉴스 군집이 관찰될 때만 최대 5점의 발견 신호를 적용한다.
- 커뮤니티 글·댓글·작성자·개인정보는 저장하거나 사실·국민 여론·분노의 근거로 사용하지 않도록 스킬 경계를 명시했다.
- 정치 후보는 당파 갈등만으로 우선하지 않고 시민의 돈·안전·권리·공정성·공공 신뢰에 대한 구체적 영향이 있을 때만 최종 후보로 추천하도록 했다.
- 플러그인 버전을 `0.33.0+codex.20260825140039`로 갱신하고 로컬 캐시에 재설치했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 검색 레인, 시민 민감도·정치·책임 분류, 핫이슈 점수, 최소 커뮤니티 신호 입력과 결과 메타데이터.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 정치·시민 영향·공개 커뮤니티 발견 절차와 후보 표시 규칙.
- `plugins/news2shorts/skills/news2shorts/references/discovery-policy.md`: 검색 범위, 점수 모델, 커뮤니티 안전 경계와 후보 구성 계약.
- `plugins/news2shorts/README.md`: 사용자용 탐색 동작과 `--community-signals` 설명.
- `plugins/news2shorts/.codex-plugin/plugin.json`: 설명과 버전.
- `docs/complete/2026-08-25-news2shorts-political-community-hot-issue-discovery.md`: 당일 작업 완료 기록.

## 검증 결과

- Python AST와 플러그인·마켓플레이스 JSON 파싱 통과.
- Skill Creator 빠른 구조 검사 통과.
- 합성 정치·연금·세금·특혜 후보가 생활비 민감도와 서로 다른 2개 커뮤니티 신호를 받고 일반 발표 후보보다 높은 점수를 받는 것을 확인.
- 커뮤니티 입력의 `body`, `author` 같은 비허용 필드가 보존되지 않고 `title`, `community`, `url`만 남는 것을 확인.
- `discover --help`에서 `--community-signals` 옵션 확인.
- `git diff --check` 통과.
- 설치본 `doctor --json`에서 `ok: true` 확인.
- `news2shorts@news2shorts-local` `0.33.0+codex.20260825140039` installed·enabled 확인.
- 작업본과 설치 캐시의 스크립트, Skill, 발견 정책, README SHA-256 일치 확인.

## 수행하지 않은 작업

- 실제 뉴스·커뮤니티 후보 수집, 외부 로그인·제출·다운로드, 영상 렌더, DB 작업과 프론트엔드 빌드는 수행하지 않았다.
- 현재 실행에서는 `naver_api_hub_configured: false`라 NAVER API 기반 실시간 발견 결과를 생성하지 않았다.
- 커뮤니티 신호는 공개 접근이 가능할 때만 읽기 전용으로 사용하며 접근 제한을 우회하지 않는다.
