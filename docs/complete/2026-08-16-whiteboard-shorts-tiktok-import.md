# Whiteboard Shorts TikTok 가져오기 완료

## 완료 내용

- 화이트보드 작업의 기본 입력을 SRT 첨부가 아니라 선택·다운로드·검토된 TikTok2Shorts 프로젝트로 변경했다.
- `init --source-project`가 TikTok 원본 MP4, `source.json`, `storyboard.json`을 새 프로젝트 안으로 복사한다.
- 검토된 한국어 장면 narration을 `input/story.srt`로 변환하고 각 화이트보드 장면에 원본 장면 ID, 시간, 화면 문구와 `source_evidence`를 연결한다.
- TikTok 원본 URL, 제작자, 후보 ID, 영상 SHA-256과 권리 상태를 `project.json`과 `rights-manifest.json`에 보존한다.
- 가져오기 과정에서 권리 상태를 수동으로 상향할 수 없게 했고 `not_permitted` 원본은 차단했다.
- 로컬 SRT 입력은 기존 사용자를 위한 호환 경로로 유지했다.
- 플러그인 버전을 `0.1.1+codex.20260816`으로 올리고 로컬 Codex 캐시에 설치·활성화했다.

## 변경 파일

- `plugins/whiteboard-shorts/scripts/whiteboard_shorts.py`: TikTok2Shorts 프로젝트 검사·복사·SRT 변환·출처 검증
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/SKILL.md`: TikTok 후보 선택부터 화이트보드 제작까지의 기본 흐름
- `plugins/whiteboard-shorts/.codex-plugin/plugin.json`: 버전, 설명, 시작 프롬프트
- `plugins/whiteboard-shorts/README.md`: TikTok 가져오기 사용법
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/references/rights-policy.md`: TikTok 출처·권리 보존 규칙
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/references/output-contract.md`: TikTok 입력 스냅샷 구조
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/templates/project.template.json`: 입력 종류 기본값
- `README.md`: 플러그인 설명

## 확인 결과

- Python 문법 검사와 CLI 도움말 확인 통과
- 기존 로컬 TikTok2Shorts 프로젝트를 이용한 `init --source-project` 실행 통과
- 가져온 7개 장면의 프로젝트 정적 검증 통과
- 원본 MP4, URL, 제작자, SHA-256, 권리 상태와 장면별 관찰 근거 보존 확인
- TikTok 가져오기에서 `--rights-status owned`로 권리를 상향하려는 입력 차단 확인
- Codex 플러그인 목록에서 `0.1.1+codex.20260816` installed/enabled 확인

## 확인하지 않은 범위

- 새 TikTok 후보 검색이나 외부 다운로드는 실행하지 않았다.
- 화이트보드 장면 이미지·annotation 생성과 MP4 렌더는 실행하지 않았다.
- 현재 TikTok 원본 권리는 `unknown`이므로 로컬 검토용 초안 외 게시 가능성을 의미하지 않는다.
