# news2shorts 뉴스픽 후보 탐색 추가

## 완료 일자

- 2026-08-29

## 완료 내용

- URL이나 단일 주제가 없는 뉴스 후보 탐색에 NAVER News와 함께 뉴스픽을 필수 발견 경로로 추가했다.
- 뉴스픽 공개 뉴스 카테고리와 사용 가능한 경우 실시간 키워드 페이지를 읽기 전용으로 확인한다.
- 뉴스픽에서는 현재 검토에 필요한 제목, 표시 언론사, 표시 시간, 뉴스픽 URL, 관찰 시간만 임시로 사용한다.
- 뉴스픽은 뉴스 집계 서비스이므로 사실 근거, 독립 언론사 수, 최근 6시간 확산 점수, 국민 여론, 이미지 사용 권리로 계산하지 않는다.
- 뉴스픽 링크에서 원문을 열 수 없거나 캐시 미스가 발생하면 제목과 언론사로 원문을 다시 찾는다. 원문과 필요한 독립 출처를 확인하지 못하면 후보에서 제외한다.
- 후보 결과에 `NewsPic 확인` 또는 `NewsPic 미확인`과 뉴스픽에서 시작한 최종 후보 수를 별도로 표시하도록 했다.
- 기존 주제 이력 제외, 시민 영향 관문, 최대 3개 후보와 사용자 선택 대기 규칙은 그대로 유지했다.

## 변경 파일

- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/references/discovery-policy.md`
- `plugins/news2shorts/skills/news2shorts/agents/openai.yaml`
- `plugins/news2shorts/.codex-plugin/plugin.json`
- `plugins/news2shorts/README.md`
- `docs/complete/2026-08-29-news2shorts-newspic-discovery.md`

## 설치 및 검증

- 설치 플러그인: `news2shorts@news2shorts-local`
- 설치 버전: `0.36.5+codex.20260829142806`
- 작업본 Skill validator: 통과
- 작업본 Plugin validator: 통과
- 설치본 Skill validator: 통과
- 설치본 Plugin validator: 통과
- 플러그인 JSON 구문 확인: 통과
- 변경 파일 공백 검사: 통과
- 작업본과 설치 캐시의 manifest, README, SKILL, 발견 정책, UI 메타데이터: 일치
- 설치 캐시에서 NewsPic 발견 계약 확인: 완료

## 수행하지 않은 작업

- 뉴스픽 전용 API나 HTML 스크레이퍼는 추가하지 않았다. 공개 웹·브라우저 기본 기능으로 확인하도록 했다.
- Python 렌더러와 `discover` 명령 구현은 변경하지 않았다. `discover`의 자동 API 수집은 기존 NAVER API HUB 범위를 유지한다.
- 실제 후보 재생산, 프로젝트 생성, 이미지 수집, 음성 생성, 영상 렌더, 업로드는 수행하지 않았다.
- 프론트엔드 빌드와 자동화 테스트는 수행하지 않았다.
- DB 조회·초기화·리셋 작업은 수행하지 않았다.
