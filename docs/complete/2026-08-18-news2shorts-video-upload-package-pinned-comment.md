# news2shorts 영상 결과 업로드 패키지 개선 완료

## 요청

- 영상 결과를 전달할 때 YouTube에 입력할 내용을 함께 안내한다.
- 고정 댓글도 빠뜨리지 않고 포함한다.

## 완료 내용

- `publish.json` 버전 2에 `pinned_comment`와 `upload_settings`를 추가했다.
- 새 프로젝트는 썸네일 안내, 재생목록, 시청자층, 카테고리, 합성 콘텐츠 공개 검토 상태, 댓글 허용 여부를 기본 생성한다.
- 최종 패키지는 제목, 설명, 태그, 고정 댓글과 필수 업로드 설정을 검증한다.
- 제목은 100자를 넘지 않도록 검사하고 최종 상태의 합성 콘텐츠 공개 여부가 `review_required`이면 중단한다.
- 모든 검토·최종 영상 결과 응답에서 업로드 내용과 고정 댓글 전문을 직접 표시하도록 Skill 반환 계약을 변경했다.
- 현재 버스하우스 프로젝트에도 실제 복사용 제목·설명·태그·설정·고정 댓글을 채웠다.
- 플러그인 버전을 `0.12.0+codex.20260818`로 갱신하고 Codex 캐시에 설치했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 업로드 패키지 초기값, 행정 식별번호 억제, 버전 2 검증 추가
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 영상 결과와 업로드 내용·고정 댓글 동시 반환 규칙 추가
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: `publish.json` 버전 2 계약 추가
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전과 기능 설명 갱신
- `plugins/news2shorts/README.md`: 업로드 패키지 기능과 반환 동작 설명
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/publish.json`: 현재 영상의 복사용 업로드 패키지
- `docs/todo/2026-08-17-hwang-hee-bus-house-final-review.md`: 현재 프로젝트 검토 상태 갱신

## 검증

- 현재 프로젝트 초안 검증: 오류 0건, 경고 0건.
- 새 프로젝트 초기화 검사에서 `publish.json` 버전 2와 신규 필드 생성을 확인했다.
- 원본 및 설치본 렌더러 SHA-256 일치.
- 원본과 설치된 Skill 빠른 검증 통과.
- 설치본 `doctor` 정상, Typecast 키체인·자동 보이스 후보 확인.

## 미실행 범위

- 기존 영상 파일은 내용 변경이 없어 다시 렌더하지 않았다.
- YouTube 업로드와 고정 댓글 게시는 수행하지 않았다.
- 프론트엔드 빌드, DB 작업은 수행하지 않았다.
