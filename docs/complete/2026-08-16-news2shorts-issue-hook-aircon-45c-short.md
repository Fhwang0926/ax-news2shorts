# news2shorts 이슈형 후크 개선 및 45도 에어컨 쇼츠 완료

## 플러그인 개선

- 사실에 근거한 논쟁·생활상 손해를 첫 문장에 제시하는 `issue-tension` 후크 유형을 추가했다.
- 과감한 훅을 사용하더라도 의미를 바꾸는 조건이나 반전은 첫 근거 장면에서 바로 공개하도록 스킬 규칙을 보강했다.
- 확인되지 않은 비난, 공포, 긴급성, 억지 공유 문구는 허용하지 않고 실용적인 결론으로 공유 가치를 만들도록 했다.
- 플러그인 버전을 `0.6.4+codex.20260816`으로 올리고 Codex 설치 캐시를 갱신했다.

## 제작 결과

- 참고 주제: KBS News `45도 넘으면 소용없다는 한국 에어컨…진실은?`
- 제작 포맷: `quick-reveal`
- 선택 후크: `45도면 한국 에어컨, 진짜 전부 장식품 됩니다?`
- 최종 결론: 45도는 모든 국내 에어컨의 일괄 중단선이 아니며, 폭염에서는 모델별 운전 범위와 실외기 열 배출 상태가 실제 냉방 성능을 좌우한다.
- KBS 영상, 음원, 썸네일, 자막은 사용하지 않았다.
- 공식 시험기준, 삼성전자 제품 자료, LG전자 고객지원, 한국에너지공단 가이드로 핵심 주장을 교차검증했다.
- 검색 결과의 자산별 상업 이용 조건과 스타일 일관성을 확보하기 어려워, 서로 다른 7개의 프로젝트 소유 평면 픽토그램을 720x1280으로 제작했다.
- 화면에는 합성 이미지 표시를 유지하고 권리 매니페스트에 제작 방식과 검색 판단을 기록했다.

## 산출물

- 프로젝트: `projects/2026-08-16-aircon-45c-factcheck/`
- 검토본: `projects/2026-08-16-aircon-45c-factcheck/preview.mp4`
- 최종본: `projects/2026-08-16-aircon-45c-factcheck/short.mp4`
- 대본: `projects/2026-08-16-aircon-45c-factcheck/script.md`
- 스토리보드: `projects/2026-08-16-aircon-45c-factcheck/storyboard.json`
- 출처·팩트·권리 기록: `sources.json`, `fact-sheet.json`, `rights-manifest.json`

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: `issue-tension` 후크 유형 허용
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 과감한 이슈형 후크의 작성·회수 규칙 추가
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`: 이슈 긴장형 정의와 선택 기준 추가
- `plugins/news2shorts/README.md`: 새 후크 전략 설명 반영
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전과 기능 설명 갱신
- `projects/2026-08-16-aircon-45c-factcheck/`: 신규 쇼츠 프로젝트와 결과물 추가

## 확인 결과

- Python 구문 검사 통과
- Skill `quick_validate.py` 검사 통과
- 설치 버전 `news2shorts@news2shorts-local` `0.6.4+codex.20260816` 확인
- Typecast 키체인과 고정 Voice ID `tc_61f0859907085fc68561c9a1` 인식 확인
- 최종 프로젝트 검증 오류 0건
- 최종 MP4: 28.75초, 720x1280, H.264/AAC, 48kHz 모노, 하드 컷
- 알려진 경고: 발행일을 정확히 확인할 수 없는 공식 자료 2건은 날짜를 비워 두었고, 모든 장면이 생성 픽토그램이라는 검토 경고를 유지했다.

## 범위

- YouTube 업로드와 게시 작업은 수행하지 않았다.
- 데이터베이스 작업과 프론트엔드 빌드는 수행하지 않았다.
