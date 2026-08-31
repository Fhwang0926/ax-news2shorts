# 시니어 쇼츠 Phase 1 플러그인 구현 완료

## 완료 범위

- 참고한 시니어 쇼츠 계획을 현재 저장소의 Codex 플러그인 구조로 구현했다.
- `senior-shorts` 플러그인을 `news2shorts-local` 마켓플레이스에 추가했다.
- Phase 1은 55~75세 시청자를 위한 45~60초 한국어 창작 사연툰으로 제한했다.
- 5개 훅을 호기심, 감정, 갈등, 명료성, 스포일러 억제 기준으로 평가하고 최고점 훅을 선택하는 JSON 계약을 추가했다.
- Hook, 인물 소개, 사건 시작, 갈등, 갈등 심화, 반전 직전, 반전, 여운의 8장면 계약을 추가했다.
- 캐릭터 정의와 한국 시니어 사연툰 스타일을 장면 프롬프트에 결합하는 `image-prompts` 명령을 추가했다.
- 사용자가 API 형식으로 내보낸 ComfyUI workflow와 노드 ID를 받아 현재 실행 중인 ComfyUI에 장면을 요청하는 표준 라이브러리 기반 클라이언트를 추가했다.
- macOS 기본 TTS 또는 장면별 사용자 음성 파일을 지원하고 실제 음성 길이와 장면 목표 길이로 타임라인을 만든다.
- 큰 2줄 ASS 자막, 핵심어 색상 강조, 1080×1920 FFmpeg Pan/Zoom, 선택적 BGM, 검토본과 최종본 렌더 명령을 추가했다.
- `project.json` 단계 상태와 `status` 명령을 추가했다.
- 대본, 첫 캐릭터 이미지, 합성·창작 고지, 검토본 승인을 순서대로 기록하며 승인 시점의 SHA-256이 현재 파일과 다르면 이후 단계를 차단한다.
- 기존 출력은 `--overwrite` 없이 덮어쓰지 않고 실제 업로드는 수행하지 않는다.

## 의도적으로 제외한 범위

- LTX-Video와 모든 장면의 AI 영상화
- Character LoRA, IP-Adapter, 캐릭터 기준 이미지 자동 주입
- 건강, 금융, 연금, 복지, 세금, 정부 정책 정보형 콘텐츠와 팩트체크
- OpenAI, ElevenLabs, Typecast API 자동 호출과 비밀키 저장
- BGM/SFX 자동 선택, 배치 생산, 웹 UI, DB, 실제 플랫폼 업로드

## 검증

- Plugin manifest validator를 통과했다.
- Skill frontmatter와 구조 validator를 통과했다.
- 플러그인 내 JSON 파일을 모두 파싱했다.
- Python CLI `--help`와 `doctor --json`을 실행해 명령 로딩을 확인했다.
- 현재 환경에서 Python 3.14.5, FFmpeg, FFprobe, macOS `say`, 한글 폰트를 확인했다.
- 현재 8188 포트에서 실행 중인 ComfyUI 프로세스는 확인되지 않아 API 이미지 생성은 실행하지 않았다.
- `git diff --check`를 통과했다.
- 사용자 지침에 따라 프론트엔드 빌드, 단위 테스트, 샘플 TTS, 이미지 생성, 영상 렌더는 수행하지 않았다.

## 변경 파일

- `.agents/plugins/marketplace.json`: `senior-shorts` 로컬 마켓플레이스 항목을 목록 끝에 추가했다.
- `README.md`: 저장소 플러그인 목록에 `senior-shorts`를 추가했다.
- `plugins/senior-shorts/.codex-plugin/plugin.json`: 플러그인 식별자, UI 정보, 기능 설명, 캐시 식별자를 정의했다.
- `plugins/senior-shorts/README.md`: Phase 1 범위, 기본 흐름, ComfyUI 연결 방법을 기록했다.
- `plugins/senior-shorts/scripts/senior_shorts.py`: 초기화, 검증, 승인, 이미지 프롬프트, ComfyUI, 음성, 자막, 렌더, 상태 명령을 구현했다.
- `plugins/senior-shorts/assets/style-presets.json`: 한국 시니어 사연툰 이미지와 큰 자막 스타일을 정의했다.
- `plugins/senior-shorts/templates/story.template.json`: 5개 훅과 8장면 구조화 대본 템플릿을 추가했다.
- `plugins/senior-shorts/skills/senior-shorts/SKILL.md`: Codex 제작 흐름과 승인 경계를 정의했다.
- `plugins/senior-shorts/skills/senior-shorts/agents/openai.yaml`: 스킬 표시명과 기본 호출 문구를 정의했다.
- `plugins/senior-shorts/skills/senior-shorts/references/story-contract.md`: 대본 구조와 창작·안전 규칙을 정의했다.
- `plugins/senior-shorts/skills/senior-shorts/references/output-contract.md`: 산출물 구조와 검증 수준을 정의했다.
