# Animal Viral Shorts 관찰 대비형 프리셋 반영

## 완료 일자

- 2026-08-25

## 반영 결과

- 신규 Animal Viral Shorts 프로젝트의 기본 화면 프리셋을 `observation-contrast-v1`으로 추가했다.
- 기존 `animal-viral-card-v1`의 720x1280 골격, 원본 영상 처리, 원본음, 비보컬 BGM·효과음, CTA 파이프라인은 재사용했다.
- 상단 고정 2줄 헤드라인, 붉은 강조와 노란 대비 표시, 하단 관찰 대상 라벨·행동 카드로 빠른 관찰→대비→결말 위계를 구현했다.
- 관찰 대비형의 모든 비트에 2~12자 `subject_label`을 요구하고, 검토된 관찰 대상과 연결되지 않거나 대사·감탄문 형태인 라벨을 차단했다.
- 일반 장면은 3초, 마지막 장면은 실제 프레임 고정을 포함해 4초 이내로 제한했다.
- 프리셋 필드가 없는 기존 프로젝트는 `animal-viral-card-v1`으로 처리해 기존 화면을 유지했다.
- 참조 채널의 로고·폰트·문구·음악·원본 영상·장면 순서를 복제하지 않고 정보 위계와 편집 리듬만 일반화하도록 스킬 지침을 추가했다.
- 재가공 여부와 별개로 `unknown`·`review_required`는 로컬 검토 전용, `not_permitted`는 차단하는 기존 권리 경계를 유지했다.
- 플러그인 버전을 `0.5.0+codex.20260825132723`으로 갱신하고 `news2shorts-local` 설치 캐시에 재설치했다.

## 변경 파일

- `plugins/animal-viral-shorts/scripts/animal_viral_shorts.py`: 프리셋 선택·전파·검증, 대상 라벨 계약, 관찰 대비형 오버레이 렌더, 기존 프로젝트 fallback, 진단 출력 추가.
- `plugins/animal-viral-shorts/templates/observation-contrast-v1.json`: 신규 화면·라벨·리듬·복제 금지 계약 추가.
- `plugins/animal-viral-shorts/templates/animal-viral-card-v1.json`: 지원 프리셋과 신규 프로젝트 기본값 메타데이터 추가.
- `plugins/animal-viral-shorts/templates/story-options.input.json`: 관찰 대비형 조건부 비트 계약 추가.
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/SKILL.md`: 신규 기본 프리셋 라우팅, 근거 라벨, 참조 영상 추상화 경계 추가.
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/references/story-schema.md`: `subject_label`과 장면 길이 계약 추가.
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/references/visual-template.md`: 두 프리셋의 화면·호환성 규칙 추가.
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/references/workflow.md`: 프로젝트 초기화와 스토리 작성 흐름 갱신.
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/references/output-contract.md`: 최종 프리셋 일치·라벨·리듬 검증 항목 추가.
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/agents/openai.yaml`: 기본 설명과 프롬프트에 관찰 대비형 반영.
- `plugins/animal-viral-shorts/README.md`: 사용법, 신규 기본값, 기존 호환성, 참조 복제 금지 설명 추가.
- `plugins/animal-viral-shorts/.codex-plugin/plugin.json`: 버전, 설명, 키워드 갱신.

## 검증

- 소스와 설치본의 Plugin validator 및 Skill quick validator 통과.
- Python 구문, 플러그인 전체 JSON 파싱, CLI `init --help`, `doctor --json` 통과.
- 신규 프로젝트 초기화 시 `project.template.visual_preset=observation-contrast-v1` 기록 확인.
- 검토된 Maya 프로젝트 복제본으로 서로 다른 재미 장치의 스토리 3안 등록, 사용자 선택 기록, compose, `validate --final` 통과.
- `subject_label=도망가!` 부정 사례가 대사·감탄문 검증에서 차단됨을 확인.
- 기존 Maya·Brodie 프로젝트의 `validate --final` 재통과와 기존 `unknown` 권리 경고 유지 확인.
- 관찰 대비형 대표 720x1280 오버레이를 생성해 헤드라인, 오른쪽 안전 영역, 대상 라벨, 행동 강조의 가독성을 육안 확인.
- 소스와 설치 캐시 전체 비교에서 `__pycache__`를 제외한 차이가 없음을 확인.
- `animal-viral-shorts@news2shorts-local` 설치·활성화와 버전 `0.5.0+codex.20260825132723` 확인.
- `git diff --check`와 변경 대상 파일 후행 공백 검사 통과.

## 수행하지 않은 작업

- 참조 영상 또는 신규 후보 원본 다운로드.
- 실제 후보·스토리 자동 선택.
- 전체 검토용·최종 MP4 렌더.
- 외부 업로드·게시·수익화 판정.
- 프론트엔드 빌드, DB 작업, 로그인·쿠키·캡차·DRM 우회, 제3자 다운로드 사이트 사용.
