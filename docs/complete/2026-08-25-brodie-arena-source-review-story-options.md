# 경기장 빅보스 원본 검토와 스토리 3안 완료

## 완료 일자

- 2026-08-25

## 완료 내용

- 사용자가 선택한 TikTok 원본 `7314339309811797291`을 공식 제작자 URL에서 로컬 검토용으로 획득했다.
- 최신 `yt-dlp 2026.08.19`와 브라우저 호환 요청을 사용했으며 로그인, 사용자 쿠키, 캡차·DRM 우회, 제3자 다운로드 사이트는 사용하지 않았다.
- 원본은 41.074초, 1080×1920, HEVC/AAC이며 SHA-256은 `de7d580f2b7a7b1eae2f33502b85510a5c3ffcce8be72ac5b34e8f348b2ba8bb`다.
- 2초 간격 21장 콘택트시트와 주요 전환 프레임을 직접 확인했다.
- 관찰 근거를 `source-analysis.json`에 등록하고 감정·의도·투표 방식을 추정하지 않도록 제한했다.
- 제목 `경기장 빅보스 / 이구역은 내꺼`를 고정한 서로 다른 스토리 3안을 생성했다.
- 세 안은 `delayed-reveal`, `escalating-wait`, `callback` 구조이며 근거 점수와 재미 점수 모두 검증 기준 75점을 통과했다.
- 우승 표시 장면에만 무보컬 `bass_drum`을 한 번 배치했다.

## 생성 및 변경 파일

- `projects/2026-08-25-brodie-arena-big-boss-v1/assets/source/source.mp4`: 공식 URL에서 받은 로컬 검토용 원본.
- `projects/2026-08-25-brodie-arena-big-boss-v1/assets/preview/`: 콘택트시트와 21장 검토 프레임.
- `projects/2026-08-25-brodie-arena-big-boss-v1/reviewed-observations.input.json`: 사람이 검토한 관찰 입력과 보호 영역.
- `projects/2026-08-25-brodie-arena-big-boss-v1/source-analysis.json`: 검증된 관찰 결과.
- `projects/2026-08-25-brodie-arena-big-boss-v1/story-options.input.json`: 스토리 3안 입력.
- `projects/2026-08-25-brodie-arena-big-boss-v1/story-options.json`: 검증된 구조화 스토리 3안.
- `projects/2026-08-25-brodie-arena-big-boss-v1/story-options.md`: 사람이 읽는 스토리 비교본.
- `projects/2026-08-25-brodie-arena-big-boss-v1/project.json`: `stories_ready` 상태와 산출물 경로 반영.
- `docs/todo/2026-08-25-brodie-arena-big-boss-source-pending.md`: 원본 대기 항목을 해결 상태로 갱신.

## 검증

- 원본 미디어 프로브와 SHA-256 등록을 완료했다.
- 실제 콘택트시트와 핵심 프레임을 직접 확인했다.
- `observe` 검증을 통과해 프로젝트가 `source_reviewed`로 전환됐다.
- `stories` 검증을 통과해 프로젝트가 `stories_ready`로 전환됐다.
- 스토리별 원본 사용 합계는 16.5초, 17.5초, 9.2초로 권리 불명 소스의 로컬 검토 한도 18초 이하다.
- 프론트엔드 빌드와 DB 작업은 수행하지 않았다.

## 남은 작업

- 사용자가 스토리 2번 `story-three-step-boss`를 명시적으로 선택했다.
- 20초 로컬 검토본 `outputs/preview.mp4`를 생성했다.
- 사용자가 검토본의 스토리 적합성과 음악 적합성을 각각 승인해야 한다.
- 권리 상태는 `unknown`이므로 현재 원본과 이후 렌더는 로컬 검토 전용이다.
- 두 항목 승인 이후에만 최종 `outputs/short.mp4`를 렌더한다.
