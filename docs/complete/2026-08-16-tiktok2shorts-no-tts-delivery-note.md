# 2026-08-16 tiktok2shorts TTS 제거와 전달 문서 분리 작업 완료

## 변경 내용

- `render`에서 macOS TTS, `--voice`, `--rate`, `--no-tts`, 외부 `narration_audio` 입력을 제거했다.
- 영상 길이는 스토리보드의 요청 길이만 사용한다. `source_audio_duck` 장면은 원본 오디오를 낮춰 사용할 수 있고, 나머지 장면은 AAC 무음 트랙을 사용한다.
- 전체 시나리오는 영상에 읽거나 자막 전문으로 넣지 않는다. `script.json`의 시나리오는 최종 렌더에서 `delivery-note.md`로 별도 전달한다.
- 화면에는 `korean_caption`의 짧은 문구만 배치한다. `korean_caption`이 없을 때 시나리오 문구를 대신 표시하던 동작도 제거했다.
- `delivery-note.md`에는 로컬 MP4 경로, 제작자, 원본 TikTok 링크, 영상에 넣지 않은 전체 시나리오, 화면에 남긴 문구를 기록한다.
- `render-report.json`과 `project.json`에도 원본 URL, 전달 문서 경로, `scenario_in_video: false`를 기록한다.

## 현재 결과물

- `outputs/tiktok2shorts/2026-08-16/egg-drop-soup/outputs/short.mp4`
- `outputs/tiktok2shorts/2026-08-16/egg-drop-soup/delivery-note.md`
- 원본: `https://www.tiktok.com/@jujumaoo/video/7662349457840688405`
- 결과 MP4는 26.021초, H.264/AAC, 720x1280이다. TTS는 포함하지 않았고 원본 자료 화면은 총 17.3초만 사용했다.

## 검증 경계

- Python 구문 검사, `render --help`에서 TTS 관련 옵션 제거, `validate --final`을 확인했다.
- 실제 렌더 후 `render-report.json`에서 `audio_mode: source_audio_ducked_or_silent`, `scenario_in_video: false`, 원본 URL, `delivery_note`를 확인했다.
- `ffprobe`로 H.264, AAC, 720x1280, 영상·음성 스트림, 26.021초를 확인했고 추출 프레임으로 화면 문구만 노출되는 구성을 검토했다.
- 외부 업로드, 게시 권한, 수익화 판단, 라이선스의 법적 유효성은 검증하지 않았다.

## 변경 파일

- `plugins/tiktok2shorts/.codex-plugin/plugin.json`
- `plugins/tiktok2shorts/scripts/tiktok2shorts.py`
- `plugins/tiktok2shorts/README.md`
- `plugins/tiktok2shorts/skills/tiktok2shorts/SKILL.md`
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/output-contract.md`
- `outputs/tiktok2shorts/2026-08-16/egg-drop-soup/*`
