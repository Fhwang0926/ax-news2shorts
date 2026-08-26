# 2026-08-15 story2short MVP 작업 완료

## 작업 범위

- 기존 저장소 로컬 marketplace에 `story2short` 플러그인을 추가했다.
- 로컬 MP4, MOV, MKV, WebM을 독립 프로젝트로 복사하고 원본 경로, 해시, 미디어 정보, 제작자, 출처 URL, 실제 권리 상태를 기록하도록 구현했다.
- FFmpeg로 시간별 분석 프레임을 추출하고 Pillow로 타임스탬프가 포함된 접촉시트를 생성하도록 구현했다.
- `analysis.json`에서 화면 관찰 사실, 추정, 확인 불가 내용을 구분하는 계약을 추가했다.
- 서로 다른 스토리 후보를 정확히 3개 작성하고, 사용자가 고른 후보만 `storyboard.json`에 확정하는 선택 게이트를 추가했다.
- 외부 캐릭터 이미지가 없어도 동작하는 기하형 `observer-v1` 캐릭터를 추가했다.
- `idle`, `confident`, `surprised`, `failed`, `exit` 포즈와 `pop`, 좌우 진입, 부유, 흔들림, 퇴장 모션을 지원한다.
- 장면별 캐릭터 대사, 상단 헤드라인, 하단 한국어 자막, 원본 출처, 원본 오디오 낮춤을 합성한다.
- 권리 미확정 프로젝트는 표시가 있는 검토본만 허용하고, 깨끗한 최종본에는 승인된 권리 상태와 네 가지 사람 검토 완료 값을 요구한다.
- 기존 출력과 분석 프레임은 명시적인 `--overwrite` 없이는 교체하지 않는다.
- Skill UI 메타데이터, 스토리 규칙, 출력 계약, 권리 정책, 사용 문서를 추가했다.

## 의도적으로 제외한 범위

- 원격 영상 다운로드, 로그인·CAPTCHA·DRM 우회, 워터마크 제거
- 외부 VLM·ASR·TTS API, 캐릭터 이미지 생성, 실시간 객체 추적과 오클루전 합성
- DB, MCP 서버, 웹 UI, 클라우드 렌더
- TikTok, YouTube 또는 다른 서비스로의 업로드
- 저작권, 공정 이용, 플랫폼 수익화 적합성 자동 판정

## 검증 경계

- Python 구문, Skill frontmatter, Plugin manifest, character·marketplace JSON 형식을 검사했다.
- 로컬 환경에서 Python 3.14, Pillow, FFmpeg, FFprobe, 한글 폰트, macOS 로컬 TTS 탐지를 확인했다.
- 권리 문제가 없는 18초 합성 세로 영상을 사용해 프로젝트 초기화, 2초 간격 9개 프레임과 접촉시트 생성, 스토리 후보 선택, 정적 검증을 수행했다.
- 4장면 16초 fixture에서 좌우 진입, 부유, 흔들림, 퇴장 캐릭터 모션과 대사, 헤드라인, 하단 자막, 출처, 검토 표시가 실제 프레임에 들어간 것을 확인했다.
- 검토본과 승인 후 최종본이 모두 16.021초, H.264, AAC, 720x1280, 영상·오디오 스트림 포함 조건을 통과했다.
- 실제 타인 영상 처리, 권리 증빙의 법적 유효성, 외부 게시, 수익화 가능성은 검증하지 않았다.
- 프론트엔드 빌드나 테스트는 수행하지 않았다.

## 변경 파일

- `.agents/plugins/marketplace.json`
- `README.md`
- `plugins/story2short/.codex-plugin/plugin.json`
- `plugins/story2short/scripts/story2short.py`
- `plugins/story2short/assets/characters/observer-v1/character.json`
- `plugins/story2short/skills/story2short/SKILL.md`
- `plugins/story2short/skills/story2short/agents/openai.yaml`
- `plugins/story2short/skills/story2short/references/output-contract.md`
- `plugins/story2short/skills/story2short/references/story-rules.md`
- `plugins/story2short/skills/story2short/references/rights-policy.md`
- `plugins/story2short/README.md`
- `docs/complete/2026-08-15-story2short-mvp.md`
