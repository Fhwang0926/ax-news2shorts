# news2shorts 퀵리빌 훅·이미지·결론 개선 완료

## 요청

- 첫 화면의 숫자가 왜 중요한지 즉시 이해되는 임팩트 훅으로 개선한다.
- 결론 카드의 작은 보조 문구를 크게 하고 다른 문구와 겹치지 않게 한다.
- 확인된 사실 범위에서 공공 영향과 논쟁 지점을 더 심각하고 선명하게 구성한다.
- 퀵리빌 핵심 장면에 기사 주장과 직접 관련된 이미지만 사용한다.

## 범용 개선

- 새 프로젝트를 version 3으로 올리고 `shorts_profile.hook_stake`를 추가했다.
- 새 퀵리빌은 첫 숫자·주장의 의미를 `hook_stake`에 출처가 있는 한 문장으로 기록한다.
- 첫 화면과 첫 내레이션이 `hook_stake`의 의미 있는 단어를 공유하고, 첫 장면이 실제 `claim_ids`와 연결돼야 최종 검수를 통과한다.
- 논란성은 확인된 실패 기대, 공공 비용, 지연, 공백, 부담, 책임 질문으로 만들고 출처에 없는 비난·분노·합의를 생성하지 않게 했다.
- 새 퀵리빌의 모든 이미지·클립에 `relevance_level`과 `relevance_note`를 요구한다.
- 훅·근거·반전·영향·결론 장면은 실제 인물, 사건, 대상, 문서, 메커니즘과 직접 일치하는 `direct` 자산만 허용한다. 도시 풍경이나 업종 분위기만 맞는 `contextual` 자산은 맥락 장면에만 허용한다.
- 수집한 비합성 자산은 퀵리빌에서 장면별 기사 연관성 육안 검수를 필수로 했다.
- 결론 카드의 답, 의미, 구분선, 마지막 질문을 서로 다른 세로 영역에 배치했다.
- 결론 제목은 최대 72px, 의미 문구는 최대 56px, 질문은 최대 66px로 확대해 720p에서도 작은 각주처럼 보이지 않게 했다.
- 기존 project version 1~2 퀵리빌은 새 필드 없이도 이전 방식으로 검증·렌더할 수 있게 유지했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 퀵리빌 훅 의미·첫 주장 연결·장면별 이미지 연관성 검증과 결론 카드 고정 영역·큰 글자 적용
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`: project version 3과 `hook_stake` 기본 필드 추가
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 퀵리빌 제작·논란 구성·직접 연관 이미지 규칙 추가
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`: 숫자 훅의 의미 연결과 사실 기반 긴장 규칙 추가
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`: 결론 카드 큰 글자 분리 영역과 퀵리빌 직접 이미지 계약 추가
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: `hook_stake`, 이미지 연관성 메타데이터와 version 3 검증 계약 추가
- `plugins/news2shorts/skills/news2shorts/references/rights-policy.md`: `direct`·`contextual` 판정과 장면별 연관성 검수 기준 추가
- `plugins/news2shorts/README.md`: 사용자용 퀵리빌 동작 설명 갱신
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전 `0.18.0+codex.20260819`과 설명 갱신
- `docs/complete/2026-08-19-news2shorts-quick-reveal-stake-visual-payoff.md`: 당일 작업 완료 기록

## 검증

- Python CLI 도움말 실행과 JSON 파싱 통과
- Skill Creator 구조 검사 통과
- 기존 project version 2 신안군 퀵리빌 초안 검증: 오류 0건, 경고 0건으로 하위 호환 확인
- 같은 프로젝트의 임시 version 3 복사본에서 `hook_stake` 누락과 자산 연관성 메타데이터 누락이 초안 경고, 최종 오류가 되는 것을 확인
- 무음 임시 렌더의 결론 프레임을 직접 확인해 큰 보조 문구, 큰 질문, 문구 간 간격, 카드 밖 출처 표시가 겹치지 않음을 확인
- 소스 플러그인과 설치 캐시의 전체 파일 비교 일치
- 설치본 `news2shorts@news2shorts-local` 버전 `0.18.0+codex.20260819`, installed/enabled 확인
- 프론트엔드 빌드, DB 작업, 기존 사용자 영상 재렌더, YouTube 업로드·게시 작업은 수행하지 않음
