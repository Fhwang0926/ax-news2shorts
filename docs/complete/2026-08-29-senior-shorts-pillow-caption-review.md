# 시니어 쇼츠 Pillow 자막 fallback과 첫 검토본 완료

## 원인

- 현재 Homebrew FFmpeg 8.1.2에는 `ass`, `subtitles`, `drawtext` 필터가 없고 `overlay` 필터만 있었다.
- 장면 영상과 음성 합본은 생성됐지만 ASS 자막 burn-in 단계에서 `No such filter: ass`로 중단됐다.

## 수정 내용

- FFmpeg 필터 지원을 실행 시 확인한다.
- `ass`와 `drawtext`가 있으면 기존 ASS 렌더 경로를 유지한다.
- 해당 필터가 없으면 설치된 Pillow와 한글 폰트로 장면별 1080×1920 투명 자막 PNG를 만든다.
- 흰색 본문, 노란색 핵심어, 검정 외곽선, 1~2줄, 중앙 하단, `LOCAL REVIEW` 표시를 유지한다.
- FFmpeg `overlay`로 각 장면 영상에 투명 자막을 합성한 뒤 기존 결합·오디오 경로를 재사용한다.
- `doctor`가 `subtitle_renderer`와 Pillow 버전을 보고하며 실제 자막 렌더러가 없으면 `ready_for_render: false`가 된다.
- `render-report.json`에 `subtitle_renderer`를 기록한다.

## 첫 검토본

- 프로젝트: `projects/2026-08-28-retired-husband-notebook`
- 음성: macOS Yuna, 165 WPM, 장면별 AIFF 8개
- 타임라인: 55.348초
- 검토본: `final/review.mp4`
- 미디어: 1080×1920, 30fps, H.264 High, AAC stereo, 55.366초
- 전체 파일 디코딩 오류 없음
- 0.5초 이상 검은 화면 없음
- 장면 사이 0.8~2.16초의 의도된 내레이션 여백이 있으며 2.2초를 넘는 장시간 무음 없음
- 대표 프레임 접촉시트에서 8개 장면, 큰 2줄 자막, 노란색 핵심어, 검토 표시, 캐릭터 연속성을 확인했다.

## 변경 파일

- `plugins/senior-shorts/scripts/senior_shorts.py`: 자막 렌더러 진단과 Pillow overlay fallback을 추가했다.
- `plugins/senior-shorts/README.md`: 자막 fallback과 doctor 필드를 기록했다.
- `plugins/senior-shorts/skills/senior-shorts/references/output-contract.md`: ASS/Pillow 자막 계약을 추가했다.
- `docs/complete/2026-08-29-senior-shorts-pillow-caption-review.md`: 원인, 수정, 첫 검토본 QA를 기록했다.

## 검증 경계

- `senior-shorts@news2shorts-local`을 `0.1.0+codex.20260829030942`로 재설치했다.
- 현재 검토본은 로컬 재생·디코딩과 정적 프레임 검증 결과다.
- 사람의 전체 시청·음성 자연스러움·스토리 감정선·게시 적합성 승인은 남아 있다.
- 실제 업로드, 플랫폼 승인, 수익화 적합성은 검증하지 않았다.
- 사용자 지침에 따라 단위 테스트, 프론트엔드 빌드, DB 작업은 수행하지 않았다.
