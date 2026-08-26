# news2shorts 자동 포맷·강조 줌·반응 밈·공통 CTA 반영

## 완료 일자

- 2026-08-20

## 반영 범위

- 출처 확인 뒤 뉴스 구조에 맞는 가장 짧은 포맷을 자동 선택하고 선택 이유와 신뢰도를 `project.json`에 기록한다.
  - 한 가지 반전·비교·정답: `quick-reveal`
  - 서로 다른 검증 주장 3개 이상: `fact-stack`
  - 원인·과정·시간 흐름: `story-explainer`
- 새 스토리보드는 `story_link.answers`와 `story_link.next_gap`으로 장면 간 질문과 답의 연결을 검사한다.
- 새 정지 장면은 기본 `motion: none`이며, 강조 대상이 대사나 화면 근거에 있을 때만 `motion_start`, `motion_duration`, `motion_emphasis`로 짧은 줌을 허용한다.
- 줌 장면은 정지 장면의 절반 이하, 연속 두 장면 이하로 제한한다.
- 비민감 뉴스의 맥락·재후킹 장면에는 상업 이용 권리가 확인된 반응 밈 또는 직접 만든 밈 카드를 약 20% 이하로 허용한다. 팩트 증거, 민감 피해, 범죄 피해자, 미성년자, 의료 응급 상황에는 사용하지 않는다.
- 새 영상은 결론을 끝낸 뒤 0.8-1.8초 공통 `다음 뉴스도 핵심만 / 구독 · 좋아요` 테일을 정확히 한 번 붙인다.
- 기존 version 3 프로젝트는 기존 동작과 검증 규칙을 유지한다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
  - version 4 프로젝트 초기화, 포맷 선택·스토리 연결·반응 밈 권리·강조 구간 줌·CTA 검증과 렌더를 추가했다.
  - 720폭 CTA에서 중앙 정렬 폭을 명시해 글자가 잘리지 않도록 수정했다.
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`
  - `format_selection`, `cta_tail`, version 4 기본값을 추가했다.
- `plugins/news2shorts/skills/news2shorts/templates/storyboard.template.json`
  - `story_link`, `visual_role`, 구간 줌 필드와 기본 정지 모션을 추가했다.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
  - 자동 포맷 선택, 장면 연결, 권리 확인 반응 밈, 선택적 줌, 공통 CTA 제작 절차를 반영했다.
- `plugins/news2shorts/skills/news2shorts/references/`
  - 포맷·대본·시각 스타일·권리·출력 계약을 version 4 기준으로 맞췄다.
- `plugins/news2shorts/README.md`, `README.md`
  - 사용자 흐름과 기능 설명을 새 규칙에 맞췄다.
- `plugins/news2shorts/.codex-plugin/plugin.json`, `plugins/news2shorts/skills/news2shorts/agents/openai.yaml`
  - 버전을 `0.19.0+codex.20260820`으로 올리고 기본 호출이 포맷을 자동 선택하도록 갱신했다.

## 검증 결과

- Python 도움말 실행과 JSON 템플릿 파싱 성공
- Skill 구조 검사 성공
- `git diff --check` 성공
- 기존 version 3 퀵리빌·팩트스택·스토리 최종 검사 모두 통과
- 임시 version 4 퀵리빌 샘플 최종 검사 통과
- 임시 샘플에서 6개 정지 장면 중 2개만 강조 줌 적용 확인
- 임시 샘플 MP4가 720x1280, H.264/AAC이고 CTA 적용 기록이 1.2초로 생성되는 것을 확인
- CTA 마지막 프레임을 직접 확인해 큰 글자 중앙 정렬과 화면 내 비잘림 확인
- 설치 캐시와 소스 렌더러 SHA-256 일치 확인
- 로컬 플러그인 `news2shorts@news2shorts-local` 0.19.0 설치·활성화 확인

## 수행하지 않은 작업

- 뉴스 영상 신규 제작과 외부 업로드는 하지 않았다.
- Typecast 유료 호출은 하지 않고 무음 검토 렌더로 영상 합성 경로를 확인했다.
- DB 작업과 프론트엔드 빌드는 대상이 아니므로 수행하지 않았다.
