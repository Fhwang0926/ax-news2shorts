# news2shorts 링크 없는 설명·글자 수 검증 완료

## 요청

- 최종 영상 결과와 함께 제공하는 YouTube 설명을 입력 한도에 맞춘다.
- 업로드 화면에서 링크를 넣지 못하는 상황을 고려해 복사용 설명에서 링크를 제거한다.

## 완료 내용

- YouTube Studio 기준 제목 100자, 설명 5,000자 제한을 상수와 검증 규칙으로 추가했다.
- 새 프로젝트의 `publish.json`을 버전 4로 올렸다.
- 버전 4 설명과 `source_lines`에는 URL, 마크다운 링크, `www` 주소, 일반 도메인을 넣지 못하게 했다.
- 원문 URL은 사실 검증용 `sources.json`에만 보존하고, 업로드 설명은 `매체명 — 기사명` 형식으로 작성하도록 계약을 변경했다.
- `upload-package` 출력에 제목과 설명의 정확한 `현재/최대` 글자 수를 표시한다.
- 기존 버전 1~3 프로젝트는 계속 읽되, 최종 복사용 출력에서 기존 링크만 자동 제거한다.
- 설명의 나머지 문장, 출처명, 해시태그는 유지한다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 제목·설명 제한, 링크 탐지·제거, publish v4 검증 및 글자 수 출력
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 영상 최종 결과의 링크 없는 설명과 글자 수 표시 규칙
- `plugins/news2shorts/skills/news2shorts/references/upload-package.md`: 복사용 업로드 설명 계약
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: publish v4 스키마와 하위 버전 호환 규칙
- `plugins/news2shorts/README.md`: 최종 전달 방식과 formatter 사용법
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전 `0.15.0+codex.20260818`과 기능 설명

## 검증

- 원본 및 설치본 Skill 빠른 검사 통과
- CLI 도움말과 플러그인 JSON 검사 통과
- 새 프로젝트 초기화 시 publish v4 생성 확인
- 버전 4 임시 프로젝트에서 설명·출처 URL 경고 확인
- 같은 프로젝트에서 링크 제거 후 신규 경고가 사라지는 것을 확인
- 제목 100자, 설명 5,000자 상수와 링크 탐지·제거 단위 검사 통과
- 기존 버전 3 프로젝트 formatter에서 링크가 제거되고 설명이 `483/5000자 · 링크 없음`으로 출력되는 것을 확인
- 원본과 설치본 Skill·CLI의 SHA-256 일치 확인
- `news2shorts@news2shorts-local`을 `0.15.0+codex.20260818`로 재설치 완료

## 미실행 범위

- 기존 프로젝트 파일과 MP4는 변경하지 않았다.
- YouTube 업로드·예약·게시·댓글 등록은 수행하지 않았다.
- 프론트엔드 빌드와 DB 작업은 수행하지 않았다.
