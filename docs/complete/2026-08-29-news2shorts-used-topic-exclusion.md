# news2shorts 기존 제작 주제 후보 제외

## 완료 일자

- 2026-08-29

## 완료 내용

- 현재 작업 폴더의 `projects/**/project.json`과 각 프로젝트의 `sources.json`을 후보 탐색 전에 읽도록 했다.
- 초안, 수정 대기, 검토 렌더, 완료 상태를 모두 이미 다룬 뉴스로 분류한다.
- 다음 기준 중 하나에 해당하면 후보 목록에서 제외한다.
  - 기존 프로젝트와 동일한 원문 또는 교차검증 기사 URL
  - 기존 제목·주제·훅·이슈 초점·시민 영향·결론·교차검증 기사 제목과 같은 뉴스 군집
- 언론사나 제목만 바뀐 동일 사건과 일반적인 후속 기사도 다시 추천하지 않는다.
- 제외 결과는 `excluded_used_topics`에 기존 프로젝트 경로, 상태, 제목, 주제와 일치 이유를 남긴다.
- NAVER API가 없어서 웹 검색과 브라우저로 수동 조사할 때도 같은 이력 제외 규칙을 적용하도록 스킬과 발견 정책에 명시했다.
- `discover --project-history-root`로 프로젝트 이력이 다른 위치에 있을 때만 경로를 바꿀 수 있게 했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/references/discovery-policy.md`
- `plugins/news2shorts/README.md`
- `plugins/news2shorts/.codex-plugin/plugin.json`
- `docs/complete/2026-08-29-news2shorts-used-topic-exclusion.md`

## 확인된 기존 중복 사례

- `projects/2026-08-28-parking-blocking-fine`: 길막 주차 과태료·견인
- `projects/2026-08-24-jeju-police-false-closures-followup`: 제주 실종신고 허위 종결 후속

두 주제는 앞으로 일반 후보 탐색에서 기본 제외된다.

## 설치 및 구조 확인

- 설치 플러그인: `news2shorts@news2shorts-local`
- 설치 버전: `0.36.5+codex.20260829030605`
- Plugin validator: 통과
- Skill validator: 통과
- Python 구문 확인: 통과
- 플러그인 JSON 확인: 통과
- 작업본과 설치 캐시의 `news2shorts.py`, `SKILL.md`, `discovery-policy.md` SHA-256: 일치
- 변경 파일 공백 검사: 통과

## 수행하지 않은 작업

- 프론트엔드 빌드와 자동화 테스트는 수행하지 않았다.
- DB 조회·초기화·초기화성 명령은 수행하지 않았다.
- 실제 뉴스 재검색, 프로젝트 생성, 이미지 수집, 음성 생성, 영상 렌더와 업로드는 수행하지 않았다.
