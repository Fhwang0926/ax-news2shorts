# news2shorts 썸네일·10초 후킹 개선

## 완료 일자

- 2026-08-25

## 반영 범위

- 새 프로젝트 버전을 13으로 올리고 첫 뉴스 장면을 2.5초 이하로 제한했다.
- 고정 인트로를 포함한 전체 타임라인 10초 안에 근거가 있는 부분 반전 장면이 시작되도록 `early_rehook_scene_id`와 요청·실측 타이밍 검증을 추가했다.
- `withheld_detail`에는 결론까지 미룰 한 가지 답을, `truth_guard`에는 초반에 반드시 밝혀야 할 조사 상태·범위·기간·비교 기준을 기록하게 했다.
- 애매한 표현은 사실을 흐리는 방식이 아니라 검증된 사실 하나를 먼저 공개하고 답 하나만 뒤로 미루는 `controlled incompleteness`로 정의했다.
- 별도 썸네일에 주제별 긴장 배지와 검증된 보조 문구를 요구하고 `충격`, `속보`, `이게 맞아?` 같은 일반 배지를 거부한다.
- 일반 비민감 뉴스는 권리와 비당사자 맥락을 확인한 별도 진행자 자산이 있을 때 진행자형 분할 구도를 사용한다.
- 진행자 자산은 `thumbnail-presenter`, `presenter_context_reviewed: true`, `case_party: false`를 요구하며 사건 당사자가 아니라는 화면 표시를 넣는다.
- 민감 뉴스 또는 안전한 진행자 자산이 없는 프로젝트는 직접 뉴스 근거 중심 합성으로 자동 전환한다.
- 업로드 정보에 썸네일 훅, 보조 문구, 긴장 배지, 구성 방식을 함께 표시한다.
- 플러그인 버전을 `0.35.1+codex.20260825202500`으로 갱신하고 로컬 Codex 캐시에 재설치했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 10초 재후킹 검증, 진행자형 썸네일 렌더링·권리 검사, 업로드 정보 출력.
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`: version 13과 초반 유지 프로필 필드.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 10초 후킹, 통제된 정보 지연, 안전한 진행자 썸네일 제작 절차.
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`: 첫 10초 스토리 계약.
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`: 진행자형·근거형 썸네일 구도.
- `plugins/news2shorts/skills/news2shorts/references/rights-policy.md`: 썸네일 진행자 출처·비당사자 검토 규칙.
- `plugins/news2shorts/skills/news2shorts/references/upload-package.md`: 썸네일 업로드 필드 정의.
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: version 13 계약과 렌더 보고서 항목.
- `plugins/news2shorts/README.md`: 사용자용 동작 설명.
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전과 기능 설명.

## 검증 결과

- Python AST와 플러그인·템플릿·마켓플레이스 JSON 파싱을 통과했다.
- Skill Creator 빠른 구조 검사를 통과했다.
- 새 프로젝트 초기화 결과가 version 13, 초반 유지 필드, 썸네일 신규 필드를 포함하는지 확인했다.
- 고정 인트로를 포함한 요청 타임라인과 Typecast 실측 타임라인에서 10초 초과 재후킹이 차단되는지 확인했다.
- 720x1280 진행자형 썸네일 생성과 민감 뉴스의 근거형 자동 전환을 확인했다.
- 설치본 `doctor --json`은 `ok: true`였고, `news2shorts@news2shorts-local` `0.35.1+codex.20260825202500` installed·enabled 상태를 확인했다.
- 작업본과 설치 캐시의 핵심 스크립트·Skill SHA-256이 일치했다.

## 수행하지 않은 작업

- 실제 뉴스 프로젝트 생성, 외부 이미지 수집, Typecast API 호출, 영상 렌더, YouTube 업로드는 수행하지 않았다.
- 현재 Codex 실행은 macOS 키체인 확인이 제한되어 Typecast 키의 부재를 단정하지 않았다.
- 프론트엔드 빌드와 DB 작업은 수행하지 않았다.
