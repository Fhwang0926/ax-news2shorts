# 평택 돈가스 메뉴 사진 수량 차이 검토 영상 제작

## 완료 내용

- JTBC News 쇼츠를 출발점으로 JTBC 기사와 파이낸셜뉴스 보도를 교차 확인했다.
- 시민 관점의 첫 질문 `메뉴 5조각, 실제 2조각이어도 될까요?`를 중심으로 29.488초 세로형 검토 영상을 제작했다.
- Typecast `필재` 음성으로 하나의 연속 내레이션을 만들고, 6개 장면과 별도 썸네일을 구성했다.
- 사건 사진을 무단 전재하지 않고, 생성 비교 이미지는 `설명 이미지 · 사건 사진 아님`으로 표시했다.
- CC BY 2.0 돈가스 자료사진은 사건 음식이 아님을 화면과 설명란에 명시했다.
- CapCut/Vrew용 편집 패키지와 YouTube 제목·설명·태그·고정 댓글 초안을 생성했다.

## 산출물

- 프로젝트: `projects/2026-08-25-pyeongtaek-tonkatsu-menu-gap/`
- 검토 영상: `projects/2026-08-25-pyeongtaek-tonkatsu-menu-gap/preview.mp4`
- 별도 썸네일: `projects/2026-08-25-pyeongtaek-tonkatsu-menu-gap/thumbnail.jpg`
- 편집 패키지: `projects/2026-08-25-pyeongtaek-tonkatsu-menu-gap/edit-package/preview/`
- 검증 보고서: `projects/2026-08-25-pyeongtaek-tonkatsu-menu-gap/render-report.json`

## 검증

- 영상: H.264, 720x1280, 29.488초, 30fps
- 음성: AAC, 48kHz, 스테레오
- 초안 규칙 검증 통과
- 추출 프레임으로 자막 잘림, 화면 겹침, 출처 표시를 육안 확인
- 음성 구간을 확인했으며 종료부에만 약 1.17초 무음이 있다.
- `git diff --check` 통과

## 공개 전 제한

- 실제 사건과 직접 일치하면서 재사용 권리가 확인된 뉴스 사진을 확보하지 못했다.
- 따라서 현재 산출물은 비공개 검토용 `preview.mp4`이며, 공개 가능한 최종 `short.mp4`는 만들지 않았다.
- 편집 검토, 권리 검토, 합성 콘텐츠 공개 검토 승인도 완료 전 상태로 유지했다.
- 보도 원본의 게시 시각은 확인 가능한 근거가 없어 비워 두었다.
- 업체의 환불·사과 약속은 보도로 확인했지만 실제 환불 완료 여부는 미확인으로 표현했다.
- YouTube 업로드는 수행하지 않았다.

## 생성·변경 파일

- 프로젝트 메타데이터와 근거: `project.json`, `sources.json`, `fact-sheet.json`, `rights-manifest.json`
- 구성과 문안: `script.md`, `storyboard.json`, `publish.json`
- 화면 자산: `assets/generated/`, `assets/collected/`
- 렌더 산출물: `preview.mp4`, `thumbnail.jpg`, `render-report.json`, `edit-package/preview/`
- 완료 기록: `docs/complete/2026-08-25-pyeongtaek-tonkatsu-menu-gap-review-video.md`
