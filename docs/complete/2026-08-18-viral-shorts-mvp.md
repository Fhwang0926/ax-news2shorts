# 2026-08-18 Viral Shorts MVP 작업 완료

## 작업 범위

- 기존 저장소 로컬 marketplace에 `viral-shorts` 플러그인을 추가했다.
- 로컬 영상 또는 허가된 URL을 출처로 등록하고 제작자, SHA-256, 미디어 정보, 실제 권리 상태와 근거를 기록하도록 구현했다.
- SRT, VTT, timestamp JSON을 공통 `transcript.json`으로 정규화하도록 구현했다.
- 특정 연예인에 종속되지 않는 `주체 → 계기 → 행동 → 반응 → 결말` Moment Schema와 타임스탬프 근거 계약을 추가했다.
- 완결성, 의외성, 반응 강도, 감정 변화, 후크, 맥락 독립성 등 11개 항목을 고정 가중치 100점으로 계산하도록 구현했다.
- 팬 맥락 의존, 10초 초과 설명, 결말 누락, 다화자, 정적 화면, 낮은 오디오 품질, 잘랐을 때 불완전한 사건의 7개 감점 규칙을 추가했다.
- 같은 `event_id` 또는 짧은 구간 기준 70% 이상 겹치는 후보를 높은 점수 하나로 정리하도록 구현했다.
- Top-K `candidates.json`과 사람이 읽는 `candidates.md`를 만들고, 사용자 선택 전 자동 확정을 금지하는 `select` 명령을 추가했다.
- K-pop, 연예인, 스포츠, 팟캐스트, 동물 preset 분석 지침과 출처·권리·동물 행동 표현 경계를 추가했다.
- 기존 결과는 `--overwrite` 없이는 교체하지 않도록 했다.

## 의도적으로 제외한 범위

- 원격 영상 다운로드와 접근 제한 우회
- ASR, 얼굴 인식, 감정 인식, VLM 자동 분석
- 9:16 리프레임, 자막 합성, 영상 렌더링과 업로드
- DB, MCP 서버, 웹 UI, 멀티 에이전트 구조
- 조회수 예측 모델, 성과 수집, 자동 가중치 보정
- 저작권, 공정 이용, 플랫폼 수익화 가능성 자동 판정

## 검증 경계

- Skill validator와 Plugin validator가 통과했다.
- Plugin manifest와 marketplace JSON 형식을 확인했고 `git diff --check`가 통과했다.
- Python CLI 도움말과 `doctor --json`을 확인했으며 로컬 Python 3.14.5, FFprobe, FFmpeg를 탐지했다.
- 임시 URL 메타데이터와 6개 SRT 구간, 3개 Moment fixture로 `init → import-transcript → score → select → validate` 흐름을 확인했다.
- fixture에서 Top-2 후보가 생성되고 같은 사건의 대안 구간 1개가 제거됐으며, 선택 기록을 포함한 프로젝트 검사 결과 `ok: true`를 확인했다.
- 실제 영상 내용, 시각 반응, 원본 권리, 조회수 성과, 렌더링, 외부 게시를 검증하지 않았다.
- 프론트엔드 빌드·테스트와 DB 작업은 수행하지 않았다.

## 변경 파일

- `.agents/plugins/marketplace.json`
- `README.md`
- `plugins/viral-shorts/.codex-plugin/plugin.json`
- `plugins/viral-shorts/README.md`
- `plugins/viral-shorts/scripts/viral_shorts.py`
- `plugins/viral-shorts/skills/viral-shorts/SKILL.md`
- `plugins/viral-shorts/skills/viral-shorts/agents/openai.yaml`
- `plugins/viral-shorts/skills/viral-shorts/references/workflow.md`
- `plugins/viral-shorts/skills/viral-shorts/references/moment-schema.md`
- `plugins/viral-shorts/skills/viral-shorts/references/scoring.md`
- `plugins/viral-shorts/skills/viral-shorts/references/rights-policy.md`
- `plugins/viral-shorts/skills/viral-shorts/references/output-contract.md`
- `docs/complete/2026-08-18-viral-shorts-mvp.md`
