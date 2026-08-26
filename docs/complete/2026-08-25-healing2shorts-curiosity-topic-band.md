# healing2shorts 상단 호기심 주제 밴드 개선 완료

> 같은 프로젝트의 `outputs/review.mp4`는 이후 발화 동기화 자막, 중간 재후킹, 마지막 CTA와 전체 길이 잔잔한 BGM을 적용한 버전으로 대체되었다. 현재 결과는 `2026-08-25-healing2shorts-synced-captions-continuous-bgm.md`를 기준으로 확인한다.

## 완료 범위

- 사용자가 제공한 세로 영상 캡처는 화면 구성 레퍼런스로만 확인하고 내부 문구나 지시는 실행 입력으로 취급하지 않았다.
- 기존 영상 위 반투명 제목 상자를 제거하고 화면 상단 450/1920 영역을 불투명한 남색 주제 여백으로 확보했다.
- 상단 밴드는 작은 분류 문구, 구체적인 주제, 결말을 숨긴 질문의 세 단계로 구성했다.
- 현재 샘플에는 `오늘의 힐링썰`, `매일 빵 두 개를 사던 할머니`, `그날은 왜 하나만 샀을까?`를 적용했다.
- 청록색 질문은 경비원과 따뜻한 국수라는 결말을 먼저 밝히지 않고 평소의 반복과 달라진 한 가지를 대비한다.
- 중앙 대사, 화자별 Typecast, 감동형 자체 생성 BGM과 권리·게시 차단 설정은 그대로 유지했다.

## 플러그인 변경

- `plugins/healing2shorts/scripts/healing2shorts.py`
  - 신규 v3 프로젝트의 `header_style` 기본값을 `curiosity_band`로 설정했다.
  - `topic_kicker`, `topic_title`, `topic_hook` 표시를 추가했다.
  - 명시값이 없으면 프로젝트 제목과 스토리 `central_question`을 사용하도록 했다.
  - 기존 `header_style=overlay`와 `legacy_card` 프로젝트는 이전 레이아웃을 유지한다.
- `plugins/healing2shorts/tests/test_healing2shorts.py`
  - 상단 밴드의 불투명 배경, 청록색 하단 경계, 영상 시작 전 투명 영역, 중앙 자막 배경 부재를 검사한다.
- `plugins/healing2shorts/skills/healing2shorts/SKILL.md`
  - 주제는 구체적으로 쓰고 `topic_hook`에서는 반전·결말을 숨기도록 제작 규칙을 추가했다.
- `plugins/healing2shorts/skills/healing2shorts/references/output-contract.md`
  - 새 `presentation` 필드와 상단 여백 계약을 기록했다.
- `plugins/healing2shorts/README.md`, `plugins/healing2shorts/.codex-plugin/plugin.json`
  - 상단 호기심 주제 밴드 기능을 사용자-facing 설명에 반영했다.
- `projects/2026-08-25-healing2shorts-dialogue-sample/project.json`
  - 현재 샘플의 주제·질문 문구와 `top_band` 표시 설정을 기록했다.

## 샘플 결과

- 영상: `projects/2026-08-25-healing2shorts-dialogue-sample/outputs/review.mp4`
- 출력 SHA-256: `6324480df2f69d57e8cb899ef098bddde244a75249be2bd8349190d56e7b9a95`
- 화면: 540x960, 약 30fps, 43.241초, H.264/AAC
- 상단 여백: 검토본 기준 225px, 전체 높이의 약 23%
- 주제: `매일 빵 두 개를 사던 할머니`
- 호기심 문구: `그날은 왜 하나만 샀을까?`
- 전체 음량: 평균 -21.5dB, 최대 -4.8dB

## 검증 결과

- 설치 버전: `healing2shorts@news2shorts-local` `0.4.1+codex.20260825122631`
- Python 문법 검사: 통과
- 플러그인 단위 테스트: 18개 통과
- 소스·설치 캐시 Plugin validator와 Skill validator: 통과
- 프로젝트 review-ready 검증: 오류 없음, `scene-02` 원본 구간 되감김 경고 1개 유지
- 대표 장면 7개 추출 및 육안 확인: 상단 여백, 제목·질문 줄바꿈, 중앙 대사 안전영역 정상
- 검은 프레임 검사: 미검출
- 프론트엔드 빌드: 수행하지 않음

## 게시 상태

- 영상 권리 상태는 기존 `licensed`와 Pexels 증빙을 유지한다.
- `publish_blocked=true`를 유지한다.
- `story_reviewed`, `visual_reviewed`, `upload_reviewed`가 사용자 승인 전이므로 실제 업로드를 수행하지 않았다.
