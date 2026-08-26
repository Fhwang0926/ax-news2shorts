# PB-02 자장면 대본 승인 및 검토본 제작

## 작업 일자

- 2026-08-26

## 반영 내용

- 사용자의 승인을 `script` 단계 승인으로 반영했다.
- 프로젝트 상태를 `evidence_reviewed → script_reviewed → draft_rendered` 순서로 전환했다.
- Typecast 키가 설정되지 않은 환경에서는 자동 음성 대체를 금지하는 플러그인 규칙에 따라 `--no-tts` 무음 검토본을 제작했다.
- `visual`과 `publish` 승인은 적용하지 않았으며 실제 업로드도 수행하지 않았다.

## 생성 산출물

- `projects/2026-08-25-pb-02-seoul-jajangmyeon/review.mp4`: 540×960 로컬 검토본.
- `projects/2026-08-25-pb-02-seoul-jajangmyeon/captions.srt`: 장면 타이밍 기준 자막.
- `projects/2026-08-25-pb-02-seoul-jajangmyeon/thumbnail.jpg`: 검토용 썸네일.
- `projects/2026-08-25-pb-02-seoul-jajangmyeon/edit-package/review/`: 장면 프레임·클립·타임라인·참조 영상이 포함된 편집 패키지.
- `projects/2026-08-25-pb-02-seoul-jajangmyeon/render-report.json`: 렌더 모드, 해시, 미디어 속성 기록.

## 검증 결과

- 프로젝트 검증: 오류 0건, 경고 0건.
- 실제 디코딩: 1,248프레임 전체 정상.
- 영상 속성: H.264, 540×960, 30fps, 41.6초.
- 오디오 속성: AAC 48kHz 스테레오 트랙이며 `silencedetect`로 41.6초 전체 무음을 확인했다. 이는 `--no-tts` 검토본의 의도된 결과다.
- `blackdetect`: 검은 화면 구간이 검출되지 않았다.
- 대표 프레임: 2초 이후 고정 노란 헤더, 주제 제목, 가격 조건, 출처·확인 시각, 하단 안전 영역을 확인했다.

## 현재 상태와 다음 단계

- 현재 상태는 `draft_rendered`다.
- 검토본 확인 후 `visual` 승인이 필요하다.
- 게시 준비와 최종본은 별도 `publish` 승인, 최신 가격 확인, 웹 인용 권리 검토 또는 중립 데이터 카드 교체, Typecast 연속 음성이 모두 충족되기 전에는 진행하지 않는다.
- 프론트엔드 빌드와 DB 작업은 수행하지 않았다.
