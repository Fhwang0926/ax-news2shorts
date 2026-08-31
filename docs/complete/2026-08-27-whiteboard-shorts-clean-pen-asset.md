# 2026-08-27 Whiteboard Shorts 무문자 펜 자산 교체 완료

## 작업 범위

- 상류 렌더러의 손·펜 오버레이에서 마커 몸통의 외국어 문자를 제거했다.
- 손, 펜촉 위치, 마커 방향, 투명 배경과 원본 `1069x1472` 크기를 유지했다.
- 플러그인 버전을 `0.6.1+codex.20260827`로 올렸다.
- `doctor`가 승인된 무문자 자산의 SHA-256을 검사하고 다른 자산이면 `ready_for_render=false`로 표시하도록 했다.
- 스킬에 검토 영상의 움직이는 프레임에서 펜 문자·로고가 없는지 확인하는 절차를 추가했다.

## 자산 정보

- 경로: `plugins/whiteboard-shorts/vendor/srt-whiteboard-animation/assets/drawing-hand.png`
- 크기: `1069x1472`
- 형식: 투명 알파 채널 PNG
- SHA-256: `6c4430a477fd90eed25469c7228f8716913ee3f9b9031326fa3d0f43db50ebb2`
- 제작 방식: 내장 이미지 편집으로 무문자 마커를 만든 뒤 원본 투명 실루엣을 보존해 필요한 문자 영역만 교체

## 확인 범위

- Plugin manifest와 Skill frontmatter 정적 검증
- Python 구문 및 `doctor`의 무문자 자산 해시 확인
- 설치본과 소스 자산의 SHA-256 일치 확인
- 기존 승인 장면의 `540x960`, 15 FPS 로컬 검토 영상 재생성 및 프레임 확인

## 재생성 결과

- 현재 검토본: `projects/2026-08-27-dobby-parrot-whiteboard-v1/previews/scene-01.mp4`
- 교체 전 보존본: `projects/2026-08-27-dobby-parrot-whiteboard-v1/previews/scene-01-before-clean-pen.mp4`
- 영상: H.264, `540x960`, 15 FPS, 3초, 전체 45프레임 디코딩 성공
- 현재 검토본 SHA-256: `1f8c39612f2dd3f133f5cd631142cf02810a0d07907b09406b863b8d0884925d`
- 초반·중간·후반 프레임에서 마커 몸통에 문자·로고가 없는 것을 확인했다.

## 전체 로컬 초안

- 사용자 승인 후 5개 장면을 새 무문자 펜 자산으로 전체 렌더했다.
- 출력: `projects/2026-08-27-dobby-parrot-whiteboard-v1/outputs/preview.mp4`
- 영상: H.264 `1080x1920`, 30 FPS, AAC 48 kHz 스테레오, 16.8초
- 영상 SHA-256: `20e70110c0f3e782405867a58add027d0a89dadccbe0b5953c49d2d518f7f12c`
- 음량: -14.1 LUFS, true peak -1.5 dBFS
- 전체 504프레임 디코딩 성공, 5개 장면과 마지막 1.8초 무음 CTA 프레임 확인
- `render-report.json`, `delivery-note.md`, `youtube-upload.json`, `youtube-upload.md`를 생성했다.
- 프로젝트 상태는 `draft_rendered`이며 `draft_reviewed=false`, `rights_reviewed=false`를 유지한다.
- 원본과 장면 이미지 권리가 `unknown`이므로 영상 상단에 로컬 검토 경고를 유지했고 실제 업로드는 수행하지 않았다.

## 변경 파일

- `plugins/whiteboard-shorts/.codex-plugin/plugin.json`
- `plugins/whiteboard-shorts/README.md`
- `plugins/whiteboard-shorts/scripts/whiteboard_shorts.py`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/SKILL.md`
- `plugins/whiteboard-shorts/THIRD_PARTY_NOTICES.md`
- `plugins/whiteboard-shorts/UPSTREAM.md`
- `plugins/whiteboard-shorts/vendor/srt-whiteboard-animation/assets/drawing-hand.png`
- `docs/complete/2026-08-27-whiteboard-shorts-clean-pen-asset.md`

## 경계

- 이번 변경은 손·펜 오버레이와 해당 검증에만 한정했다.
- TikTok 원본과 장면 이미지의 권리 상태는 변경하지 않는다.
- 재생성 영상은 로컬 검토본이며 게시·수익화 권한이나 플랫폼 승인을 의미하지 않는다.
