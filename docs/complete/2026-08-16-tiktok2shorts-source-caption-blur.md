# TikTok2Shorts 원본 자막 영역 블러 반영

## 완료 내용

- 플러그인 버전을 `0.3.6+codex.20260816`으로 올리고 설치·활성화 상태를 갱신했다.
- 원본 영상에 박힌 외국어 자막을 처리하는 `blur_and_localize_bottom` 모드를 추가했다.
- 장면별 `source_caption_blur` 편집 액션과 `source_caption_blur_region` 좌표를 추가했다.
  - 좌표는 원본 프레임 기준 0~1 비율의 `x`, `y`, `width`, `height`다.
  - `radius`는 4~40 범위에서 검증한다.
- 렌더러가 지정한 사각 영역만 FFmpeg `boxblur`로 처리하도록 수정했다.
- 블러와 기존 화면 이동 방식인 `source_caption_safe_reframe`을 같은 장면에서 함께 쓰지 못하게 검증한다.
- 편집 지시서, 전달 안내, 렌더 보고서에 블러 방식과 실제 좌표를 남긴다.
- 워터마크·채널 출처는 보존하고, 원문·한국어 연결과 원본 권리 상태도 그대로 유지한다.

## 샘플 결과물

- 새 프로젝트: `outputs/tiktok2shorts/2026-08-16/나비넥타이를-하고도-아무도-인사해-주지-않는-지하철-강아지-v3-원본자막-블러`
- 기존 v2 프로젝트는 수정하지 않고 보존했다.
- 반복 영문 자막 영역:
  - `x=0.08`
  - `y=0.60`
  - `width=0.84`
  - `height=0.17`
  - `radius=24`
- 한국어 상황극 문구는 하단에만 유지하고 장면 전환 효과는 추가하지 않았다.
- 원본 TikTok 권리 상태는 `unknown`, 결과물은 `local_only`이며 업로드 기능은 없다.

## 변경 파일

- `plugins/tiktok2shorts/scripts/tiktok2shorts.py`
  - 블러 모드·좌표 검증·선택 영역 렌더·보고서 출력을 추가했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/SKILL.md`
  - 외국어 내장 자막을 검토한 영역만 블러하는 기본 작업 규칙으로 수정했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/output-contract.md`
  - 새 모드와 장면 필드 계약을 문서화했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/editorial-and-rights.md`
  - 자막 블러와 워터마크·출처 보존 경계를 문서화했다.
- `plugins/tiktok2shorts/README.md`
  - 사용 예시와 동작 설명을 갱신했다.
- `plugins/tiktok2shorts/.codex-plugin/plugin.json`
  - 버전과 사용자 설명·예시 요청을 갱신했다.
- 샘플 v3 프로젝트의 `project.json`, `storyboard.json`, `viral-analysis.json`, `publish.json`
  - 블러 영역, 원문·번역 연결, 편집 고지를 기록했다.

## 검증

- Python 구문 검사 통과.
- 원본 및 설치 캐시의 skill `quick_validate.py` 통과.
- 원본 및 설치 캐시 렌더러의 `validate --final` 통과.
- 설치 버전: `0.3.6+codex.20260816`.
- 원본·설치 캐시 렌더러 SHA-256 일치:
  - `4d01f18f5a0db755ffb942dca652536107a58d639ceb9d864dae427b2094a369`
- 결과 MP4:
  - 길이 `15.021029초`
  - `720x1280`, `30fps`
  - H.264 영상, AAC 스테레오 오디오
  - 파일 크기 `3,493,045 bytes`
  - SHA-256 `50724c6fac5164a9188d874bbf9d893a35f244ad10acb9f383c64398cab9f94b`
  - 평균 음량 `-28.2 dB`, 최대 음량 `-11.0 dB`
- `final-contact-sheet.jpg`와 `transition-check.jpg`를 확인해 영문 자막이 읽히지 않고, 강아지 얼굴·상단 채널 정보·연속 동작이 유지됨을 검토했다.

## 제한

- 기술 검증과 로컬 렌더 완료는 원본 영상의 게시·재사용 허가, 공정 이용, 수익화 가능성을 의미하지 않는다.
