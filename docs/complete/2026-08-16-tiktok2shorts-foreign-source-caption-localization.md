# TikTok2Shorts 외국어 원본 자막 개선 완료

## 판단

- YouTube Shorts 검색 결과의 한국어 동물 쇼츠 5개 썸네일을 표본으로 확인했다. 표본은 대체로 한 개의 큰 한국어 주자막을 사용했고, 서로 다른 의미의 원문과 한국어 문구를 동시에 크게 보여 주는 구성은 확인하지 못했다.
- YouTube 공식 도움말은 텍스트의 노출 시점을 장면에 맞추고 Shorts UI의 안전 영역을 시각 가이드로 확인하도록 안내한다.
  - https://support.google.com/youtube/answer/13380879?hl=en
  - https://support.google.com/youtube/answer/16215842?hl=en-NG
- TikTok 공식 안내는 자막 번역을 언어 장벽을 줄이는 기능으로 설명한다.
  - https://newsroom.tiktok.com/auto-translations-and-captions?lang=en
- 원본 자막을 지우거나 흐리는 대신, 원문을 화면에 온전히 보존하면서 첫 큰 하단 한국어 자막이 원문의 뜻과 상황극 훅을 함께 전달하는 방식을 선택했다.

## 플러그인 개선

- `tiktok2shorts@news2shorts-local`을 `0.3.3+codex.20260816`으로 갱신했다.
- `project.template.source_caption_handling`을 추가했다.
  - `not_detected`: 원본 내장 자막 없음
  - `preserve`: 원본 자막 보존
  - `preserve_and_localize_bottom`: 원문을 보존하고 연결 장면의 큰 하단 한국어 자막에 뜻을 통합
- `bridges`의 `scene_id`, `source_text`, `korean_text`와 실제 장면의 `korean_caption` 일치를 최종 검증한다.
- `source_caption_safe_reframe`과 `source_vertical_shift_pixels`를 추가했다.
  - 자막만 제거·블러·인페인팅하지 않는다.
  - 원본 프레임 전체를 위로 이동해 하단 패널에 가려진 원문을 안전 영역 안으로 옮긴다.
  - 1~400px 범위와 원본 영상 장면 여부를 검증한다.
- 편집 지시서, 전달 안내, 렌더 보고서에 원문 자막 처리 방식과 연결 문구를 기록한다.

## 길버트 v2 결과

- 기존 결과는 보존하고 새 프로젝트를 만들었다.
  - `outputs/tiktok2shorts/2026-08-16/나비넥타이를-하고도-아무도-인사해-주지-않는-지하철-강아지-v2-원문자막-한국어통합`
- 반복되는 영어 원문:
  - `Nobody wants to pet Gilbert even though he's got his best bow tie on.`
- 첫 한국어 통합 문구:
  - `나비넥타이 풀세팅인데 쓰담 한 번을 안 줌`
- 모든 연속 장면에 동일한 180px 상향 리프레임을 적용했다.
- 영어 원문 세 줄, 길버트 얼굴, 상단 채널명, 하단 역할·상황극 문구가 모두 보인다.
- 장면 사이 페이드나 이미지 전환은 추가하지 않았다.

## 변경 파일

- `plugins/tiktok2shorts/.codex-plugin/plugin.json`
  - 버전과 외국어 원본 자막 처리 설명·기본 요청을 갱신했다.
- `plugins/tiktok2shorts/scripts/tiktok2shorts.py`
  - 원문-한국어 연결 검증, 원본 프레임 상향 리프레임, 편집·전달·렌더 메타데이터를 추가했다.
- `plugins/tiktok2shorts/README.md`
  - 반복 원문 통합과 안전 리프레임 사용법을 기록했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/SKILL.md`
  - 프레임 검토 후 내장 자막 처리 절차를 추가했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/output-contract.md`
  - `source_caption_handling`, bridge, 안전 리프레임 계약을 추가했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/editorial-and-rights.md`
  - 원문 보존과 한국어 읽기 경로 통합 원칙을 추가했다.
- 길버트 v2 프로젝트의 `project.json`, `script.json`, `storyboard.json`, `viral-analysis.json`과 재생성된 편집·전달·렌더 산출물

## 검증

- Python 구문 검사 통과
- Skill Creator `quick_validate.py` 통과
- 플러그인 매니페스트와 프로젝트 JSON 파싱 통과
- 설치된 `0.3.3` 스크립트와 저장소 스크립트 SHA-256 일치
  - `cdc50e53db475172bb51744b1a3cac680bc056ddacbba244a276289ea24897f7`
- 설치된 버전으로 프로젝트 `validate --final` 통과
- 최종 MP4: 15.021초, 720×1280, 30fps, H.264/AAC
- 파일 크기: 4,053,857바이트
- 평균 음량: -28.2dB, 최대 음량: -11.0dB
- 최종 MP4 SHA-256:
  - `b9944d683bb47521fd15e87ad2473709e746e0431184a5e04e28b3bb4c88bf99`
- 대표 프레임과 장면 경계 프레임을 검토해 영어 원문 전체, 길버트 얼굴, 한국어 자막, 무전환 연결을 확인했다.

## 권리와 범위

- 원본 권리 상태는 `unknown`, 배포 모드는 `local_only`로 유지했다.
- 원본 자막과 워터마크를 삭제하지 않았다.
- 외부 업로드 기능은 추가하거나 사용하지 않았다.
- 기술 검증은 게시 허가, 공정 이용, 수익화 가능성을 확정하지 않는다.
