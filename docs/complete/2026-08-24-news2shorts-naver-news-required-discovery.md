# news2shorts NAVER News 필수 후보 탐색

## 완료 일자

- 2026-08-24

## 반영 범위

- NAVER API 설정 여부와 관계없이 NAVER News를 현재 뉴스 후보 발굴 범위에 항상 포함한다.
- API가 없으면 `news.naver.com` 또는 `n.news.naver.com` 도메인 검색과 원문 검색을 함께 사용한다.
- Computer Use를 사용할 수 있으면 일반 뉴스 화면이 아니라 NAVER News 랜딩 또는 검색 결과를 읽기 전용으로 최소 한 번 확인한다.
- 다른 작업 탭을 덮어쓰지 않도록 별도 브라우저 탭을 사용한다.
- NAVER에서 발견된 기사도 동일한 최신성·원문·독립 출처 검증을 통과해야 하며 노출 순서만으로 우선하지 않는다.
- 결과에 NAVER News 확인 방식과 최종 후보 반영 수를 표시하고, 확인 실패 시 `NAVER News 미확인`을 명시한다.

## 변경 파일

- `plugins/news2shorts/skills/news2shorts/SKILL.md`: NAVER News 필수 탐색과 확인 상태 보고 규칙 추가.
- `plugins/news2shorts/README.md`: 사용자용 NAVER News 탐색·대체 동작 설명 보강.
- `plugins/news2shorts/.codex-plugin/plugin.json`: 설명과 버전을 `0.30.2+codex.20260824213146`으로 갱신.

## 검증 결과

- Skill Creator 빠른 구조 검사와 플러그인·마켓플레이스 JSON 파싱을 통과했다.
- 설치본 CLI 도움말과 `doctor --json`을 실행했고 환경 검사는 `ok: true`였다.
- `news2shorts@news2shorts-local` `0.30.2+codex.20260824213146`이 installed·enabled 상태임을 확인했다.
- 작업본과 설치 캐시의 Skill, 플러그인 매니페스트, README SHA-256이 각각 일치했다.
- `git diff --check`를 통과했다.

## 수행하지 않은 작업

- 뉴스 후보 생성, 영상 렌더, 외부 로그인·제출·다운로드, DB 작업과 프론트엔드 빌드는 수행하지 않았다.
- 현재 Codex 샌드박스에서는 macOS 키체인 확인이 제한되어 Typecast 키 유무는 판정하지 않았다.
