# news2shorts 이슈 렌즈·시선 장치 강화

## 완료 일자

- 2026-08-22

## 반영 범위

- 행정 절차나 발표 상태를 그대로 훅으로 요약하지 않고, 검증된 핵심 모순과 실패한 기대를 먼저 정의하도록 변경했다.
- `shorts_profile`에 `issue_focus`, `viewer_stake`, `tension_question`을 추가했다.
- 선택한 훅, 첫 화면, 첫 대사와 결론이 같은 이슈 렌즈를 드러내고 회수하는지 새 프로젝트 최종 검수에서 확인한다.
- `이게 맞나?`, `어떻게 될까?`처럼 대상과 문제가 없는 추상 질문을 허용하지 않는다.
- 새 프로젝트는 `reaction-meme`, `contrast-composite`, `consequence-photo`, `evidence-closeup`, `motion-proof` 중 하나를 핵심 시선 장치로 지정하고 적용 장면과 이유를 기록한다.
- 반응 밈은 비민감 뉴스의 맥락·재후킹에만 사용하며, 상업 이용 권리와 원본 출처가 확인되지 않은 방송·영화·SNS 캡처는 계속 차단한다.
- 기존 프로젝트 version 4 이하는 새 필드 없이도 계속 검증·렌더할 수 있도록 호환성을 유지했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
  - version 5 프로젝트 초기값, 이슈 렌즈·시선 장치 검증, 렌더 보고서의 `attention_strategy` 기록을 추가했다.
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`
  - version 5와 새 `shorts_profile` 필드를 추가했다.
- `plugins/news2shorts/skills/news2shorts/templates/storyboard.template.json`
  - 새 프로젝트 스토리보드 버전을 5로 올렸다.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
  - 훅 작성 전 이슈 렌즈 게이트와 필수 시선 장치 선택 절차를 추가했다.
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`
  - 훅 평가에서 이슈 명확성과 시청자 이해관계를 강화하고 절차 요약과 실제 문제를 구분하도록 했다.
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`
  - 다섯 가지 핵심 시선 장치의 용도와 배치 기준을 정의했다.
- `plugins/news2shorts/skills/news2shorts/references/rights-policy.md`
  - 밈을 핵심 시선 장치로 선택할 때도 권리·민감도 경계를 유지하도록 명시했다.
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
  - version 5 프로젝트·스토리보드·렌더 보고서 계약을 문서화했다.
- `plugins/news2shorts/skills/news2shorts/agents/openai.yaml`, `plugins/news2shorts/README.md`
  - 플러그인의 기본 안내와 사용자용 기능 설명을 갱신했다.
- `plugins/news2shorts/.codex-plugin/plugin.json`
  - 플러그인 버전을 `0.23.0+codex.20260822185843`으로 올리고 새 기능 설명을 반영했다.

## 설계 판단

- 감정 단어를 기계적으로 강제하거나 분노를 조작하지 않고, 출처로 입증되는 모순과 시청자 영향을 구조화했다.
- 밈을 모든 영상에 강제하지 않고 권리와 주제에 맞는 고강도 시각 장치 하나를 선택하도록 했다.
- 새 외부 패키지나 별도 렌더 시스템을 추가하지 않고 기존 프로젝트 JSON, 스토리보드, 권리 매니페스트, 검증기를 재사용했다.

## 검증 결과

- Python AST와 플러그인·템플릿 JSON 파싱 성공
- Skill 구조 검사 성공
- 새 프로젝트 초기화 시 project/storyboard version 5와 새 필드 생성 확인
- version 5 완성 프로젝트 복사본에 구체적인 이슈 렌즈와 시선 장치를 적용했을 때 최종 검증 성공
- 같은 복사본에서 추상 질문과 시선 장치를 제거했을 때 최종 검증 실패 확인
- 기존 version 4 고시원 프로젝트가 수정 없이 최종 검증을 통과해 하위 호환 확인
- 후행 공백 검사와 CLI 도움말 실행 성공
- 로컬 플러그인 `news2shorts@news2shorts-local` version `0.23.0+codex.20260822185843` 설치·활성화 확인
- 설치 캐시의 렌더러와 Skill SHA-256이 작업본과 일치함을 확인

## 수행하지 않은 작업

- 새 뉴스 영상이나 MP4를 다시 제작하지 않았다.
- Typecast 유료 호출과 YouTube 업로드·게시를 수행하지 않았다.
- DB 작업과 프론트엔드 빌드는 대상이 아니므로 수행하지 않았다.
