# healing2shorts 스토리 품질·저해상도 검토본 개선 완료

## 완료 범위

- 신규 스토리 후보 계약을 v2로 올리고 요약형 6비트 대신 사건·질문·단서·새 사실의 반전이 이어지는 가변 7비트를 기본으로 적용했다.
- 재미 점수와 출처·민감도 검증을 분리했다. 출처가 안전하다는 이유만으로 재미없는 후보가 BEST가 되지 않으며, 신규 후보의 최고점이 70점 미만이면 후보 재조사를 요구한다.
- 검토본을 540x960, CRF 23으로 낮추고 최종본과 편집 패키지는 720x1280을 유지했다.
- 각 장면 시작의 1프레임 검은 페이드를 제거해 장면 경계를 직결 컷으로 바꿨다.
- 기존 v1 후보와 6비트 프로젝트는 다시 열고 렌더할 수 있도록 호환성을 유지했다.
- 설치본을 `healing2shorts@news2shorts-local 0.3.0+codex.20260824150737`로 갱신했다.

## 스토리 계약 v2

- 지원 엔진: `missing_routine`, `object_mystery`, `misunderstanding_reveal`, `quiet_sacrifice`, `returned_promise`
- 필수 비트: `cold_open`, `setup`, `problem`, `clue`, `escalation`, `reveal`, `afterglow`
- 첫 장면: 2–3초, 답을 먼저 밝히지 않는 구체적 질문 또는 이상 징후
- 나머지 장면: 각각 3–8초, 전체 30–45초
- 기사형은 모든 비트가 claim ID를 참조하고 `reveal`에 `cold_open`에서 쓰지 않은 새 claim이 있어야 한다.
- 재미 점수: 훅·열린 질문 20, 인물·사건 15, 긴장 진행 20, 반전·회수 25, 구어체 자연스러움 10, 음식 동작 연결 10
- 출처, claim 연결, 사연 동의·비식별화, 민감 주제는 점수 가산이 아닌 별도 검증 게이트다.

## 변경 파일

- `plugins/healing2shorts/scripts/healing2shorts.py`: v2 후보·점수·반전 claim 검증, 가변 7비트 길이 배분, 검토·최종 렌더 프로필 분리, 장면 경계 검은 페이드 제거를 반영했다.
- `plugins/healing2shorts/tests/test_healing2shorts.py`: v2 기사형·익명 사연형, 30/36/45초 길이 경계, 70점 미만 BEST 차단, 새 claim 반전, 렌더 프로필, v1 호환 테스트를 추가했다.
- `plugins/healing2shorts/skills/healing2shorts/SKILL.md`: 신규 후보 제작 흐름과 BEST 기준, 540x960 검토본을 반영했다.
- `plugins/healing2shorts/skills/healing2shorts/references/story-patterns.md`: 다섯 스토리 엔진, 7비트 작성 규칙, 음식 동작 연결, 공식 참고 자료와 적용 한계를 추가했다.
- `plugins/healing2shorts/skills/healing2shorts/references/candidate-contract.md`: v2 후보·점수·claim 계약과 v1 호환 경계를 기록했다.
- `plugins/healing2shorts/skills/healing2shorts/references/output-contract.md`: 검토본 540x960, 최종본·편집 클립 720x1280 계약을 기록했다.
- `plugins/healing2shorts/skills/healing2shorts/templates/story-candidates.template.json`: 신규 템플릿 버전을 2로 변경했다.
- `plugins/healing2shorts/skills/healing2shorts/agents/openai.yaml`: 사건·반전 중심 기본 호출 문구를 반영했다.
- `plugins/healing2shorts/.codex-plugin/plugin.json`: 설치 버전과 기능 설명을 갱신했다.
- `plugins/healing2shorts/README.md`: 신규 스토리 구조와 해상도 분리를 문서화했다.
- `projects/2026-08-24-healing2shorts-story-03/outputs/review.mp4`: 기존 선택 프로젝트를 새 540x960 검토 프로필로 다시 렌더했다.
- `projects/2026-08-24-healing2shorts-story-03/project.json`, `render-report.json`, `publish.json`, `youtube-upload.json`, `youtube-upload.md`, `edit-package/`: 재렌더 결과와 게시 차단 상태를 갱신했다.

## 참고한 공식 자료

- YouTube 공식 블로그의 첫 1초 훅과 미니 스토리 안내
- YouTube 도움말의 초반 기대 충족, 기대·호기심 유지 안내
- TikTok Creative Codes와 Storytelling Formats의 hook/body/close, 초반 서스펜스, 장면 변화 구조

TikTok 자료는 광고 크리에이티브 가이드이므로 유기적 Shorts의 바이럴 보장 근거로 사용하지 않고 구조 참고로만 반영했다.

## 검증 결과

- Plugin validator: 통과
- Skill quick validator: 통과
- Python 구문 검사: 통과
- 표준 라이브러리 단위 테스트 10개: 통과
- manifest·스토리 템플릿 JSON 검사: 통과
- 기존 v1 기사 fixture 호환: 통과
- 실제 `story-03 + food-01` 재렌더: 42.021초, 540x960, 30fps, H.264/AAC
- 대표 시작·종료 프레임 시각 확인: 자막 안전 영역과 세로 크롭 정상
- FFmpeg blackdetect: 장면 경계와 종료 구간에서 검은 프레임 미검출
- 설치 상태: `healing2shorts@news2shorts-local 0.3.0+codex.20260824150737` installed, enabled
- 프론트엔드 빌드: 수행하지 않음

## 증명 경계

- 기존 `story-03`의 문구는 자동으로 덮어쓰지 않았다. 새 재미 규칙은 신규 후보 생성부터 적용되며, 기존 이야기를 v2로 다시 쓰려면 새 후보 버전으로 별도 제작한다.
- 현재 실행에서는 Typecast 키체인 확인이 제한되어 신규 음성 API 호출 준비 상태는 false였다. 실제 재렌더는 기존 프로젝트에 저장된 Typecast 음원 6개를 재사용했다.
- 검토본 재렌더와 정적 검증은 게시 권리, 사실성, 플랫폼 승인, 수익화 또는 조회수 성과를 보장하지 않는다.
- 영상 권리 검증, 중국어 구간 제외, 도우인 페이지·CDN 다운로드 차단은 그대로 유지했다.
