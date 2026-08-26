# TikTok2Shorts 동물 감정 해설형 피벗 완료

- 작업일: 2026-08-16
- 플러그인: `plugins/tiktok2shorts`
- 템플릿: `animal-emotion-story-v1`

## 반영 내용

- TikTok 후보 선별을 동물 전용으로 제한했다. `platform=tiktok`, 동물 카테고리, 종, 영상에서 확인한 행동 근거가 없으면 바이럴 지표가 높아도 추천하지 않는다.
- 참조 쇼츠의 화면 리듬만 반영해 상단 흰 제목, 중앙 실제 원본 장면, 하단 큰 서사 자막을 사용하는 독자 템플릿으로 바꿨다. 참조 채널의 이름·로고·문구·음원은 사용하지 않는다.
- 모든 장면에 `animal_emotion`을 추가했다. 감정 표현은 `관찰`, `보호자 설명`, `행동 해석`으로 구분하며 실제 행동 핵심어가 포함된 근거가 없으면 최종 검증에서 차단한다.
- `music-plan.json`을 추가했다. 자동 모드에서는 장면별 감정 흐름에 따라 `gentle`, `tender`, `tension`, `relief`, `playful` 구간을 이어 붙이고, 직접 고른 프로필은 전체 영상에 고정한다. 렌더러는 외부 음원·보컬·TTS 없이 새 무보컬 앰비언트를 원본 오디오 아래에 합성한다.
- `delivery-note.md`, `edit-plan.md`, `render-report.json`에 원본 링크, 행동·감정 해석 근거, 선택된 음악 프로필을 남긴다.

## 검증

- 동물 샘플 후보는 점수화와 프로젝트 초기화를 통과했다.
- 비동물 카테고리와 동물 근거가 없는 후보는 동물 게이트에서 거절되는 것을 확인했다.
- 스킬 구조 검증과 Python 구문 검사를 통과했다.
- 합성 기술용 소스(실제 동물 영상 아님)로 최종 검증·편집 지시서·렌더를 수행했다. 16.021초, 720x1280, H.264/AAC 결과와 장면별 `tender → gentle → relief → tender` 생성 무보컬 배경음 합성을 확인했다.
- 실제 동물 원본의 권리·사실성·감정 해석은 후보별 검토가 별도로 필요하다.

## 변경 파일

- `plugins/tiktok2shorts/scripts/tiktok2shorts.py`
- `plugins/tiktok2shorts/.codex-plugin/plugin.json`
- `plugins/tiktok2shorts/examples/candidates.sample.json`
- `plugins/tiktok2shorts/README.md`
- `plugins/tiktok2shorts/skills/tiktok2shorts/SKILL.md`
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/{candidate-schema,output-contract,editorial-and-rights}.md`
- `README.md`
