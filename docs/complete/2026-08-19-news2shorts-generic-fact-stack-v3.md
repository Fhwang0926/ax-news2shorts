# news2shorts 범용 팩트스택 v3 개선 완료

## 요청

- 기존 팩트스택의 긴 나열식 전개와 약한 결론을 플러그인 수준에서 개선한다.
- 특정 추석지원금 영상의 문구나 숫자에 종속되지 않고 이후 모든 뉴스 주제에 적용되는 규칙으로 재정의한다.

## 범용 계약

- 새 팩트스택은 `storyboard.json` version 3을 사용한다.
- 서로 다른 검증 주장과 근거 장면이 각각 최소 3개 있어야 하며, 각 장면은 `claim_ids`로 `fact-sheet.json`에 직접 연결한다.
- 근거 장면만 `fact_index`를 사용하고 `1/N`부터 `N/N`까지 빠짐없이 이어지게 한다.
- 각 근거 장면에 `evidence_kind`와 `evidence_label`을 기록하고, 숫자·비교 근거에는 `evidence_value`를 필수로 둔다.
- 중간 `turn` 또는 `rehook`은 전체 길이의 35~70%에 배치하고 앞선 주장을 반복하지 않는 새 조건이나 해석을 추가한다.
- 마지막 결론에는 `payoff_callback`을 넣어 첫 후크의 질문과 검증된 답을 직접 연결한다.
- 검증 주장이 3개 미만이면 내용을 늘리지 않고 `quick-reveal`로 전환한다.
- 기존 version 1~2 스토리보드는 새 필드 없이도 기존 방식으로 렌더하고 검사한다.

## 구현

- 팩트 번호, 근거 라벨·값, 정확 구문 강조를 보여주는 팩트스택 전용 근거 카드를 추가했다.
- 사진·문서처럼 별도 숫자가 없는 근거도 자막을 핵심 값으로 사용해 카드가 사라지지 않게 했다.
- 마지막 결론 카드 위에 후크 회수 문구를 별도 계층으로 배치하고, 질문형 보조 문구가 있을 때도 카드와 겹치지 않게 했다.
- 긴 고정 헤드라인은 두 줄 폭을 균형 있게 나눠 짧은 고아 줄이 생기지 않도록 했다.
- 팩트 번호 누락·중복·건너뜀, 존재하지 않는 주장 참조, 근거 유형 불일치, 너무 이른 답 공개, 정지 이미지·동일 근거 유형 반복을 검사한다.
- 렌더 보고서에 팩트 번호, 주장 ID, 근거 종류·라벨·값, 결론 콜백을 기록해 결과를 추적할 수 있게 했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 범용 v3 검증, 팩트스택 화면 계층, 균형 헤드라인, 렌더 보고서 필드 추가
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`: 팩트 번호 화면 표시 기본값 추가
- `plugins/news2shorts/skills/news2shorts/templates/storyboard.template.json`: version 3과 주장·근거·결론 콜백 필드 추가
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 세 주장 게이트와 범용 v3 제작 절차 추가
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`: 번호형 근거 누적, 중간 전환, 결론 회수 규칙 추가
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`: 팩트 카운터·근거 카드·콜백 화면 계약 추가
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: v3 필드와 하위 호환성, 렌더 보고서 계약 추가
- `plugins/news2shorts/skills/news2shorts/references/reference-formats.md`: 범용 팩트스택 선택 기준 갱신
- `plugins/news2shorts/README.md`: 새 팩트스택 동작과 포맷 라우팅 설명 추가
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전 `0.17.0+codex.20260819`과 설명 갱신
- 현재 Codex 플러그인 설치본을 `0.17.0+codex.20260819`로 갱신

## 검증

- 기존 version 2 프로젝트의 초안 검증 통과: 오류 0건, 새 v3 필수 필드 오류 없음
- version 3 통합 프로젝트의 최종 검증 통과: 오류 0건, 정지 근거 장면 품질 경고만 확인
- 정상·누락·조기 결론 시나리오로 범용 계약 검사 통과
- 근거 카드와 결론 카드 프레임을 직접 렌더해 팩트 번호, 강조, 카드 간 겹침, 출처 표시를 시각 확인
- Skill 구조 검사, JSON 파싱, CLI 도움말, 소스와 설치본 일치 여부를 확인
- 프론트엔드 빌드, DB 작업, 기존 영상 재렌더, YouTube 업로드·게시 작업은 수행하지 않음
