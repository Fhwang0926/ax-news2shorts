# 2026-08-20 Animal Viral Shorts 재미·스토리·음악 v2 작업 완료

## 작업 범위

- animal-viral-shorts를 `0.2.0+codex.20260820080036`으로 갱신했다.
- 기존 관찰 근거, 권리 상태, 소스·스토리 사용자 선택, TTS·업로드 금지 정책은 유지했다.
- 새 스토리에 setup, build, turn, payoff 기승전결과 서로 다른 재미 장치를 요구하도록 변경했다.
- 기존 근거 점수와 별도로 훅, 누적, 재훅, 전환, 결말, 반복·댓글 가능성을 평가하는 100점 재미 점수를 추가하고 75점 미만을 차단했다.
- 유형별 길이 하드 게이트를 제거하고 최종 길이를 59.5초 이하로 변경했다. 권리 불명 소스의 개별 8초·총 18초 제한은 유지했다.
- 장면 수를 새 v2 프로젝트에서 4~12개로 확장하고, 5초 초과 장면에 연속 행동과 2회 이상 시각 변화를 요구했다.
- 하단 메시지를 질문, 누적, 전환, 결말 역할에 따라 다른 크기·강조·배경으로 그리도록 변경했다. 기승전결 라벨은 화면에 표시하지 않는다.
- 단일 반복 생성음 대신 같은 BPM과 조성을 유지하면서 장면별 에너지, 원본음 우선순위, 드롭, 임팩트를 적용하는 `synthetic_score_v2`를 추가했다.
- 검토용 렌더의 재미와 음악 적합성을 사용자가 승인해야 최종본을 만들 수 있도록 `approve-draft`와 `draft_approved` 상태를 추가했다.
- 검토용 보고서와 최종 보고서가 충돌하지 않도록 `draft-render-report.json`과 `render-report.json`을 분리했다.
- 기존 v1 프로젝트의 스토리보드와 `synthetic_ambient` 음악 계획은 계속 정적 검증할 수 있도록 호환 경로를 유지했다.

## 변경 파일

- `plugins/animal-viral-shorts/scripts/animal_viral_shorts.py`
  - v2 스토리·재미 점수·59.5초 계약, 장면별 음악, 강조 하단 메시지, 초안 승인, 렌더 보고서 분리를 구현했다.
- `plugins/animal-viral-shorts/.codex-plugin/plugin.json`
  - 버전과 사용자 설명을 v2 기능에 맞췄다.
- `plugins/animal-viral-shorts/README.md`
  - 새 제작 흐름, 초안 승인 명령, 산출물과 음악 동작을 문서화했다.
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/SKILL.md`
  - 기승전결, 재미 장치, 장면별 음악, 초안 승인 절차를 Skill 결정 규칙에 반영했다.
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/agents/openai.yaml`
  - Skill 설명을 새 기능에 맞췄다.
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/references/workflow.md`
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/references/story-schema.md`
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/references/visual-template.md`
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/references/output-contract.md`
  - 새 워크플로, 입력 계약, 자막 스타일, 상태·산출물 계약을 기록했다.
- `plugins/animal-viral-shorts/templates/story-options.input.json`
- `plugins/animal-viral-shorts/templates/music-profiles.json`
- `plugins/animal-viral-shorts/templates/animal-viral-card-v1.json`
  - v2 스토리, 음악, 하단 메시지 기본값을 추가했다.
- `README.md`
  - 플러그인 목록 설명을 v2 기능에 맞췄다.

기존 sibling 플러그인, DB, 웹 UI, 서버는 수정하지 않았다. 작업 전부터 존재하던 다른 변경과 미추적 파일도 제거하거나 재작성하지 않았다.

## 수행한 비파괴 확인

- Plugin validator 통과.
- Skill quick validator 통과.
- 플러그인과 마켓플레이스를 포함한 JSON 파일 파싱 통과.
- CLI 최상위 도움말과 doctor, score-candidates, init, acquire, preview, observe, stories, select-story, compose, edit-plan, validate, approve-draft, render의 개별 도움말 로드 통과.
- `doctor --json`에서 Python, FFmpeg, FFprobe, Pillow, yt-dlp, 한글 글꼴과 59.5초·기승전결·초안 승인 계약을 확인했다.
- 기존 `tucker-nugget-mystery` v1 프로젝트의 `validate --final`이 오류 없이 통과했고, 권리 불명 로컬 검토 경고는 유지됐다.
- 로컬 마켓플레이스에서 `animal-viral-shorts@news2shorts-local`을 `0.2.0+codex.20260820080036`으로 재설치하고 installed, enabled 상태를 확인했다.
- 설치 캐시에서도 Plugin/Skill validator가 통과했고, 원본과 설치본의 CLI·Skill SHA-256이 각각 일치했다.
- `git diff --check`와 변경 대상 파일의 후행 공백 검사가 통과했다.

## 실행하지 않은 검증

- AGENTS.md 지침에 따라 자동 테스트와 프론트엔드 빌드를 실행하지 않았다.
- 외부 후보 조사, 영상 다운로드, DB 작업, 업로드를 수행하지 않았다.
- 새 v2 스토리 입력으로 실제 MP4 전체 렌더를 실행하지 않았다.
- 생성 음악의 실제 청감, 하단 메시지 가독성, 결말 임팩트 타이밍을 영상으로 시청·청취 검수하지 않았다.

## 남은 외부 확인

- 실제 제작에서는 선택 소스의 권리 상태와 현재 공개 지표를 다시 확인해야 한다.
- 새 v2 검토용 MP4를 실제로 보고 스토리 재미와 음악 적합성을 각각 승인해야 한다.
- 기술 검증과 사용자 초안 승인은 게시 권리, 수익화, 동물 복지 판단, 바이럴 성과를 보장하지 않는다.
