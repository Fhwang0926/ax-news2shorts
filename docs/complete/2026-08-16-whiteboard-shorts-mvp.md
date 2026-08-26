# Whiteboard Shorts Codex 플러그인 MVP 완료

## 완료 내용

- 저장소 로컬 마켓플레이스에 `whiteboard-shorts` Skill-only 플러그인을 추가했다.
- `geeklee/srt-whiteboard-animation`의 MIT 런타임을 커밋 `696a7243c0e6ffb6827676e539c2ca5ebae2bf6b`로 고정해 포함했다.
- SRT 프로젝트 초기화, 장면 계획, Annotation 정적 검증, 9:16 영역 미리보기, 초안/최종 렌더 관문과 다중 장면 병합을 단일 CLI로 구성했다.
- SRT와 장면 이미지의 권리 상태, 사용자 승인, 기존 출력 덮어쓰기 방지를 프로젝트 계약에 포함했다.
- 권리 미확인 초안에는 로컬 검토 표시를 추가하고 clean final은 확인된 권리와 승인값이 있을 때만 허용하도록 구성했다.
- 플러그인을 `whiteboard-shorts@news2shorts-local` 버전 `0.1.0+codex.20260816`으로 설치하고 enabled 상태를 확인했다.

## 주요 파일

- `plugins/whiteboard-shorts/.codex-plugin/plugin.json`: 플러그인 메타데이터와 시작 프롬프트
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/SKILL.md`: Codex 작업 순서와 범위
- `plugins/whiteboard-shorts/scripts/whiteboard_shorts.py`: 프로젝트·검증·미리보기·렌더 CLI
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/references/`: Annotation, 권리, 출력, 시각 스타일 계약
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/templates/`: 프로젝트와 권리 JSON 템플릿
- `plugins/whiteboard-shorts/vendor/srt-whiteboard-animation/`: 고정된 업스트림 렌더러와 MIT 라이선스
- `.agents/plugins/marketplace.json`: 로컬 마켓플레이스 항목

## 확인 결과

- Python 문법 검사 통과
- JSON 파싱 검사 통과
- Skill `quick_validate.py` 통과
- Plugin `validate_plugin.py` 통과
- `git diff --check` 통과
- CLI 도움말과 읽기 전용 `doctor --json` 실행 통과
- Codex 플러그인 목록에서 installed/enabled 확인

## 확인하지 않은 범위

- 렌더 의존성은 설치하지 않았다. 현재 `doctor`의 `ready_for_render`는 `false`다.
- 사용자 지침에 따라 실제 MP4 렌더, 영상 품질 검사, 프론트엔드 빌드는 수행하지 않았다.
- ASR, TTS, 음원, 자막 합성, 공개 영상 취득과 YouTube 업로드는 MVP 범위에 포함하지 않았다.
