# Shorts Suite

`shorts-suite`는 신규 쇼츠를 `소스 → 대본 → 이미지 → 음성 → 렌더` 순서로 제작하며 매 단계에서 사용자 옵션 선택과 결과 승인을 요구하는 로컬 Codex 플러그인입니다.

## 신규 작업 기본 흐름

```text
python3 -B scripts/shorts_suite.py guided init --project-dir <new-project> --mode auto
python3 -B scripts/shorts_suite.py guided options --project-dir <project> --stage source
python3 -B scripts/shorts_suite.py guided select --project-dir <project> --stage source --option production_mode=... --option source_input=...
python3 -B scripts/shorts_suite.py guided produce --project-dir <project> --stage source --producer-role <role> --artifact <file>
python3 -B scripts/shorts_suite.py guided approve --project-dir <project> --stage source --decision approve --result-sha256 <digest>
```

같은 `options → select → produce → approve` 순서를 `script`, `image`, `voice`, `render`에 반복합니다. 옵션 파일은 현재 선택 가능한 모든 항목의 설명, 적합 용도, 장단점, 입력, 시간·비용, 권리 영향과 추천 여부를 포함합니다. 추천은 자동 선택되지 않습니다.

검토 렌더 승인 후 역할 렌더러가 만든 깨끗한 MP4를 확정합니다.

```text
python3 -B scripts/shorts_suite.py guided finalize \
  --project-dir <project> \
  --artifact <project-relative-final.mp4> \
  --confirm-clean-render
```

권리 상태가 `owned`, `licensed`, `permission_confirmed`, `public_domain`, `official_press_asset` 중 하나가 아니면 깨끗한 최종본을 차단합니다. 합성 자산은 이미지 승인 단계에서 합성 고지를 확인해야 합니다. 실제 업로드는 수행하지 않습니다.

## 통합 역할

- `guided`: 모든 신규 작업의 5단계 승인 오케스트레이터
- `discover`: 재미·의외성 우선 공개 후보와 Korean Gap 조사
- `package`: 선택 Candidate ID의 출처·주장·에셋·대본 패키징
- `whiteboard`: 기존 Whiteboard 프로젝트와 손그림 렌더러 호환
- `senior`: 기존 Senior Storytoon 프로젝트와 렌더러 호환
- `animal`: 검증된 동물 원본 기반 제작
- `healing`: 익명·창작 힐링 대화와 음식 영상 제작
- `romance`: 승인된 2인 로맨스 드라마 제작
- `globalize`: 한국 Shorts 신호의 독립 영어권 재구성

```text
python3 -B scripts/shorts_suite.py <role> --help
```

직접 역할 명령은 기존 프로젝트 호환용입니다. 신규 프로젝트는 `guided`를 사용합니다.

## 단계별 옵션

- 소스: YouTube 공개 후보, 공개 웹, 사용자 URL, 로컬 파일, 시니어 독립 창작과 현재 배치의 모든 적격 Candidate ID
- 대본: 선택 역할이 생성한 모든 유효 방향과 역할별 구조 프리셋
- 이미지: 원본 프레임, 사용자 자산, Whiteboard grid/skeleton·contour-wipe/brush, Senior ImageGen/ComfyUI, 역할별 프리셋
- 음성: 설정된 Typecast, 설치된 한국어 macOS 음성, 사용자 파일, 권리 확인 소스 음성, 역할이 허용하는 음성 없음
- 렌더: 역할 렌더러, 편집 속도, 자막, 음악, 검토 해상도

선택되지 않은 옵션의 실제 샘플은 생성하지 않습니다. 결과가 거절되거나 상위 단계가 변경되면 이후 승인은 무효화하고 기존 파일은 `revisions/` 기록과 함께 보존합니다.

## YouTube API

`shorts-discovery`는 공개 메타데이터를 후보 신호로 사용할 수 있습니다. API 키는 `YOUTUBE_API_KEY`, `shorts-suite.youtube-data-api-key` 키체인, 기존 `senior-shorts.youtube-data-api-key` 키체인 순으로 확인하며 값을 출력하지 않습니다.

```text
python3 -B scripts/shorts_suite.py discover configure-youtube
python3 -B scripts/shorts_suite.py discover doctor --check-youtube --json
```

API 결과는 `discovery_lead`일 뿐이며 실제 화면, 원출처, Korean Gap과 권리를 브라우저에서 별도로 확인해야 합니다.

## 이전 Whiteboard 자산

고정된 `srt-whiteboard-animation` 업스트림과 수정된 손 자산은 `vendor/`에 포함됩니다. 라이선스와 수정 내역은 `THIRD_PARTY_NOTICES.md`와 `UPSTREAM.md`를 유지합니다. 공통 YouTube 인계 기능은 `scripts/core/youtube_delivery.py` 한 곳에서 관리합니다.

## 검증 경계

로컬 JSON·Skill·manifest 검증이나 MP4 렌더 성공은 사실 정확성, 원본 사용 권리, 플랫폼 승인, 수익화 또는 게시 허가를 증명하지 않습니다. 사용자 단계 승인은 콘텐츠 적합성 결정이며 권리 허가를 대신하지 않습니다.
