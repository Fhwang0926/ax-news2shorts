# Percy 비 오는 날 수건 원본 선택

## 작업 일자

- 2026-08-26

## 요청 반영

- 사용자의 `2번으로 변경` 요청에 따라 `percy-rainy-day-towel` 후보를 새 원본으로 선택했다.
- 신규 프로젝트는 `observation-contrast-v1` 화면 프리셋과 `unknown` 권리 상태로 초기화했다.
- 이전 1번 프로젝트는 삭제하거나 덮어쓰지 않고 그대로 보존했다.

## 현재 상태

- 선택한 TikTok 정식 URL 한 개를 `yt-dlp`로 직접 획득했지만 `Unable to extract universal data for rehydration` 오류가 발생했다.
- 로그인, 쿠키, CAPTCHA, DRM 우회, 제3자 다운로드 미러와 워터마크 제거는 사용하지 않았다.
- 후보 조사 때 사용한 임시 검토 영상도 프로젝트와 임시 폴더에 남아 있지 않았다.
- 프로젝트 상태는 `source_pending`이며 읽을 수 있는 원본이 없어 프레임 관찰, 스토리 3안 작성과 렌더링은 진행하지 않았다.

## 변경 파일

- `projects/2026-08-26-percy-rainy-towel-v1/project.json`: 2번 후보 선택과 `source_pending` 상태를 기록했다.
- `projects/2026-08-26-percy-rainy-towel-v1/source.json`: 정식 URL, 제작자, 공개 지표, 행동 요약과 권리 상태를 기록했다.
- `projects/2026-08-26-percy-rainy-towel-v1/rights-manifest.json`: 공개 원본만 확인된 `unknown` 권리 상태를 유지했다.

## 다음 입력

- 제작자에게 받은 파일 또는 TikTok 공식 저장 기능으로 받은 원본 로컬 영상이 필요하다.
- 파일이 제공되면 실제 프레임을 검토한 뒤 서로 다른 재미 구조의 스토리 3안을 작성하고 사용자 선택 단계에서 멈춘다.
