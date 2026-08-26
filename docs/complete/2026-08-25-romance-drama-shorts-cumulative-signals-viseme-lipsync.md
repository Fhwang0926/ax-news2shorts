# 연애 드라마 Shorts 누적 시그널·다중 입 모양 립싱크 개선 완료

## 요청

- 아래 비어 있는 영역에 `신호 1~3`이 차례로 누적되게 한다.
- 고정 이미지처럼 보이지 않도록 대사 구간의 립싱크를 개선한다.

## 반영 내용

- 신호 카드를 중앙 영상창 밖의 하단 여백으로 이동했다.
- 신호가 공개되면 이전 신호를 지우지 않고 `1 → 1·2 → 1·2·3` 순서로 누적하며 CTA까지 유지한다.
- 새로 공개된 신호만 노란 테두리로 강조하고, 이미 공개된 신호는 중립 테두리로 낮춰 현재 진행 단계가 보이게 했다.
- 9개 1인 대사 숏에 `정지·벌림·가로·둥근·좁은` 다섯 입 모양을 적용했다.
- 기존 Typecast 구절별 발화 구간 안에서 한국어 음절의 모음 형태에 따라 입 모양을 전환하고, 무음 구간에는 입을 닫는다.
- 얼굴 전체나 턱을 변형하지 않도록 입술 주변의 좁은 마스크만 합성하고 기존 카메라 움직임을 유지했다.
- 투숏, 리액션, 사물 인서트, 신호 유지 화면, CTA에는 립싱크를 강제로 적용하지 않았다.
- 음성 세기만으로 두 입 모양을 반복하던 반려 방식은 다시 사용하지 않았다.

## 변경 파일

- `plugins/romance-drama-shorts/scripts/romance_drama_shorts.py`: 누적 신호 스택, 5상태 입 모양 렌더 명령, 합성·보고서 기록, 버전 `0.1.9`.
- `plugins/romance-drama-shorts/skills/romance-video-producer/SKILL.md`: 하단 누적 규칙과 로컬 다중 입 모양 대체 경로.
- `plugins/romance-drama-shorts/references/project-contract.md`: 신호 공개 이후 누적 유지 계약.
- `plugins/romance-drama-shorts/README.md`: `render-viseme-clips` 사용법과 품질 경계.
- `plugins/romance-drama-shorts/.codex-plugin/plugin.json`: `0.1.9+codex.20260825224551` 버전 갱신.
- 프로젝트 `sync-plan.json`, `viseme-plan-v11.json`, `lip-sync-viseme-v11.json`, `project.json`, `rights-manifest.json`: 최신 출력 연결, 검수 상태, 생성 자산 권리·해시 기록.
- 프로젝트 `assets/generated/lip-sync/scene-03-mouth-open-v2.png`부터 `scene-06-mouth-open-v2.png`: 동일 인물의 입 모양 편집 자산.
- 프로젝트 `assets/generated/lip-sync-v11/*.mp4`: 9개 대사 숏용 로컬 입 모양 클립.
- 프로젝트 `outputs/preview-cumulative-signals-viseme-v11.mp4`, `cumulative-signals-viseme-v11-report.json`: 최종 로컬 검토본과 검수 결과.

## 검증

- 0.2초, 1.2초, 6.7초, 8.2초, 14.8초, 20.2초, 23.0초, 25.0초, 28.6초의 합성 프레임을 직접 확인했다.
- 신호 1·2·3의 순차 누적, 하단 여백 안쪽 배치, 자막·검토 배지·CTA와의 비중첩을 확인했다.
- 대표 립싱크 콘택트 시트와 9개 대사 숏의 입 모양 피크 프레임을 확인했다. 인물 동일성 이탈, 턱·볼 마스크 누출, 불안정한 치아는 관찰되지 않았다.
- H.264/AAC, 720×1280, 30fps, 29.521초, 48kHz 스테레오로 확인했다.
- 전체 885프레임 디코딩과 0.08초 이상 검은 프레임 검사를 통과했다.
- 프로젝트 검증은 오류와 경고 없이 통과했고, 플러그인의 네 스킬도 모두 유효성 검사를 통과했다.
- `romance-drama-shorts@news2shorts-local` 0.1.9 설치와 활성화를 확인했고, 소스와 설치 캐시의 스크립트·제작 스킬·매니페스트 해시가 일치한다.

## 남은 경계

- 이번 방식은 측정된 Typecast 구절 구간과 한국어 음절을 활용한 로컬 검토용 다중 입 모양 애니메이션이며, 제공자 음소 타임스탬프를 이용한 정밀 립싱크는 아니다.
- 현재 연결된 Runway 계정에는 사용할 수 있는 영상 모델이 없어 외부 영상 생성은 수행하지 않았다.
- 권리, 합성 콘텐츠 표시, 게시 승인은 계속 미완료이며 결과물은 로컬 검토용이다.
- DB 작업과 프론트엔드 빌드는 수행하지 않았다.
