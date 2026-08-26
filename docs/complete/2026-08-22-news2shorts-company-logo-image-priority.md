# news2shorts 기업 로고·실제 이미지 우선 적용

## 완료 일자

- 2026-08-22

## 반영 범위

- 대본과 화면 문구에 특정 기업이 핵심 당사자로 등장하는지 시각자료 수집 전에 검토하도록 변경했다.
- 뉴스 매체명, 출처 표시, 단순 비교에 잠깐 등장하는 기업은 강제 대상에서 제외했다.
- 핵심 기업은 첫 주요 언급 장면에 권리 승인된 실제 로고 또는 직접 관련 기업 이미지를 최소 1회 사용하도록 했다.
- 허용 기업 자료 유형은 `logo`, `official-image`, `licensed-photo`, `branded-product`, `facility-signage`로 제한했다.
- 회사 홈페이지나 보도자료에 공개됐다는 이유만으로 사용하지 않고, 자산별 상업 이용 또는 편집 이용 근거와 표시 조건을 확인하도록 했다.
- AI로 기업 로고를 재현하거나 유사 로고를 만드는 것을 최종 검증에서 차단했다.
- 권리 안전한 기업 자료를 구하지 못하면 일반 업종 이미지로 대체하지 않고 최종 렌더를 중단해 권리 장애를 보고하도록 했다.

## 프로젝트 계약

- 새 프로젝트 버전을 6으로 올렸다.
- `visual_sourcing.company_visuals.mentions_reviewed`로 기업명 검토 완료 여부를 기록한다.
- `visual_sourcing.company_visuals.companies`에 핵심 기업의 정확한 이름과 첫 주요 언급 `scene_ids`를 기록한다.
- 사용한 기업 자산의 권리 기록에는 `company_names`, `company_visual_type`, `company_identity_reviewed: true`를 기록한다.
- 기존 version 5 이하 프로젝트는 새 필드 없이 기존 검증과 렌더 흐름을 유지한다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
  - version 6 기업 시각자료 계약, 기업별 장면 연결, 자산 유형·식별 검수, 생성형 로고 금지, 최종 차단 검사를 추가했다.
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`
  - version 6과 기본 `company_visuals` 검토 필드를 추가했다.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
  - 핵심 기업 추출, 첫 주요 언급 배치, 권리 확인, AI 로고 금지와 권리 장애 처리 절차를 추가했다.
- `plugins/news2shorts/skills/news2shorts/references/rights-policy.md`
  - 기업 로고·브랜드 이미지의 허용 출처, 상표 표시, 기록 필드와 금지 사항을 정의했다.
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
  - version 6 프로젝트 및 권리 매니페스트 계약을 문서화했다.
- `plugins/news2shorts/skills/news2shorts/agents/openai.yaml`
  - 기본 요청에 핵심 기업 실이미지 사용 조건을 반영했다.
- `plugins/news2shorts/README.md`
  - 사용자용 기능 목록과 시각자료 안내를 갱신했다.
- `plugins/news2shorts/.codex-plugin/plugin.json`
  - 버전을 `0.24.0+codex.20260822200509`로 올리고 기능 설명을 갱신했다.

## 검증 결과

- Python AST와 플러그인·템플릿 JSON 파싱 통과
- Skill Creator 원본·설치본 구조 검사 통과
- CLI 도움말 실행 통과
- 새 프로젝트 초기화 시 project version 6과 `company_visuals` 기본 필드 생성 확인
- 핵심 기업은 선언했지만 연결된 기업 자산이 없는 최종 프로젝트 검증 실패 확인
- 기업명·유형·식별 검수를 기록한 사용 자산이 첫 주요 언급 장면에 있을 때 최종 검증 통과 확인
- 기업 자산을 합성 이미지로 표시했을 때 최종 검증 실패 확인
- 기존 version 5 카드 리볼빙 프로젝트가 수정 없이 최종 검증을 통과해 하위 호환 확인
- 후행 공백 검사 통과
- `news2shorts@news2shorts-local` `0.24.0+codex.20260822200509` 설치·활성화 확인
- 작업본과 설치 캐시의 Skill, 렌더러, 프로젝트 템플릿 SHA-256 일치 확인

## 수행하지 않은 작업

- 새 뉴스 영상이나 MP4를 렌더링하지 않았다.
- Typecast API 호출과 YouTube 업로드·게시를 수행하지 않았다.
- DB 작업과 프론트엔드 빌드는 대상이 아니므로 수행하지 않았다.
