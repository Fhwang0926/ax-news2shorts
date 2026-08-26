# 2026-08-20 Viral Shorts 승인된 HLS 원본 취득 개선

## 작업 범위

- 사용자가 아이브 장원영 후보 1번을 선택한 기록을 `selection.json`에 보존했다.
- 사용자의 원격 EJS 실행 승인 후에도 기본 YouTube HTTPS 영상 스트림이 HTTP 403을 반환하는 것을 확인했다.
- 공식 yt-dlp PO Token 안내에서 현재 `web_safari` HLS가 GVS PO Token 없이 제공될 수 있음을 확인했다.
- 명시적 원격 EJS 승인이 있고 기본 스트림이 실패한 경우에만 `web_safari` 공개 HLS를 최대 720p로 재시도하도록 `acquire`를 개선했다.
- 해당 대체 경로는 API key, 로그인, 쿠키, PO Token 제공자를 사용하지 않으며, 실제 사용한 영상 전송 방식을 `source.json`에 기록한다.
- 현재 ffmpeg 빌드에 `subtitles/libass`가 없어 최초 렌더가 실패한 환경 차이를 확인했다.
- 추가 패키지 설치 없이 기존 Pillow로 시간 구간별 투명 자막 PNG를 만들고 ffmpeg 기본 `overlay` 필터로 표시하도록 렌더러를 개선했다.

## 검증 결과

- Python AST, Plugin validator, Skill validator, CLI `--help`가 모두 통과했다.
- 승인된 `web_safari` HLS 재시도로 1280x720 H.264/AAC 원본 279,748,753바이트를 취득했다.
- 원본 취득에 API key, 로그인, 쿠키, PO Token 제공자를 사용하지 않았다.
- 선택한 `00:21:43.720~00:22:23.000` 구간을 39.28초 로컬 검토 MP4로 렌더했다.
- 최종 MP4가 720x1280, H.264, AAC, 30fps이며 SHA-256이 `6bd117991caaf47c91eeb57b6ed2d6c6d706d3bba754d624cfcec74a855f84a7`임을 `render-report.json`과 `ffprobe`로 확인했다.
- 대표 4개 프레임 접촉 이미지를 생성해 후킹, 세로형 화면 배치, 한국어 자막, `로컬 검토용` 표시가 보이는지 확인했다.
- 프로젝트 `validate`가 오류 0건으로 통과했고 `rendered_media_verified: true`를 확인했다.
- 프론트엔드 빌드·테스트와 DB 작업은 수행하지 않았다.

## 변경 파일

- `plugins/viral-shorts/scripts/viral_shorts.py`
- `plugins/viral-shorts/skills/viral-shorts/SKILL.md`
- `plugins/viral-shorts/skills/viral-shorts/references/workflow.md`
- `plugins/viral-shorts/skills/viral-shorts/references/output-contract.md`
- `docs/complete/2026-08-20-viral-shorts-approved-hls-acquisition.md`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/selection.json`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/project.json`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/source.json`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/assets/source/source.mp4`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/outputs/review.mp4`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/outputs/review-contact-sheet.png`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/render-report.json`
