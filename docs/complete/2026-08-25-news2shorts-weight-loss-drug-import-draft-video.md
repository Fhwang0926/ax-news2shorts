# news2shorts 비만치료제 직구 가격 격차 검토 영상

- 완료일: 2026-08-25
- 프로젝트: `projects/2026-08-25-weight-loss-drug-import-price-gap`
- 범위: Typecast 연속 음성, 검토용 MP4, 별도 썸네일, CapCut/Vrew 호환 편집 패키지, YouTube 업로드 문구

## 완료 내용

- 건강 민감 뉴스 자동 정책으로 Typecast `Seohyeon` 보이스를 적용했다.
- 채널 인트로, 5개 뉴스 장면, 사실 결론, 음성 포함 구독·좋아요 CTA 순서로 검토본을 렌더링했다.
- Typecast 실측 결과에 따라 장면 4와 결론 대사를 압축했다.
- 최종 검토본 길이는 23.344초이며 모든 일반 장면은 4.5초 이하, 결론은 5.684초다.
- `thumbnail.jpg`와 `edit-package/preview`의 참조 영상, 오버레이 없는 편집 영상, SRT, WAV, 장면별 MP4, 타임라인을 생성했다.
- 링크와 제작 방식 문구가 없는 YouTube 제목, 설명, 태그, 고정 댓글, 공개 설정을 `publish.json`에 작성했다.

## 검증

- 프로젝트 일반 검증: 오류 0건
- 남은 경고: 게시일이 없는 관세청 상시 안내 페이지 1건
- 영상: H.264 720×1280, AAC 48kHz 스테레오, 23.344초
- 전체 MP4 디코딩: 오류 없음
- 대표 프레임과 별도 썸네일을 확인해 글자 겹침, 잘림, 깨짐이 없음을 확인했다.

## 승인 경계

- 권리 검토와 합성 콘텐츠 공개 검토는 완료 상태다.
- 건강 민감 주제의 편집 검토가 남아 있어 `editorial_reviewed`는 `false`로 유지했다.
- 따라서 이번 결과는 `preview.mp4` 검토본이며 `short.mp4` 최종 렌더와 업로드는 수행하지 않았다.

## 변경 파일

- `project.json`: 검토 상태, Typecast 자동 선택 결과, 렌더 상태를 기록했다.
- `script.md`: 실측 길이에 맞게 근거와 결론 대사를 압축했다.
- `storyboard.json`: 압축한 연속 내레이션을 반영했다.
- `publish.json`: 업로드용 제목, 설명, 태그, 썸네일 설정, 고정 댓글을 작성했다.
- `render-report.json`, `preview.mp4`, `thumbnail.jpg`, `audio/`, `edit-package/preview/`: 검토 렌더 결과물이다.
