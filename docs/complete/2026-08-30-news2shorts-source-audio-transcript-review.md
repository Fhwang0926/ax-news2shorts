# news2shorts 소스 음성 전사 검토 추상화

## 완료 내용

- `audio_mode: "source-video"` 장면을 공통 대상으로 삼는 `review-source-audio` 명령을 추가했다.
- 이미 설치된 로컬 OpenAI Whisper CLI와 캐시된 모델을 자동 감지하며, 없으면 임의 설치·다운로드하지 않고 `transcript_pending`으로 중단한다. 모델 다운로드는 `--allow-model-download`를 명시한 경우에만 허용한다.
- 검토된 UTF-8 JSON 또는 단일 장면 텍스트 전사를 대체 입력으로 받을 수 있게 했다.
- 장면별 영상 SHA-256, `video_start`, `duration`, 예상 `narration`, 전사 문구, 선택적 발화 구간과 컷 여백을 `source-audio-review.json`에 기록한다.
- 예상 대사 누락, 낮은 대사 포함률, 컷 경계 0.15초 이내 발화를 불일치로 판정한다.
- 영상 파일, 컷 시간, 예상 대사가 바뀌면 이전 검토를 무효로 처리한다.
- 초안 검증은 누락·불일치를 경고하고, 최종 검증과 최종 렌더는 통과 기록이 없으면 차단한다.
- 전사는 화자의 신원이나 발언의 사실성을 증명하지 않는다는 편집 경계를 보고서와 문서에 기록했다.
- 편집 호환 패키지의 `metadata/`에 전사 검토 보고서가 있을 때 함께 보존한다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
  - 전사 백엔드 감지, 전사 입력 정규화, 대사 대조, 컷 경계 판정, 검토 보고서 생성, 최종 검증 게이트를 추가했다.
- `plugins/news2shorts/tests/test_retention_v16.py`
  - 대사 후반 누락, 정상 전사, 컷 경계 위험, 초안·최종 차등 처리, 검토 후 타이밍 변경 무효화를 검사한다.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
  - 원본 전체 영상 보존, 전사 검토 순서, 로컬 우선 및 사실성 경계를 추가했다.
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
  - `source-audio-review.json` 계약과 편집 패키지 보존 규칙을 추가했다.
- `plugins/news2shorts/README.md`
  - 자동 및 승인 전사 파일 사용 예시를 추가했다.
- `plugins/news2shorts/.codex-plugin/plugin.json`
  - 설치 캐시 갱신용 버전을 `0.36.5+codex.20260830030035`로 변경했다.

## 확인 결과

- Python 문법 검사 통과.
- `plugins.news2shorts.tests.test_retention_v16` 10개 테스트 통과.
- 모의 장면에서 `저기요. 경찰이에요, 경찰.` 대비 `저기요` 전사는 `mismatch`로 판정됐다.
- 전체 예상 대사와 안전한 컷 여백을 가진 전사는 `passed`로 판정됐다.
- 로컬 Whisper CLI가 없는 현재 환경에서 자동 전사는 `transcript_pending`으로 안전하게 중단됐다.
- 기존 `2026-08-30-2am-police-door-check` 프로젝트는 초안 검증에서 전사 검토 누락 경고, 최종 검증에서 차단 오류가 확인됐다.

## 범위 제외

- Whisper 또는 다른 ASR 패키지와 모델은 설치하지 않았다.
- 클라우드 음성 업로드는 추가하지 않았다.
- 기존 프로젝트 영상과 렌더 결과는 다시 만들거나 수정하지 않았다.
