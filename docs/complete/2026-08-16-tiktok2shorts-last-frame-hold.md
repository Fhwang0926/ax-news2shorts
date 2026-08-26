# TikTok2Shorts 마지막 검은 화면 제거

## 완료 내용

- 플러그인 버전을 `0.3.8+codex.20260816`으로 올리고 설치·활성화 상태를 갱신했다.
- 최종 `conclusion` 장면에서 실제 마지막 유효 프레임을 고정하는 `hold_last_frame` 편집 액션을 추가했다.
- `hold_last_frame_seconds`를 0.2~2초 범위로 검증한다.
- 원본 끝에 검은 프레임이 포함된 경우 `hold_last_frame_source_offset_seconds`로 끝에서 0~1초 앞선 검토 프레임을 선택할 수 있게 했다.
- `hold_last_frame`은 마지막 `conclusion` 원본 장면에만 허용하고, 장면 길이가 `source_clip_seconds - source offset + hold seconds`와 일치하는지 검증한다.
- 최종 합성 전에 영상·오디오 길이를 정렬하고, 영상이 오디오보다 한 프레임 이상 먼저 끝나면 렌더를 실패시키도록 했다.
- 배경음 합성의 `-shortest` 스트림 복사로 마지막 영상 패킷이 잘리던 문제를 제거했다.

## 원인과 해결

- 기존 v3 MP4의 마지막 1초 대부분에는 정상 장면이 있었지만, 원본 파생 영상 끝 약 0.2초에 검은 프레임이 포함돼 있었다.
- 초기 고정 시도는 그 검은 프레임을 복제해 중앙 원본 영역이 검게 남았다.
- 원본 끝에서 0.25초 앞선 마지막 유효 장면을 선택해 0.8초 고정했다.
- 최종 합성 후에는 영상 스트림이 오디오보다 약 0.15초 먼저 끝나는 현상도 확인했다.
- 최종 프레임을 영상 길이까지 채우고 영상·오디오 종료 시점을 한 프레임 이내로 정렬했다.

## 샘플 결과물

- 새 프로젝트: `outputs/tiktok2shorts/2026-08-16/나비넥타이를-하고도-아무도-인사해-주지-않는-지하철-강아지-v4-마지막프레임-고정`
- 기존 v3 프로젝트와 MP4는 수정하지 않고 보존했다.
- 마지막 원본 구간: 3.0초
- 마지막 소스 오프셋: 0.25초
- 마지막 유효 프레임 고정: 0.8초
- 마지막 장면 길이: 3.55초
- 권리 상태는 `unknown`, 결과물은 `local_only`이며 업로드 기능은 없다.

## 변경 파일

- `plugins/tiktok2shorts/scripts/tiktok2shorts.py`
  - 마지막 유효 프레임 선택·고정, 장면 설정 검증, 영상·오디오 길이 정렬, 스트림 종료 시점 검증을 추가했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/SKILL.md`
  - 마지막 결론 장면의 프레임 고정 작업 규칙을 추가했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/output-contract.md`
  - `hold_last_frame`과 소스 오프셋 데이터 계약을 추가했다.
- `plugins/tiktok2shorts/README.md`
  - 사용 예시와 장면 길이 계산 방식을 추가했다.
- `plugins/tiktok2shorts/.codex-plugin/plugin.json`
  - 버전과 기능 설명을 갱신했다.
- 샘플 v4 프로젝트의 `project.json`, `storyboard.json`, `publish.json`
  - 버전 계보, 마지막 프레임 설정, 편집 고지를 기록했다.

## 검증

- Python 구문 검사 통과.
- 원본 및 설치 캐시의 skill `quick_validate.py` 통과.
- 원본 및 설치 캐시 렌더러의 `validate --final` 통과.
- 설치 버전: `0.3.8+codex.20260816`.
- 원본·설치 캐시 렌더러 SHA-256 일치:
  - `859d14af8554f2d8ca20acb6a0dbc5a788d401c31b0933facc84eac0ec214887`
- 결과 MP4:
  - 길이 `15.566667초`
  - `720x1280`, `30fps`
  - H.264 영상 `15.566667초`, AAC 오디오 `15.562초`
  - 영상이 오디오보다 약 `0.0047초` 길어 재생 종료 시 검은 공백이 생기지 않는다.
  - 파일 크기 `3,324,349 bytes`
  - SHA-256 `5288185d90814c702fe508f84279badc2022d041bbe204139d2606a5414245cc`
  - 평균 음량 `-28.2 dB`, 최대 음량 `-11.0 dB`
- 마지막 1.05초의 중앙 원본 영역에 FFmpeg `blackdetect` 결과가 없었다.
- `end-check-after.jpg`를 확인해 마지막 유효 강아지 장면이 검은 화면 없이 유지됨을 검토했다.

## 제한

- 기술 검증과 로컬 렌더 완료는 원본 영상의 게시·재사용 허가, 공정 이용, 수익화 가능성을 의미하지 않는다.
