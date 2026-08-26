# 연애 드라마 Shorts 화면 검토본 배지 제거 완료

## 요청

- 영상 오른쪽 아래에 표시되는 `검토본` 배지를 제거한다.

## 반영 내용

- 오리지널 각색의 박스형 영상 화면에서 `검토본` 배지를 그리던 처리를 제거했다.
- 첫 대사, 시그널 공개, CTA를 포함한 모든 장면에서 배지가 나타나지 않게 했다.
- 시그널 누적, Typecast 음성·자막, 9개 대사 숏 립싱크, 배경음과 기존 화면 구성은 유지했다.
- 초안·승인 상태는 화면에 표시하지 않고 `project.json`과 렌더 보고서에만 기록한다.
- 권리·합성 콘텐츠 표시·게시 승인 게이트는 변경하지 않았다.

## 변경 파일

- `plugins/romance-drama-shorts/scripts/romance_drama_shorts.py`: 박스형 영상의 화면 배지 제거, 보고서에 `onscreen_review_badge: false` 기록, 버전 `0.1.10`.
- `plugins/romance-drama-shorts/skills/romance-video-producer/SKILL.md`: 화면 배지와 내부 승인 상태를 분리하는 제작 규칙 추가.
- `plugins/romance-drama-shorts/README.md`: 오리지널 각색 영상의 배지 미표시와 승인 게이트 유지 안내.
- `plugins/romance-drama-shorts/.codex-plugin/plugin.json`: `0.1.10+codex.20260825225943`으로 갱신.
- 프로젝트 `sync-plan.json`, `project.json`: v12 출력 경로와 변경 이력 기록.
- 프로젝트 `outputs/preview-cumulative-signals-viseme-v12.mp4`, `cumulative-signals-viseme-v12-report.json`: 배지 없는 영상과 검수 결과.

## 검증

- 1.2초 대사 화면, 6.7초 첫 시그널 화면, 28.6초 CTA 화면을 직접 확인해 배지가 없음을 확인했다.
- H.264/AAC, 720×1280, 30fps, 29.521초, 48kHz 스테레오를 확인했다.
- 전체 885프레임 디코딩과 0.08초 이상 검은 프레임 검사를 통과했다.
- 프로젝트 검증은 오류·경고 없이 통과했고 제작 스킬 유효성 검사도 통과했다.
- 플러그인 0.1.10 설치·활성화와 소스·설치 캐시 해시 일치를 확인했다.

## 경계

- 화면 배지만 제거한 것이며 `draft_rendered`, 미완료 권리·합성 표시·게시 승인 상태는 그대로다.
- 제3자 원본이 `unknown` 또는 `review_required`인 경우 최종 렌더·업로드 차단 정책은 유지된다.
- DB 작업과 프론트엔드 빌드는 수행하지 않았다.
