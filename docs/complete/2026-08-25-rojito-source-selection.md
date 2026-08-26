# Rojito 아침 점프 원본 선택

## 작업 일자

- 2026-08-25

## 요청 반영

- 아기 동물 후보 1번 `rojito-morning-bed-jumps`를 사용자 선택 원본으로 기록했다.
- 신규 프로젝트는 `observation-contrast-v1` 화면 프리셋과 `unknown` 권리 상태로 초기화했다.
- 선택한 TikTok 정식 URL 한 개만 직접 획득했으며 로그인, 쿠키, 미러, 워터마크 제거는 사용하지 않았다.

## 현재 상태

- TikTok 페이지 연결은 됐지만 `yt-dlp`가 원본 페이지의 재생 데이터를 추출하지 못했다.
- `컴퓨터` 플러그인으로 로그인 정보가 없는 Chrome 시크릿 창에서 정식 게시물, TikTok 공식 플레이어, TikTok 공식 임베드를 확인했지만 모두 영상 영역이 비어 있어 브라우저 저장도 불가능했다.
- 검토에 사용한 임시 시크릿 창은 닫고 기존 Chrome 화면으로 복귀했다.
- 플러그인 규칙에 따라 프로젝트 상태를 `source_pending`으로 전환했다.
- 읽을 수 있는 원본 영상이 없어 프레임 관찰, 보호 영역 기록, 스토리 3안 작성과 렌더링은 수행하지 않았다.

## 변경 파일

- `projects/2026-08-25-rojito-morning-jumps-v1/project.json`: 1번 후보 선택과 `source_pending` 상태를 기록했다.
- `projects/2026-08-25-rojito-morning-jumps-v1/source.json`: 정식 URL, 제작자, 공개 지표, 행동 요약과 권리 상태를 기록했다.
- `projects/2026-08-25-rojito-morning-jumps-v1/rights-manifest.json`: 공개 원본만 확인된 `unknown` 권리 상태를 유지했다.

## 다음 입력

- 제작자에게 받은 파일이나 사용 권한을 확인할 수 있는 원본 로컬 영상이 필요하다.
- 파일이 제공되면 실제 프레임을 검토한 뒤 서로 다른 재미 구조의 스토리 3안을 작성하고 사용자 선택 단계에서 멈춘다.
