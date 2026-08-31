# Shorts Discovery 재미·YouTube 우선 보완 완료

## 반영 배경

- 기존 기업·기술·인터넷 48시간 탐색 결과가 보안 사고 중심으로 구성되어 재미있는 쇼츠 후보라는 의도와 어긋났다.
- YouTube API가 미설정된 실행에서 YouTube 후보가 0개였지만 일반 공개 웹 후보만으로 결과가 완성됐다.

## 완료 내용

- 새 후보에 `features.entertainment_value`와 구체적인 이유를 추가했다.
- 기존 스키마는 호환성을 유지한다.
  - 과거 입력에 재미 점수가 없으면 hook·story twist·visual clarity 평균으로 파생한다.
  - 새 조사에서는 재미 점수와 이유를 직접 기록한다.
- 전체 Discovery 점수에 Entertainment Value 10점을 추가하고 Viral Momentum을 15점, Story / Twist를 10점으로 조정해 총 가중치를 100점으로 맞췄다.
- 일반 탐색을 재미·의외성 우선으로 변경했다.
  - 재미있는 기업 대응
  - 시각적으로 이상한 기술 시연
  - 웃기거나 만족스러운 반전·정정
  - 한 문장 결말이 있는 인터넷 사건
  - 인지도가 높은 대상과 명확한 화면 변화
- 사용자가 보안을 별도로 요청하지 않으면 침해·취약점·지정학·규제 같은 무거운 후보를 최대 2개로 제한했다.
- 일반 탐색에서 YouTube를 먼저 확인하도록 했다.
  - API가 있으면 메타데이터 신호 후 브라우저 검증
  - API가 없으면 공개 YouTube Shorts 화면 직접 확인
  - 적격 YouTube 후보 최소 3개를 목표로 사용
- `validate`와 `rank`에 `--min-youtube` 옵션을 추가했다.
  - 적격 YouTube 후보만 슬롯을 확보한다.
  - 부족하면 `youtube_shortfall`을 보고하고 다른 플랫폼 후보를 억지로 YouTube 후보로 취급하지 않는다.
- shortlist Markdown에 YouTube 적격 수·부족 수와 후보별 재미 점수를 표시한다.
- 최근 48시간 공개 YouTube Shorts를 직접 확인해 재미 우선 후보 3개를 새로 생성했다.
  - `eilik-gummy-eggs-20260827`
  - `rocket-league-ai-clip-quiz-20260827`
  - `robot-games-epic-fails-20260826`
  - YouTube 적격 3개, 부족 0개, 자동 선택 없음

## 명령

```text
python3 -B plugins/shorts-suite/scripts/shorts_suite.py discover rank \
  --input <research-candidates.json> \
  --output-dir <research-output> \
  --max-age-hours 48 \
  --top-k 10 \
  --min-youtube 3
```

## 변경 파일

- `plugins/shorts-suite/scripts/discover.py`: 재미 점수, YouTube 슬롯, 부족 수 출력
- `plugins/shorts-suite/skills/shorts-discovery/SKILL.md`: 재미 우선·YouTube 필수 확인·무거운 소재 제한
- `plugins/shorts-suite/skills/shorts-discovery/references/research-workflow.md`: 재미 우선 필터와 YouTube 조사 순서
- `plugins/shorts-suite/skills/shorts-discovery/references/candidate-schema.md`: Entertainment Value 계약
- `plugins/shorts-suite/skills/shorts-discovery/references/scoring.md`: 재미 가중치와 YouTube 슬롯 계약
- `plugins/shorts-suite/skills/shorts-discovery/agents/openai.yaml`: 기본 호출 예시 갱신
- `plugins/shorts-suite/README.md`, `README.md`: 사용법과 역할 설명 갱신
- `plugins/shorts-suite/.codex-plugin/plugin.json`: 재미·YouTube 우선 기능 설명
- `projects/shorts-suite/discovery/2026-08-28-fun-youtube-48h/`: 직접 검증한 YouTube 후보 입력과 순위 결과

## 보존 경계

- 재미를 충격·피해·공포와 동일시하지 않는다.
- YouTube 후보 수를 맞추기 위해 오래되거나 미확인인 영상을 넣지 않는다.
- YouTube 검색 결과·API 신호만으로 원본·권리·화면 내용을 확정하지 않는다.
- 자동 선택, 다운로드, 대본, 렌더링, 업로드는 포함하지 않는다.
- DB·프론트엔드 변경은 없다.

## 검증 범위

- Skill 빠른 검증: 통과
- Plugin 구조 검증: 통과
- `discover.py --help`: 통과
- 기존 8개 후보 입력 호환 검증: 8개 적격, 중복·제외 없음
- 새 재미 우선 입력 검증: 3개 적격, YouTube 3개, 부족·중복·제외 없음
- 변경 파일 공백·패치 오류 검사: 통과
- 설치 버전: `0.1.0+codex.20260828130059`
- 소스와 설치 캐시의 `discover.py`, `shorts-discovery/SKILL.md` SHA-256 일치
- 설치 캐시의 Skill 빠른 검증: 통과
- 프론트엔드 빌드, 자동화 테스트, 실제 YouTube Data API 호출, 영상 렌더, 다운로드, DB 작업은 수행하지 않았다.
