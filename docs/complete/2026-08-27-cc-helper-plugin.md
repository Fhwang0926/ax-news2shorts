# cc_helper 이슈 설명형 CapCut 초안 플러그인 구현 완료

## 작업 범위

- 저장소 마켓플레이스에 기술 식별자 `cc-helper`, 표시명 `cc_helper` 플러그인을 추가했다.
- 최근 48시간 이슈 후보를 최대 3개 제시하고 사용자 선택 전 제작을 중단하는 스킬 흐름을 추가했다.
- 선택된 이슈의 조사 자료, 7~10개 대본 단위, 15개 장면, 상단 흰색·노란색 제목, 하단 자막을 기록하는 프로젝트 계약을 추가했다.
- 기사 페이지의 `og:image`, `twitter:image`, JSON-LD, 본문 이미지와 지연 로딩·`srcset` 후보를 추출하고 대표 이미지·고해상도 본문 사진을 우선하는 수집기를 구현했다.
- 웹·로컬·생성 이미지와 로컬 영상을 등록하고, 가로·저해상도 자료를 포함해 1080×1920 PNG로 정규화하는 기능을 구현했다.
- 영상은 원본을 보존하고 대표 프레임을 장면 슬롯에 배치하며, 사람이 교체할 수 있도록 큐시트를 생성한다.
- 기본 무배경음, 내레이션 텍스트·SRT, 7개 로컬 효과음 프리셋과 배치 큐시트를 제공한다.
- 기존 CapCut `news2shorts` 프로젝트의 15장면·제목 2트랙·자막 14개 구조를 검증하고, 승인 후 원본을 보존한 새 로컬 초안을 생성하는 드라이런·복제·검증 명령을 구현했다.
- 수집 자료의 라이선스는 생성 차단 조건으로 사용하지 않되, 출처 URL·해시·합성 여부·`rights_status: unreviewed`를 기록하고 결과를 `local_review_only`, `publish_blocked`로 유지한다.

## 변경 파일

- `.agents/plugins/marketplace.json`: `cc-helper` 저장소 마켓플레이스 항목을 추가했다.
- `plugins/cc-helper/.codex-plugin/plugin.json`: 플러그인 메타데이터와 UI 표시명을 추가했다.
- `plugins/cc-helper/scripts/cc_helper.py`: `doctor`, `init`, `collect-assets`, `prepare-capcut`, `clone-capcut`, `validate` 명령을 구현했다.
- `plugins/cc-helper/skills/cc-helper/SKILL.md`: 후보 선택, 자료 수집, 그림체 변환, 승인, CapCut 인계 흐름을 정의했다.
- `plugins/cc-helper/skills/cc-helper/agents/openai.yaml`: UI 표시명, 기본 프롬프트, 자동 호출 정책을 정의했다.
- `plugins/cc-helper/skills/cc-helper/references/workflow.md`: 주제·제목·대본·에셋·사운드 규칙을 기록했다.
- `plugins/cc-helper/skills/cc-helper/references/project-contract.md`: JSON 산출물, CLI 사용법, CapCut 복제 경계를 기록했다.

기존 `plugins/news2shorts`와 `plugins/whiteboard-shorts` 파일은 이 작업에서 수정하지 않았다.

## 검증 결과

- 스킬 `quick_validate.py`: 통과
- 플러그인 `validate_plugin.py`: 통과
- `doctor --json`: Pillow, FFmpeg, FFprobe 사용 가능 확인
- 실제 템플릿 정적 검사: 1080×1920, 30fps, 6트랙, 15장면, 제목 2개, 자막 14개, 오디오 소재 0개 확인
- 임시 프로젝트 전체 흐름: `init → 로컬 이미지 15개 등록 → assets 검증 → prepare-capcut --dry-run → clone-capcut --confirm → capcut 검증` 통과
- 임시 복제 결과: 총 43초, 신규 draft UUID, 원본 템플릿 해시 불변, 목적지 재실행 차단 확인
- 복제 프로젝트의 기존 외부 이미지·원본 템플릿 경로 잔존: 0건
- 루트·타임라인의 `draft_info.json`, 백업, `template-2.tmp` 6개 파일 SHA-256 일치
- `mini_draft.json`의 전체 길이, 흰색·노란색 제목, 첫 장면, 둘째 자막의 시간과 문구 갱신 확인
- 페이지 이미지 후보 정렬: 대표 이미지와 고해상도 본문 사진 우선, 로고 SVG 제외 확인
- 로컬 MP4 등록과 대표 프레임 1080×1920 정규화 확인
- 설치 버전: `0.1.0+codex.20260827122247`
- 설치 소스와 캐시의 CLI·SKILL SHA-256 일치 확인

## 확인 한계

- 라이브 CapCut 프로젝트 폴더에는 테스트 초안을 만들지 않았다. 실제 CapCut UI에서 새 프로젝트가 표시되고 편집되는지는 첫 승인된 실사용 프로젝트에서 별도로 확인해야 한다.
- 최종 영상 렌더링, TTS, 효과음 자동 배치, 업로드와 게시 기능은 범위에 포함하지 않았다.
- 프론트엔드 빌드와 DB 작업은 수행하지 않았다.

## 무문자 시각 자료 검증 개선 및 박위 초안 수정

- CapCut 템플릿의 상단 제목과 하단 자막이 유일한 편집 문구 레이어가 되도록 스킬 규칙을 보강했다.
- 합성 이미지에 설명 문구, 날짜, 분류 라벨, 출처 문구, 로고, 워터마크, 유사 문자가 없어야 한다고 명시했다.
- `collect-assets --synthetic`로 로컬 이미지를 등록할 때 육안 확인을 나타내는 `--text-free`를 필수로 추가했다.
- 합성 에셋은 `asset-manifest.json`에 `visual_text: none`을 기록하고, 기존 프로젝트처럼 확인값이 없는 합성 에셋은 에셋 검증 단계에서 차단하도록 개선했다.
- 기존 박위 프로젝트의 문구형 사실 카드 10개가 새 검증에서 모두 차단되는 것을 확인했다.
- 장면 2, 3, 6, 7, 8, 10, 12, 13, 14, 15를 글자·숫자·로고·워터마크가 없는 비식별 편집 이미지로 교체하고 육안 검토했다.
- 에셋 검증은 오류 없이 통과했으며 권리 미검토 자료로 인한 `local_review_only` 경고와 게시 차단은 유지했다.
- 새 CapCut 수정본은 43초, 15장면, 제목 2개, 하단 자막 14개 구조로 드라이런을 완료했으며 기존 초안은 보존했다.
- 설치 버전을 `0.1.1+codex.20260827232523`으로 갱신하고 소스와 설치 캐시의 CLI·SKILL SHA-256 일치를 확인했다.
- 합성 에셋 확인값 회귀 테스트 2건, 스킬 검증, 플러그인 검증을 통과했다.
- 실제 CapCut 수정본 복제는 새 목적지 확인과 사용자 승인 후 진행하도록 대기한다.
- 프론트엔드 빌드와 DB 작업은 수행하지 않았다.

## 기존 CapCut 복사본 반영

- 사용자 요청에 따라 신규 초안을 만들지 않고 기존 복사본 `cc-20260827-222857-park-wi-seoul-ambassador-resignation`에 직접 반영했다.
- CapCut 종료 상태를 확인한 뒤 장면 2, 3, 6, 7, 8, 10, 12, 13, 14, 15의 이미지 파일만 같은 이름으로 교체했다.
- 교체 전 `cc-helper-assets` 전체를 초안 내부 `.cc-helper-backup-before-text-free-20260827-235733`에 보존했다.
- 교체 이미지 10개는 프로젝트의 검토 완료 정규화 이미지와 바이트 단위로 모두 일치한다.
- 초안의 에셋 명세와 스토리보드를 새 에셋 ID 및 `visual_text: none` 기록으로 갱신했다.
- `draft_info.json` SHA-256 `abf6a728fffe16ac40312b189e2d37d3023152e73fc02b3e4b19855227654e9e`와 `draft_meta_info.json` SHA-256 `7b8d13f8aef7a5fd22edb8f2ec1ec7021cfb32e52831f905a51d52fde4256741`가 교체 전후 동일함을 확인했다.
- 제목, 하단 자막, 장면 타이밍과 CapCut 초안 구조는 수정하지 않았다.
- 에셋 검증은 통과했으며 권리 미검토 자료로 인한 `local_review_only` 경고와 게시 차단은 유지했다.
- CapCut UI 확인, 최종 렌더링과 업로드는 수행하지 않았다.
