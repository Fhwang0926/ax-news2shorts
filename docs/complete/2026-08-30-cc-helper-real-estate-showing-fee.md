# 집 보기 20만 원 임장비 논란 cc-helper CapCut 초안 완료

## 완료 내용

- 클리앙 원문, 뉴시스 보도 2건, KBS 보도, 2026년 8월 28일 시행 공인중개사법·시행규칙을 교차 확인했다.
- 바이럴 각도는 `20만 원 제도 시행`이 아니라 `커뮤니티 개인 제안과 실제 업계 검토안의 차이`로 정리했다.
- 서사 기점은 `2025년 공인중개사협회의 현장 안내 보수제 검토`로 바로잡고, `2026년 클리앙 글`은 발단이 아닌 후속 커뮤니티 찬반 반응 자료로 재배치했다.
- 10개 대화형 내레이션 비트와 정확히 15개 장면을 작성했다.
- 클리앙 원문·찬반 댓글·보도·법령 화면을 원문 픽셀만 사용한 1000×720 가독성 카드로 구성했다.
- 최종 선택 화면에서 기사 사진 속 incidental people을 모두 제거했다.
- 360×640 미리보기에서 각 근거 화면의 앵커 문구를 확인하고 에셋 검수 기록을 남겼다.
- YouTube 제목·설명·해시태그·검색 태그·고정 댓글·썸네일 문구를 복사용 초안으로 준비했다.
- CapCut 초안을 복제하고, 플레이어 검수 중 발견한 긴 자막 4개를 짧게 보정했다.
- 오디오 없는 프로젝트에서 `retime-capcut`을 사용할 수 없어 기존 복제본을 덮어쓰지 않고 별도 버전으로 보정했다.
- 최종 v5 초안의 10개 비트 중간 화면을 실제 CapCut 플레이어에서 확인하고 `final-visual-qc.json`에 해시로 묶었다.

## 프로젝트

- 프로젝트: `projects/cc-helper/2026-08-30/CCH-20260830-01-real-estate-showing-fee`
- 상단 제목: `집만 봐도 20만 원?` / `진짜 시작된 걸까`
- 전체 길이: 45초
- 상태: `local_review_only`
- 게시 차단: `publish_blocked: true`
- BGM: 없음
- 네이티브 오디오 트랙 추가: 없음

## CapCut 최종본

- 원본 템플릿: `/Users/hdh/Movies/CapCut/User Data/Projects/com.lveditor.draft/news2shorts`
- 원본 트리 SHA-256: `c53ff6120947d3c4c62dec4b755aa196165c89601ee441d61265f059ac3e3604`
- 최종 목적지: `/Users/hdh/Movies/CapCut/User Data/Projects/com.lveditor.draft/cc-20260830-120742-real-estate-showing-fee-debate-v5`
- CapCut 표시명: `cc-20260830-120742-real-estate-showing-fee-debate-v5`
- 초안 ID: `190D5C21-E1E3-471D-B7C4-FF7EB18FDBEE`
- 장면: 15개
- 자막: 14개
- 전체 길이: 45초
- 최초 복제본과 v2·v3·v4는 복구용으로 보존
- 공용 `root_meta_info.json`: clone 전후 해시 불변 확인

## 검증

- `validate --stage research`: 통과, 경고 없음
- `validate --stage assets`: 통과
- `prepare-capcut --dry-run`: 완료
- `clone-capcut --confirm`: 최종 v5 복제 완료
- `validate --stage capcut`: 통과
- 프론트엔드 빌드·테스트: 대상 작업이 아니며 실행하지 않음
- 실제 CapCut 플레이어 검수: 10개 narration beat 모두 승인

## 남은 경고와 경계

- scene-04, scene-09, scene-12, scene-15 자막은 4초로 권장 3.2초보다 길다.
- 모든 외부 자료의 `rights_status`는 `unreviewed`다.
- 가독성·내용 검수는 게시 권리 승인이 아니며 공개 게시 전 별도 권리 검토가 필요하다.
- Typecast 음성, 최종 렌더, 업로드, 게시, 일정 예약은 수행하지 않았다.
- `draft_info.json.bak`은 복구본이므로 현재 미러와 달라도 유지한다.

## 변경 파일

- `projects/cc-helper/2026-08-30/CCH-20260830-01-real-estate-showing-fee/research.json`: 출처·후보·팩트 정리
- `projects/cc-helper/2026-08-30/CCH-20260830-01-real-estate-showing-fee/storyboard.json`: 10비트·15장면·자막·SFX·에셋 연결
- `projects/cc-helper/2026-08-30/CCH-20260830-01-real-estate-showing-fee/project.json`: 복사용 YouTube 문구와 게시 차단 상태
- `projects/cc-helper/2026-08-30/CCH-20260830-01-real-estate-showing-fee/asset-manifest.json`: 출처·해시·정규화·가독성 검수 기록
- `projects/cc-helper/2026-08-30/CCH-20260830-01-real-estate-showing-fee/assets/`: 원본 캡처, 가독성 카드, 9:16 정규화본, 미리보기, SFX
- `projects/cc-helper/2026-08-30/CCH-20260830-01-real-estate-showing-fee/handoff/`: 내레이션·SRT·SFX 큐·YouTube 문구·편집 안내·플레이어 검수 캡처
- `projects/cc-helper/2026-08-30/CCH-20260830-01-real-estate-showing-fee/handoff/final-visual-qc.json`: v5 타임라인·storyboard·capcut-map·10개 비트 캡처 해시 승인
- `projects/cc-helper/2026-08-30/CCH-20260830-01-real-estate-showing-fee/capcut-map.json`: 최종 v5 장면·제목·자막 매핑
- `docs/complete/2026-08-30-cc-helper-real-estate-showing-fee.md`: 당일 작업 완료 기록
