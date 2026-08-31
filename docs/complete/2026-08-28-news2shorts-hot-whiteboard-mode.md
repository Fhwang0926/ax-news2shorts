# news2shorts 최신 실사·Whiteboard 옵션 개선 완료

## 완료 내용

- `news2shorts`에 `standard`, `hot-real-news`, `whiteboard` 시각 모드를 추가했다.
- `discover --hot-real-news`는 최근 24시간 범위에서 최근 6시간 내 서로 다른 보도 출처 2곳 이상이 확인되고 시민 영향 관문을 통과한 후보만 남긴다.
- 프로젝트 version을 15로 올리고 시각 모드, 최신 뉴스 게이트, Whiteboard 프로젝트 경로와 원본 권리 상속 여부를 기록하도록 했다.
- 저작권 또는 사용 허가가 확인되지 않은 공개 이미지는 `unreviewed`로 기록할 수 있게 했다.
  - `approved: false`
  - `permission_status: unknown|review_required`
  - `local_review_only: true`
  - canonical `source_url` 필수
  - 로컬 검토본에만 허용하며 실제 뉴스 실사 비율과 clean final 자격에는 포함하지 않는다.
- `prepare-whiteboard` 명령을 추가했다.
  - 기존 뉴스 storyboard의 실제 로컬 이미지 또는 영상 프레임을 사용한다.
  - 기사 연관성 검토와 문자·로고 영역 검토가 끝난 자산만 받는다.
  - warm-paper·dark-ink 선화 이미지를 만들고 원본 permission status를 그대로 상속한다.
  - Whiteboard Shorts의 SRT 호환 프로젝트, 장면 PNG, annotation, 자막·모션·생성 무보컬 음악 계획을 만든다.
- `render --visual-mode whiteboard --draft --confirm-whiteboard-review` 옵션을 추가했다.
  - 장면 이미지와 annotation을 사람이 확인한 뒤에만 로컬 draft를 렌더한다.
  - 결과는 `whiteboard-project/outputs/preview.mp4`에 생성한다.
  - 이 모드는 standard 뉴스한면 인트로와 Typecast 내레이션을 포함하지 않는다.
  - clean final과 외부 업로드는 수행하지 않는다.

## 권리 경계

- 공개 URL, 다운로드 성공, 출처 표시, 크롭, 선화 변환은 게시 권리를 만들지 않는다.
- `not_permitted` 자산은 Whiteboard 검토본에도 사용할 수 없다.
- `unreviewed`, `unknown`, `review_required` 자산은 로컬 draft만 허용한다.
- 게시 가능한 final은 기존과 동일하게 `owned`, `licensed`, `official` 등 사용 근거와 사람 권리 검토가 완료된 자산만 통과한다.
- 뉴스 이미지의 permission status는 Whiteboard 파생 이미지에도 그대로 유지한다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
  - 최신 뉴스 게이트, 시각 모드, unreviewed 검증, Whiteboard 준비·draft 렌더 추가
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`
  - project version 15와 시각 모드 계약 추가
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
  - hot-real-news·unreviewed·Whiteboard 승인 흐름 추가
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
  - version 15과 Whiteboard 결과 구조 추가
- `plugins/news2shorts/skills/news2shorts/references/rights-policy.md`
  - unreviewed 로컬 검토 자산 규칙 추가
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`
  - 실제 뉴스 이미지 선화 파생 스타일과 권리 상속 규칙 추가
- `plugins/news2shorts/skills/news2shorts/agents/openai.yaml`
  - 신규 시각 모드 기본 프롬프트 반영
- `plugins/news2shorts/README.md`
  - 명령 예시와 제한 사항 추가
- `plugins/news2shorts/.codex-plugin/plugin.json`
  - 기능 설명과 캐시버전 갱신

## 설치 및 검증

- 설치 버전: `news2shorts@news2shorts-local` `0.36.5+codex.20260828054930`
- Plugin validator: 통과
- Skill validator: 통과
- project template version 15·시각 모드 JSON 확인: 통과
- `discover`, `init`, `prepare-whiteboard`, `render` 도움말 로딩: 통과
- 변경 파일 공백 검사: 통과

자동화 테스트, 프론트엔드 빌드, 실제 뉴스 이미지 다운로드, Whiteboard 영상 렌더, Typecast 생성, DB 작업과 업로드는 수행하지 않았다.

## 보존 범위

- 기존 news2shorts의 quick-reveal·continuous-flow·실사 60%·썸네일·업로드 패키지 계약을 유지했다.
- 기존 dirty worktree의 자막 정렬, 실사 비율, 공개 문구 중복 제거 변경을 보존했다.
- `whiteboard-shorts` 플러그인 소스와 현재 변경 내용은 수정하지 않고 기존 SRT 호환 실행기만 호출한다.
