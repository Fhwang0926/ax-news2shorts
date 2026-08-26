# 2026-08-16 tiktok2shorts 자동 편집 품질 개선 작업 완료

## 검토 결과와 개선

- 기존 결과는 원본 보상 장면 대신 추상적인 해설 카드로 시작했고, 카드가 편집 그래픽이 아니라 임시 UI처럼 보여 영상의 맥락과 시선 유도가 약했다.
- `role` 값(`hook`, `evidence`, `commentary`, `payoff`, `conclusion`)에 따라 카드 색상·핵심 문구·정리 단계를 자동 구성하도록 렌더러를 바꿨다. `visual_path`가 없을 때 더 이상 가짜 목록 UI를 만들지 않는다.
- 상단 영역은 작은 해설 표기와 2줄 제목으로 줄이고, 하단 자막은 작고 분리된 안전 영역으로 정리해 원본 조리 화면을 더 많이 보이게 했다.
- 최종 렌더가 TTS 길이에 맞춰 장면을 늘릴 때, `render-report.json`에 실제 장면 시작·끝·길이를 기록하고 `edit-plan.md`도 그 실제 타임라인으로 갱신하게 했다.

## 개선된 로컬 결과물

- `outputs/tiktok2shorts/2026-08-16/egg-drop-soup/outputs/short.mp4`
- 26.858초, 720x1280, H.264 영상과 AAC 한국어 내레이션(Yuna)이다.
- 첫 장면은 00:42.2~45.8의 달걀 리본 보상 장면으로 시작하고, 재료·국물·보상 장면의 원본 사용량은 총 17.3초다. 장면당 8초, 총 18초 제한 안이다.
- 원본 워터마크·영문 표기를 지우지 않았고, 원본 오디오는 근거 장면에서 낮추며 출처를 표기한다.
- 원본 권리 상태는 `unknown`으로 유지한다. 결과물은 `local_only`이며 공개·수익화·이용 허가를 뜻하지 않는다.

## 검증 경계

- Python 구문 검사와 최종 프로젝트 `validate --final`을 통과했다.
- 실제 렌더를 완료하고 `ffprobe`와 `render-report.json`으로 H.264, AAC, 720x1280, 영상·음성 스트림, 26.858초를 확인했다.
- 추출 프레임으로 보상 장면 시작, 원본 화면 가림 감소, 역할별 해설 카드, 실제 타임라인 갱신을 검토했다.
- 외부 업로드, 게시 권한, 수익화 판단, 라이선스의 법적 유효성은 검증하지 않았다.

## 변경 파일

- `plugins/tiktok2shorts/scripts/tiktok2shorts.py`
- `plugins/tiktok2shorts/README.md`
- `plugins/tiktok2shorts/skills/tiktok2shorts/SKILL.md`
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/output-contract.md`
- `outputs/tiktok2shorts/2026-08-16/egg-drop-soup/*`
