# Shorts Suite Guided·Whiteboard·Senior 완전 통합 완료

## 완료 범위

- `shorts-suite`를 신규 쇼츠 제작의 단일 플러그인으로 확장했다.
- `whiteboard-shorts`의 CLI, Skill, 템플릿, reference, 고정 vendor 렌더러, 라이선스·수정 고지를 Shorts Suite 내부 `whiteboard` 역할로 이전했다.
- `senior-shorts`의 CLI, Skill, 스타일 프리셋, 대본·후보 템플릿과 reference를 Shorts Suite 내부 `senior` 역할로 이전했다.
- `shorts_suite.py`에 `guided`, `whiteboard`, `senior` 역할을 추가했다.
- 공통 `guided` 오케스트레이터에 `init`, `options`, `select`, `produce`, `approve`, `status`, `finalize` 명령을 추가했다.
- 신규 작업은 `source → script → image → voice → render` 순서로 고정했다.
- 각 단계는 모든 실제 선택 가능 옵션과 설명을 기록하고, 사용자 선택·결과 파일 SHA-256·승인 결정을 묶는다.
- 상위 단계 옵션이나 결과가 변경되면 이후 승인을 `invalidated`로 바꾸고 기존 파일과 workflow 스냅샷을 `revisions/`에 보존한다.
- 합성 이미지 승인은 합성 고지 확인을 요구하고, 음성 제공자 실패 시 다른 제공자로 자동 대체하지 않도록 Skill 계약을 고정했다.
- 렌더 승인은 깨끗한 최종본 생성 권한과 분리했다. `finalize`는 렌더 승인, publishable 권리, 합성 고지, `--confirm-clean-render`, 프로젝트 내부 MP4를 모두 요구한다.
- `unknown`, `unreviewed`, `review_required`, `transformative_review`, `not_permitted` 권리 상태는 깨끗한 최종본을 차단한다.
- YouTube 키 조회는 `YOUTUBE_API_KEY`, `shorts-suite.youtube-data-api-key`, 기존 `senior-shorts.youtube-data-api-key` 순으로 호환한다.
- Whiteboard의 중복 `youtube_delivery.py`는 더 많은 호환 기능이 있는 Shorts Suite 공통 모듈로 통합했다.
- 신규 기본 Skill `guided-shorts-producer`를 추가하고 기존 Whiteboard·Senior Skill은 레거시 프로젝트 호환용으로 제한했다.

## 옵션 계약

- 소스: 제작 역할, YouTube·공개 웹·사용자 URL·로컬 파일·시니어 독립 창작, 현재 탐색 배치의 적격 후보 최대 10개
- 대본: 역할이 생성한 모든 유효 안 또는 역할별 구조 프리셋
- 이미지: 원본·사용자 자산, Whiteboard grid/skeleton·contour-wipe/brush, Senior ImageGen/ComfyUI, 기존 역할 프리셋
- 음성: 설정된 Typecast, 설치된 한국어 macOS 음성, 사용자 파일, 권리 확인 소스 음성, 역할이 허용하는 음성 없음
- 렌더: 역할 렌더러, calm/standard/dynamic, 자막 스타일, 음악, 검토 해상도

옵션은 설명 후 선택하며 선택되지 않은 옵션의 실제 샘플을 생성하지 않는다. `recommended`는 자동 선택이 아니다.

## 호환성과 제거

- 기존 Whiteboard 프로젝트는 `python3 plugins/shorts-suite/scripts/shorts_suite.py whiteboard ...`로 읽는다.
- 기존 Senior 프로젝트는 `python3 plugins/shorts-suite/scripts/shorts_suite.py senior ...`로 읽는다.
- 기존 프로젝트 JSON과 결과물은 변환하거나 삭제하지 않았다.
- `whiteboard-shorts@news2shorts-local`, `senior-shorts@news2shorts-local` 설치를 제거했다.
- 마켓플레이스에서 두 항목을 제거했다.
- 새 Shorts Suite 설치와 소스·캐시 일치를 확인한 뒤 `plugins/whiteboard-shorts`, `plugins/senior-shorts` 소스 폴더를 제거했다.
- 통합된 파일은 `plugins/shorts-suite`에 남고, 기존 tracked Whiteboard 파일은 Git에서도 복구할 수 있다.

## 설치 버전

- `shorts-suite@news2shorts-local`: `0.1.0+codex.20260829045423`
- `cc-helper@news2shorts-local`: `0.1.2+codex.20260829045423`

## 변경 영역

- `plugins/shorts-suite`: guided 오케스트레이터, 통합 역할·Skill·자산·문서·manifest
- `.agents/plugins/marketplace.json`: Whiteboard·Senior 항목 제거
- `plugins/cc-helper/skills/cc-helper/SKILL.md`: Whiteboard 통합 경로 갱신
- `README.md`: 단일 Shorts Suite 플러그인 목록과 설명 갱신
- `docs/complete/2026-08-29-shorts-suite-guided-whiteboard-senior-consolidation.md`: 통합·검증·호환 기록

## 검증 경계

- Shorts Suite와 cc-helper Plugin validator를 통과했다.
- Shorts Suite의 모든 Skill과 cc-helper Skill validator를 통과했다.
- 통합 플러그인 JSON 파일을 파싱했다.
- Guided·Whiteboard·Senior CLI 도움말을 확인했다.
- 기존 Senior 프로젝트를 새 `shorts_suite.py senior status` 명령으로 읽었다.
- Shorts Suite와 설치 캐시의 manifest, guided, whiteboard, senior, 공통 YouTube 인계, Skill, vendor 자산 SHA-256 일치를 확인했다.
- 실제 guided 신규 프로젝트 생성·단계 거부·렌더·외부 API·업로드는 실행하지 않았다.
- 사용자 지침에 따라 단위 테스트, 프론트엔드 빌드, DB 작업을 수행하지 않았다.
