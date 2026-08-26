# news2shorts YouTube 업로드 항목 패키지 v3 완료

## 요청

- 첨부한 YouTube Studio 업로드 화면처럼 영상 결과와 함께 입력해야 할 항목을 안내한다.
- 최종 응답에서 항목을 빠뜨리지 않고 바로 복사할 수 있게 한다.

## 완료 내용

- `publish.json`을 버전 3으로 확장했다.
- 기존 제목, 설명, 태그, 출처, 고정 댓글, 썸네일 안내, 재생목록, 시청자층, 카테고리, 합성 콘텐츠, 댓글 설정을 유지했다.
- 썸네일 방식, 영상 언어, 유료 프로모션, 연령 제한, 공개 상태, 예약 공개 시각을 추가했다.
- 새 프로젝트의 공개 상태는 안전한 기본값인 `private`로 설정하며 예약 공개는 시간대가 포함된 ISO 8601 시각을 요구한다.
- 최종 검증에서 구체적인 썸네일 장면·시점 또는 파일 안내와 재생목록 추천·`선택 안 함`을 필수로 확인한다.
- `altered_content`와 `age_restriction`이 `review_required`인 최종 패키지는 통과하지 않는다.
- `upload-package` 명령을 추가해 `publish.json`을 첨부 화면 순서에 가까운 한국어 `YouTube 업로드 정보`로 출력한다.
- 영상 결과를 반환할 때 formatter의 전체 출력을 생략 없이 응답에 포함하도록 Skill 계약을 강화했다.
- 기존 버전 2 프로젝트도 formatter로 읽을 수 있게 유지했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: publish v3 초기값, 최종 검증, `upload-package` formatter와 CLI 추가
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 영상 결과의 업로드 정보 필수 반환 규칙 강화
- `plugins/news2shorts/skills/news2shorts/references/upload-package.md`: YouTube Studio 항목 매핑과 최종 응답 순서 추가
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: publish v3 스키마와 호환성 계약 반영
- `plugins/news2shorts/README.md`: 업로드 항목과 formatter 사용법 추가
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전 `0.13.0+codex.20260818` 및 설명 갱신

## 검증

- 원본 Skill 빠른 검사 통과
- 원본 CLI 도움말과 플러그인 JSON 검사 통과
- 새 프로젝트 초기화 시 publish v3와 신규 기본값 생성 확인
- 기존 버전 2 버스하우스 프로젝트에서 제목·설명 전문, 태그, 썸네일, 재생목록, 시청자층, 카테고리, 합성 콘텐츠, 댓글, 공개 상태, 고정 댓글 출력 확인
- 완성형 v3 임시 프로젝트에서 신규 업로드 설정 검증 통과 후 기존 `editorial_reviewed` 미승인만 남는 것을 확인
- 썸네일 안내를 비운 음수 테스트에서 신규 검증 오류가 발생하는 것을 확인
- 설치본 Skill·CLI·새 reference와 원본의 SHA-256 일치 확인
- 설치본 Skill 빠른 검사와 `upload-package` 실행 성공
- `news2shorts@news2shorts-local`을 `0.13.0+codex.20260818`로 재설치 완료

## 미실행 범위

- 기존 프로젝트의 `publish.json`과 MP4는 변경하지 않았다.
- YouTube 업로드, 예약 공개, 고정 댓글 게시는 수행하지 않았다.
- 프론트엔드 빌드와 DB 작업은 수행하지 않았다.
