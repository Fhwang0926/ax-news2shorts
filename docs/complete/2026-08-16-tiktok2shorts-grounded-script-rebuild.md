# 2026-08-16 tiktok2shorts 실제 내용 대본·해설 리빌드 완료

## 요청 반영

- 기존의 “기다린 보상”, “다음 변화”, “빈칸”처럼 편집 구조만 설명하던 문구를 제거했다.
- 선택한 원본 프레임을 다시 검토해 `버섯과 썬 무 투입`, `흰 후추와 설탕으로 간 맞추기`, `달걀을 포크로 풀기`, `국물을 저으며 달걀물 붓기`로 시나리오·헤드라인·화면 문구를 교체했다.
- `script.json.storyboard_override`는 계속 원본 구간·길이·권리를 바꾸지 못하며, 적용된 화면 문구는 장면의 실제 원본 근거와 일치해야 한다.

## 플러그인 개선

- `storyboard.json`의 각 최종 장면에 `script_segment_id`와 `source_evidence`를 요구한다.
- `source_evidence`에는 검토한 실제 동작과 두 개 이상의 재료·도구·동작 핵심어를 기록한다.
- 최종 검증은 해당 핵심어가 별도 한국어 시나리오와 실제 화면 문구에도 함께 있는지 확인한다. 장면과 연결되지 않은 해설 구간도 거부한다.
- 이 검증을 통과하지 못하면 최종 MP4 렌더를 시작하지 않는다.

## 결과물

- 최종 MP4: `outputs/tiktok2shorts/2026-08-16/egg-drop-soup/outputs/short.mp4`
- 전달 문서: `outputs/tiktok2shorts/2026-08-16/egg-drop-soup/delivery-note.md`
- 원본 링크: `https://www.tiktok.com/@jujumaoo/video/7662349457840688405`
- 17.321초, 720x1280, H.264/AAC, 4개 장면 모두 `source_video`, 대본 오버라이드 적용됨.

## 검증 경계

- Python 구문 검사, `validate --final`, 실제 `render --overwrite`, 변경 공백 검사를 통과했다.
- 최종 MP4의 네 장면을 추출해 실제 화면과 제목·화면 문구의 일치를 확인했다.
- 외부 업로드, 게시 권한, 수익화 판단, 라이선스의 법적 유효성은 검증하지 않았다. 원본 권리 상태는 계속 `unknown`이며 결과물은 로컬 전용이다.

## 변경 파일

- `plugins/tiktok2shorts/scripts/tiktok2shorts.py`: 근거 연결과 실제 내용 검증 추가.
- `plugins/tiktok2shorts/.codex-plugin/plugin.json`: 0.1.3 버전과 설명 반영.
- `plugins/tiktok2shorts/README.md`, `skills/tiktok2shorts/SKILL.md`, `skills/tiktok2shorts/references/output-contract.md`: 실제 내용 대본 계약 문서화.
- `outputs/tiktok2shorts/2026-08-16/egg-drop-soup/{script,storyboard,commentary-plan,viral-analysis}.json`: 원본 프레임 근거 대본과 화면 문구로 교체.
