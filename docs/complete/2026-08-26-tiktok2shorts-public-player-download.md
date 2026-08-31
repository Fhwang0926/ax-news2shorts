# 2026-08-26 tiktok2shorts 공식 공개 플레이어 다운로드 폴백 완료

## 완료 내용

- `tiktok2shorts download`가 기존 `yt-dlp`를 먼저 사용하고, TikTok 페이지 추출이 실패하면 공식 `player/v1` 공개 플레이어 폴백을 자동 사용하도록 연결했다.
- 폴백은 설치된 Chrome 계열 브라우저를 임시 격리 프로필로 실행하고 로컬 DevTools 포트에서 실제 `video` 또는 `source` 요소의 주소만 읽는다.
- TikTok 소유 HTTPS 호스트만 허용하고, 사용자 브라우저 프로필·로그인·쿠키를 재사용하지 않는다.
- 미러 사이트, CAPTCHA·DRM 우회, 워터마크 제거, 기존 파일 덮어쓰기를 지원하지 않는다.
- 최대 파일 크기, HTTPS 인증서, 리다이렉트 호스트, MP4 헤더를 확인한 뒤 파일을 확정하고 다운로드 방식·원본 URL·제작자·파일 해시·권리 상태를 프로젝트에 기록한다.
- 플러그인 버전을 `0.4.1+codex.20260826235109`로 올리고 스킬·권리 정책·출력 계약·사용 문서를 같은 흐름으로 갱신했다.

## 검증

- 공개 플레이어 폴백 직접 검증: H.264/AAC, 576x1024, 7.366초, 809,300바이트 MP4 저장 성공.
- 선택 프로젝트 원본 검증: HEVC/AAC, 1080x1920, 7.337초, 1,197,321바이트 MP4.
- 선택 프로젝트에서 1초 간격 검토 프레임 7장을 생성하고 첫·마지막 프레임에 같은 앵무새와 접근 동작이 이어지는 것을 확인했다.
- Python 단위 테스트 5개 통과.
- `doctor`, 스킬 `quick_validate`, 플러그인 JSON 검사, `git diff --check` 통과.

## 권리 경계

- 공개 영상 다운로드 성공은 로컬 파일 확보만 증명하며 재사용·게시·수익화 허가가 아니다.
- 선택한 Dobby 원본의 권리 상태는 `unknown`으로 유지하며 허가 증빙 전까지 로컬 검토용으로만 사용한다.

## 변경 파일

- `plugins/tiktok2shorts/scripts/tiktok_public_download.py`
- `plugins/tiktok2shorts/scripts/tiktok2shorts.py`
- `plugins/tiktok2shorts/tests/test_tiktok_public_download.py`
- `plugins/tiktok2shorts/.codex-plugin/plugin.json`
- `plugins/tiktok2shorts/README.md`
- `plugins/tiktok2shorts/skills/tiktok2shorts/SKILL.md`
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/editorial-and-rights.md`
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/output-contract.md`
- `docs/complete/2026-08-26-tiktok2shorts-public-player-download.md`
