# Shorts Suite 역할별 플러그인 통합 완료

## 완료 내용

- `animal-viral-shorts`, `tiktok2shorts`, `healing2shorts`, `s-finder`, `shorts-globalizer`, `shorts-studio`를 `shorts-suite` 하나로 통합했다.
- 플러그인 내부를 `discover`, `animal`, `healing`, `romance`, `globalize` 역할별 실행기와 스킬로 분리했다.
- `tiktok2shorts`와 `animal-viral-shorts`는 `animal` 역할로 합쳤다.
  - TikTok·YouTube Shorts 후보 검증과 실제 프레임 관찰, 스토리 3안, 검토·최종 렌더 흐름은 기존 Animal v2 계약을 사용한다.
  - TikTok 획득은 yt-dlp를 먼저 사용하고, 실패하면 격리된 브라우저 프로필의 TikTok 공식 공개 플레이어만 폴백으로 허용한다.
  - 별도 유지한 `whiteboard-shorts`에 검토 프로젝트를 넘길 수 있도록 사람 적합성 검토가 필요한 `whiteboard-handoff` 명령을 추가했다.
- 힐링과 로맨스 역할의 Typecast 키체인·HTTPS·WAV 검증 코드를 `scripts/core/typecast.py`로 통합했다.
- 동물 역할의 YouTube 인계 코드는 `scripts/core/youtube_delivery.py`, TikTok 공개 플레이어 코드는 `scripts/core/tiktok_public_download.py`로 통합했다.
- 공통 라우터 `scripts/shorts_suite.py`와 Typecast 보안 설정 명령 `configure-typecast`를 추가했다.
- 기존 프로젝트의 역할별 권리·승인·상태 의미는 하나의 스키마로 강제 변환하지 않고 기존 호환 읽기를 유지했다.

## 역할별 스킬

- `shorts-suite`: 요청 역할 라우팅
- `shorts-discovery`: 해외 후보·원본 추적·Korean Gap 조사
- `animal-shorts-producer`: 동물 후보 선택·관찰·스토리·렌더
- `healing-shorts-producer`: 익명·재구성 힐링 사연과 음식 영상 제작
- `romance-shorts-producer`: 승인된 2인 로맨스 드라마 제작
- `global-shorts-producer`: 한국 Shorts의 독립 출처 기반 영어권 원작 초안

## 등록 및 설치 변경

- 저장소 marketplace는 다음 4개만 유지한다.
  - `news2shorts`
  - `whiteboard-shorts`
  - `cc-helper`
  - `shorts-suite`
- 레거시 5개 설치본을 Codex 로컬 설정과 캐시에서 제거했다.
  - `tiktok2shorts`
  - `healing2shorts`
  - `s-finder`
  - `shorts-studio`
  - `shorts-globalizer`
- `animal-viral-shorts`는 기존에 미설치 상태였으며 저장소 소스만 제거했다.
- `shorts-suite@news2shorts-local` `0.1.0+codex.20260828045604`를 설치했다.

## 제거한 소스

- `plugins/animal-viral-shorts`
- `plugins/tiktok2shorts`
- `plugins/healing2shorts`
- `plugins/s-finder`
- `plugins/shorts-globalizer`
- `plugins/shorts-studio`

삭제 전 현재 작업 트리 내용을 `/private/tmp/shorts-suite-legacy-backup.Hm7u1v`에 복사했다. 기존 `projects/`와 `outputs/` 결과물은 삭제하지 않았다.

## 변경 파일

- `.agents/plugins/marketplace.json`: 레거시 6개 항목을 제거하고 `shorts-suite` 등록
- `README.md`: 현재 4개 플러그인 구조로 목록 갱신
- `plugins/shorts-suite/.codex-plugin/plugin.json`: 신규 통합 플러그인 manifest
- `plugins/shorts-suite/README.md`: 역할·명령·제외 범위 안내
- `plugins/shorts-suite/scripts/`: 역할별 실행기, 라우터, 공통 코어
- `plugins/shorts-suite/skills/`: 라우터와 역할별 5개 스킬
- `plugins/shorts-suite/templates/animal/`: 동물 후보·관찰·스토리·화면 템플릿
- `plugins/shorts-suite/tests/`: 이관된 역할별 회귀 테스트와 fixture

## 검증 결과

- Plugin validator: 통과
- 6개 Skill validator: 모두 통과
- 공통 라우터의 `discover`, `animal`, `healing`, `romance`, `globalize`, `configure-typecast` 도움말 로딩: 모두 종료 코드 0
- 설치 캐시와 소스의 대표 실행기·라우터 스킬 SHA-256: 일치
- 설치 목록: `news2shorts`, `whiteboard-shorts`, `cc-helper`, `shorts-suite`만 활성 상태
- 레거시 설치 캐시 디렉터리: 제거 확인

자동화 테스트, 프론트엔드 빌드, 영상 렌더, 외부 다운로드, DB 작업, 업로드는 수행하지 않았다.

## 보존 경계

- `cc-helper`, `news2shorts`, `whiteboard-shorts`의 기존 소스 변경은 수정하지 않았다.
- 과거 프로젝트 데이터와 렌더 결과는 그대로 보존했다.
- 기존 프로젝트의 성공 기록은 새 `shorts-suite` 런타임 검증으로 간주하지 않는다.
- 새 스킬과 설치본을 Codex에서 확인하려면 새 작업을 열어야 한다.
