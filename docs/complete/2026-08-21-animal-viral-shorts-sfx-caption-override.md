# Animal Viral Shorts 효과음·한국어 원문 번역 개선 완료

## 작업 범위

- `Animal Viral Shorts`를 `0.4.0+codex.20260821`로 올렸다.
- 장면별 `question_pop`, `soft_whoosh` 비보컬 효과음을 생성해 원본음·BGM과 함께 믹스할 수 있게 했다.
- 영어 원본 자막이 실제로 표시되는 시간에만 불투명 `원문 번역` 한국어 카드를 표시하도록 했다.
- 번역 카드는 원본 영상 영역과 오른쪽 UI 안전 영역 안에 있어야 하며, `reviewed_safe`와 `not_observation`를 필수로 검증한다.
- 렌더 보고서와 편집 계획에 효과음 시점과 번역 오버라이드 수를 기록한다.

## 적용 프로젝트

- `projects/2026-08-21-maya-what-the-fluff-animal-short`
- 2.0초: 담요가 내려간 직후 `question_pop` 효과음
- 10.5초: 침대에서 내려가는 전환에 `soft_whoosh` 효과음
- 영어 원문 5구간: `wait`, `Karen disappeared?!`, `but I haven't eaten yet`, `better search for her`, `here u are`를 시간 구간별 한국어 카드로 교체
- 17.6초, 720x1280, H.264/AAC 검토용 MP4 재생성

## 확인 결과

- Python 문법 검사 통과
- 프로젝트 최종 구성 검증 통과
- 실제 검토용 렌더 통과
- 번역 카드 대표 프레임 육안 확인
- YouTube 업로드 패키지 재생성
- Skill 구조 검증 통과 및 `0.4.0+codex.20260821` 설치 캐시 동기화 완료

## 확인 경계

- 원본 권리 상태가 `unknown`이므로 결과물은 개인 로컬 검토용이다.
- 번역은 원본 자막의 현지화 표시이며 관찰 사실의 근거가 아니다.
- 최종본은 사용자가 스토리와 음악 적합성을 모두 승인한 뒤에만 생성한다.
- 프론트엔드 변경이 없어 프론트 빌드는 수행하지 않았다.
