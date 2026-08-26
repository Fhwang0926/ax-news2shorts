# 황희 버스하우스 quick-reveal 최종 검토 대기

## 완료 내용

- 조선비즈 원문과 연합뉴스·뉴스1·미디어오늘 보도를 교차 확인했다.
- 삭제된 페이스북 원문은 직접 확인하지 못한 한계와 레딧 댓글의 대표성 한계를 팩트시트에 기록했다.
- 정치 소재에 맞춰 확정 정책과 개인 제안을 구분하는 5장면 quick-reveal 대본과 스토리보드를 작성했다.
- 대한민국 국회 공공누리 제1유형 자료사진 1장과 설명용 생성 이미지 4장을 준비하고 권리·합성 표시·육안 품질 검토를 기록했다.
- 자동 보이스 선택이 민감 뉴스용 `Seohyeon`을 선택했으며 Typecast `ssfm-v30`으로 리뷰 영상을 생성했다.
- 기존 리뷰 영상은 보존하고, 결론을 `확인된 결론 → 보도된 비판 → 청년 주거 대책으로, 이게 맞나요?` 순서의 새 편집형 카드로 갱신했다.
- 새 `preview-v2.mp4`는 서현 보이스를 사용한 720x1280 H.264/AAC, 25.150초 검토본이며 렌더 보고서의 경고는 0건이다.
- `preview-v4.mp4`에서 결론 배지와 상단 장식을 제거하고, 질문을 `청년 주거 대책으로, 이게 맞나?`로 강조했으며 인물 사진을 얼굴 중심으로 `1.14배` 줌인했다.
- `preview-v5.mp4`에서는 결론 카드 배경을 완전 불투명하게 바꿔 원본 일러스트의 두 패널이 카드 내부에 비치지 않게 했다. 바깥 단일 카드 테두리만 유지했다.
- `preview-v5.mp4`는 720x1280 H.264/AAC, 25.214초, Typecast 서현 보이스이며 렌더 경고는 0건이다.
- `publish.json`을 버전 2 업로드 패키지로 갱신해 제목, 전체 설명, 검색 태그, 썸네일·재생목록 안내, 시청자층·카테고리·합성 콘텐츠·댓글 설정과 고정 댓글을 준비했다.

## 변경 파일

- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/project.json`: 주제, quick-reveal 집중 유지 설계, 자동 보이스 결과, 검토 상태 기록
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/sources.json`: 원문·독립 보도·공식 자료 출처 기록
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/fact-sheet.json`: 확인된 사실, 보도 귀속 주장, 미확인 범위 기록
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/script.md`: 후크 후보 3개와 선택 점수, 최종 내레이션 기록
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/storyboard.json`: 5장면 구성, 출처, 모션, 편집형 결론 카드 기록
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/rights-manifest.json`: 실사진 라이선스와 생성 이미지 검색·품질·합성 상태 기록
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/publish.json`: 게시용 제목·설명·출처·합성 미디어 표시 준비
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/preview.mp4`: 기존 사용자 편집 검토용 영상
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/preview-v2.mp4`: 반응과 맥락형 질문을 반영한 새 사용자 편집 검토용 영상
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/preview-v4.mp4`: 배지 없는 결론 카드, 강한 질문 어조, 인물 줌을 반영한 최신 사용자 편집 검토용 영상
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/preview-v5.mp4`: 배경 패널 비침을 제거한 최신 사용자 편집 검토용 영상
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/render-report.json`: preview-v5 렌더 사양과 자동 보이스 선택 결과
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/publish.json`: YouTube 복사용 업로드 내용과 고정 댓글 패키지

## 남은 작업

- 정치 소재 필수 편집 검토에서 사용자가 리뷰본을 승인하면 `editorial_reviewed`를 완료 처리한다.
- 최종 검증을 통과한 뒤 `short.mp4`를 렌더하고 완료 문서를 `docs/complete`에 기록한다.

## 미실행 범위

- 사용자 검토 전이라 최종 `short.mp4`는 생성하지 않았다.
- 업로드·게시, 프론트엔드 빌드, DB 작업은 수행하지 않았다.
