# Whiteboard Shorts 펀치 리믹스와 장면 줌

## 완료 내용

- 기존 v2 프로젝트를 보존하고 `projects/2026-08-17-border-collie-fake-cat-whiteboard-punch-v3`로 새 렌더를 만들었다.
- 자막을 `shorts-punch` 스타일로 바꿔 첫 줄은 노란색, 둘째 줄은 흰색, 전체는 굵은 검은 외곽선으로 표시한다.
- 다섯 장면 문구를 실제 화면 행동에 맞는 훅, 공개, 재확인, 접근, 결론 순서로 짧게 다시 썼다.
- 코믹·추격·공개 비중이 높은 TikTok 프로젝트는 별도 입력 없이 `can-can` 퍼블릭 도메인 멜로디 리믹스를 선택한다.
- 외부 녹음을 복제하지 않고 캉캉 선율을 160 BPM 전자음으로 새로 합성하며 킥, 클랩, 하이햇, 전환 임팩트를 생성한다.
- 공개·접근·결론 장면에 임팩트 히트를 넣고 장면 1, 2, 4, 5에 목적이 있는 줌을 적용했다.
- 펀치 리믹스는 -14 LUFS, -1.5 dB true-peak 목표로 정규화한다. 이번 결과 측정값은 -14.3 LUFS, -1.1 dBFS다.
- 잔잔하거나 민감한 행동은 기존 `synthetic_ambient`로 자동 회피하도록 유지했다.
- 기존 설치의 격리 렌더 환경이 없는 경우 이전 캐시를 재사용하며, 이번 0.4.0 설치본에는 새 격리 환경도 준비했다.

## 음악 근거와 권리 기록

- 작곡: Jacques Offenbach, `Galop infernal from Orphee aux enfers`
- 악보 근거: `https://imslp.org/wiki/Orph%C3%A9e_aux_enfers_(Offenbach,_Jacques)`
- 작곡 상태: `public_domain`
- 녹음 상태: 플러그인이 새로 만든 합성 녹음, `owned`, `synthetic: true`, `vocals: false`
- TikTok 원본과 장면 이미지 권리는 계속 `unknown`이며 로컬 검토 초안에만 사용한다.

## 플러그인 변경 파일

- `plugins/whiteboard-shorts/scripts/whiteboard_shorts.py`
- `plugins/whiteboard-shorts/.codex-plugin/plugin.json`
- `plugins/whiteboard-shorts/README.md`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/SKILL.md`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/agents/openai.yaml`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/references/post-production-contract.md`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/references/output-contract.md`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/references/rights-policy.md`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/templates/post-production.template.json`

## 결과 프로젝트

- 프로젝트: `projects/2026-08-17-border-collie-fake-cat-whiteboard-punch-v3`
- 결과 영상: `outputs/preview.mp4`
- 이전 음량판 보존: `outputs/preview-before-loudness.mp4`
- 영상 SHA-256: `6985afc8fb0d0d7fff7f546cf1fb702ce5dfc7e6f28990c219c020166c6a5312`
- 음악 SHA-256: `4e17ba0d47bb96a3fd3d2a70d946f63558d71cd0ecf96f989b4d9c3755d1fc97`

## 검증 결과

- 플러그인 `0.4.0+codex.20260817` 설치·활성 확인
- 설치본 `doctor`: `ready_for_render: true`
- Python 구문, manifest/template JSON, 스킬 구조 검사 통과
- 임시 TikTok 가져오기에서 `shorts-punch`, `can-can`, 160 BPM, 장면 임팩트와 줌 계획 자동 생성 확인
- 프로젝트 정적 검사와 `--render-ready` 통과
- 1초 간격 접촉 시트로 자막 위치, 공개 장면 펀치 줌, 마지막 줌아웃 확인
- 1080x1920, 30 FPS, H.264, AAC 48 kHz 스테레오, 15.5초 확인
- clean final은 원본·장면 이미지 권리와 최종 승인 부족으로 의도대로 차단
