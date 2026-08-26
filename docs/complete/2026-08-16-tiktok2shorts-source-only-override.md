# 2026-08-16 tiktok2shorts 대본 오버라이드·원본 장면 전용 리빌드 완료

## 요청 반영

- `script.json.storyboard_override`를 추가해 검토된 장면의 `headline`과 `korean_caption`만 대본 기준으로 덮어쓸 수 있게 했다. 원본 구간, 길이, 편집 동작, 권리 정보는 오버라이드할 수 없다.
- 렌더 전 검증에서 실제 원본 구간이나 출처가 기록된 `visual_path`가 없는 장면을 거부하게 했다.
- 도형, 단계표, 자동 해설 카드 렌더 경로를 제거했다. 첨부된 화면과 같은 의미 없는 정리 카드는 더 이상 생성하지 않는다.
- `delivery-note.md`, `render-report.json`, `project.json`에 대본 오버라이드 반영 여부와 원본 TikTok URL을 기록한다.

## 리빌드 결과

- `outputs/tiktok2shorts/2026-08-16/egg-drop-soup/outputs/short.mp4`
- 17.321초, 720x1280, H.264/AAC, 원본 영상 장면 4개만 사용했다.
- 모든 장면의 `visual_kind`는 `source_video`이고, 원본 사용 시간은 17.3초다. 장면당 8초와 총 18초 제한 안이다.
- 대본 오버라이드가 적용됐고, 전체 시나리오는 영상 밖의 `delivery-note.md`에만 남겼다.
- 원본 링크: `https://www.tiktok.com/@jujumaoo/video/7662349457840688405`

## 검증 경계

- Python 구문 검사, JSON 형식 검사, `validate --final`, 실제 `render --overwrite`를 수행했다.
- `render-report.json`으로 `script_override_applied: true`, 원본 URL, 4개 `source_video`, 17.3초 원본 사용량을 확인했다.
- 추출 프레임으로 자동 도형·정리 카드가 사라지고 실제 조리 장면만 남은 것을 확인했다.
- 외부 업로드, 게시 권한, 수익화 판단, 라이선스의 법적 유효성은 검증하지 않았다.

## 변경 파일

- `plugins/tiktok2shorts/.codex-plugin/plugin.json`
- `plugins/tiktok2shorts/scripts/tiktok2shorts.py`
- `plugins/tiktok2shorts/README.md`
- `plugins/tiktok2shorts/skills/tiktok2shorts/SKILL.md`
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/output-contract.md`
- `outputs/tiktok2shorts/2026-08-16/egg-drop-soup/script.json`
- `outputs/tiktok2shorts/2026-08-16/egg-drop-soup/storyboard.json`
- `outputs/tiktok2shorts/2026-08-16/egg-drop-soup/*`
