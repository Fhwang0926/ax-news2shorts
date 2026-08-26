# healing2shorts Typecast 대화형 샘플 제작 완료

> 같은 프로젝트의 `outputs/review.mp4`는 이후 내레이터→인물 직접 인용과 감동형 자체 생성 BGM을 적용한 버전으로 대체되었다. 현재 결과는 `2026-08-25-healing2shorts-emotional-bgm-narrated-quotes.md`를 기준으로 확인한다.

## 완료 범위

- 기존 42초 대화형 샘플에 화자별 Typecast TTS를 적용했다.
- 할머니는 문정, 손녀는 다은 음성을 사용해 10개 대사를 화자별로 생성하고 장면 단위로 합쳤다.
- 제목은 화면 상단의 강조 영역에 고정하고, 대사는 화면 가운데에 배경 카드 없이 흰 글자·검은 외곽선으로 표시했다.
- 기존 프로젝트의 레거시 자막은 유지하고, 새 프로젝트에서만 `dialogue_clean` 스타일이 기본값이 되도록 범위를 제한했다.
- 실제 업로드나 게시 가능 승인은 수행하지 않았다.

## 변경 파일

- `plugins/healing2shorts/scripts/healing2shorts.py`: 화자별 Typecast 생성·캐시·장면 결합과 `dialogue_clean` 오버레이를 추가했다.
- `plugins/healing2shorts/tests/test_healing2shorts.py`: 대사 배경 카드가 없고 상단 제목 강조가 존재하는지 확인하는 테스트를 추가했다.
- `plugins/healing2shorts/skills/healing2shorts/SKILL.md`: 새 대화형 기본 스타일과 화자별 음성 설정을 안내했다.
- `plugins/healing2shorts/skills/healing2shorts/references/output-contract.md`: `presentation`과 `speaker_voices` 계약을 기록했다.
- `plugins/healing2shorts/README.md`: Typecast 다중 화자와 새 화면 구성을 반영했다.
- `plugins/healing2shorts/.codex-plugin/plugin.json`: 기능 설명과 플러그인 버전을 갱신했다.
- `projects/2026-08-25-healing2shorts-dialogue-sample/project.json`: 문정·다은 음성 매핑과 `dialogue_clean` 표시 설정을 기록했다.

## 생성 결과

- 영상: `projects/2026-08-25-healing2shorts-dialogue-sample/outputs/review.mp4`
- 편집 패키지: `projects/2026-08-25-healing2shorts-dialogue-sample/edit-package/`
- 대표 장면: `projects/2026-08-25-healing2shorts-dialogue-sample/qa-frames/`
- 렌더 보고서: `projects/2026-08-25-healing2shorts-dialogue-sample/render-report.json`
- 업로드 문구 초안: `projects/2026-08-25-healing2shorts-dialogue-sample/youtube-upload.md`

## 검증 결과

- 플러그인 단위 테스트: 15개 통과
- 설치 버전: `healing2shorts@news2shorts-local` `0.4.1+codex.20260825120157`
- 소스·설치 캐시 Plugin validator 및 Skill validator: 통과
- Typecast 적용: 7개 장면 모두 `typecast-dialogue`
- 영상 속성: H.264/AAC, 540x960, 약 30fps, 42.066초
- 음량: 평균 -22.7dB, 최대 -5.4dB
- 검은 프레임 검사: 미검출
- 대표 장면 육안 확인: 상단 제목, 중앙 대사, 대사 배경 없음, 세로 안전영역 정상
- 권리 상태: `licensed`, 기존 Pexels 증빙 유지
- 프론트엔드 빌드: 수행하지 않음

## 게시 상태

- `publish_blocked=true`를 유지한다.
- `story_reviewed`, `visual_reviewed`, `upload_reviewed`가 사용자 승인 전이므로 실제 업로드를 수행하지 않았다.
- 로컬 검토본과 Typecast 생성 성공은 플랫폼 승인, 수익화 또는 조회수 성과를 보장하지 않는다.
