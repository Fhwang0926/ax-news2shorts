# Whiteboard Shorts 장면 자막과 배경음

## 완료 내용

- 기존 무음 화이트보드 프로젝트를 보존하고 자막·BGM 적용본을 별도 v2 프로젝트로 만들었다.
- `post-production.json` 계약을 추가해 장면별 한국어 코믹 자막, 위치, 무보컬 음악 프로필, 음량, 페이드와 권리 상태를 기록했다.
- TikTok2Shorts에서 가져온 장면 역할과 음악 큐를 기본값으로 사용해 새 프로젝트 생성 시 추가 입력 없이 자막·BGM 계획을 만든다.
- 자막은 실제 화면 행동을 벗어나지 않는 한 장면 한 농담, 최대 두 줄 규칙으로 렌더한다.
- 배경음은 외부 음원을 사용하지 않고 플러그인이 직접 생성하며 `owned`, `synthetic: true`, `vocals: false`, SHA-256을 기록한다.
- 보더콜리 영상은 1~2번 장면에 `tension`, 3~5번 장면에 `playful`을 적용했다.
- 초반 긴장 구간이 너무 작게 측정되어 생성 톤을 2.5배 보강하고 전체 믹스 값을 0.4로 조정했다.

## 변경 파일

- `plugins/whiteboard-shorts/scripts/whiteboard_shorts.py`
- `plugins/whiteboard-shorts/.codex-plugin/plugin.json`
- `plugins/whiteboard-shorts/README.md`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/SKILL.md`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/agents/openai.yaml`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/references/output-contract.md`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/references/rights-policy.md`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/references/post-production-contract.md`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/templates/post-production.template.json`

## 결과 프로젝트

- `projects/2026-08-16-border-collie-fake-cat-whiteboard-caption-bgm-v2`
- 결과 영상: `outputs/preview.mp4`
- 결과 SHA-256: `715d63b3e3d564f38f187d830e268b8103f755737515b1d88f04812343d01ccd`

## 검증 결과

- 플러그인 버전: `0.3.1+codex.20260816`, 설치·활성·격리 렌더 환경 확인
- Python 구문, 플러그인 JSON, 스킬 구조 검사 통과
- 프로젝트 `validate --render-ready` 통과
- 자막 5개 위치와 최종 화면 육안 확인
- 1080x1920, 30 FPS, H.264, AAC 48 kHz 스테레오, 15.5초 확인
- 초반 BGM 평균/최대: -34.7/-25.3 dB, 후반 BGM 평균/최대: -28.6/-14.7 dB
- 권리 상태 `unknown`인 원본·장면 이미지는 로컬 초안에만 사용하고 clean final은 차단
