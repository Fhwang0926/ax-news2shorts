# healing2shorts 대화형 초기 무음 샘플 기록

> 이 문서는 2026-08-25에 만든 초기 무음 검토본 기록이다. 같은 프로젝트의 `outputs/review.mp4`는 이후 Typecast 다중 화자와 새 자막 레이아웃을 적용한 검토본으로 대체되었다. 현재 결과는 `2026-08-25-healing2shorts-typecast-clean-dialogue-sample.md`를 기준으로 확인한다.

## 완료 범위

- 사용자 요청에 따라 Typecast와 다른 TTS를 호출하지 않은 대화형 v3 샘플을 제작했다.
- 게시 후보가 아닌 형식 검토용으로 `할머니가 매일 빵 두 개를 산 이유`라는 창작·재구성 익명 사연을 사용했다.
- 2명의 화자, 10개 대사, 화자 교대 8회, 42초의 7장면으로 구성했다.
- 모든 장면을 인물 이름이 포함된 두 줄 이내 대사 자막으로 만들었다.
- 기존 `food-01`의 사용 조건이 기록된 Pexels 음식 영상과 권리 증빙을 재사용했다.
- 실제 업로드와 최종 렌더는 수행하지 않았다.

## 생성 파일

- `projects/2026-08-25-healing2shorts-dialogue-sample-intake/story-candidates.json`: v3 창작 샘플의 대사, 7비트, 점수와 재구성 표시를 기록했다.
- `projects/2026-08-25-healing2shorts-dialogue-sample/outputs/review.mp4`: 당시에는 540x960 무음 기술 검토본이었으나 현재는 Typecast 적용본으로 대체되었다.
- `projects/2026-08-25-healing2shorts-dialogue-sample/edit-package/`: 장면 클립 7개, 무음 WAV 7개, SRT와 메타데이터를 생성했다.
- `projects/2026-08-25-healing2shorts-dialogue-sample/qa-frames/`: 렌더 후 대표 장면 7개를 생성했다.
- `projects/2026-08-25-healing2shorts-dialogue-sample/youtube-upload.md`: 실제 업로드 없이 창작·재구성 표시가 포함된 문구 초안을 생성했다.

## 검증 결과

- v3 story contract: 통과
- review-ready 검증: 통과
- 검토 렌더: H.264/AAC, 540x960, 30fps, 42.067초
- 렌더 보고서의 장면별 `audio_source`: 모두 `silent`
- Typecast 내레이션 자산: 생성되지 않음
- 잔여 앰비언트: 평균 -58.8dB, 최대 -51.9dB
- 대표 장면 확인: 10개 대사 흐름, 두 줄 자막 안전 영역, 세로 크롭 정상
- 중국어·원본 워터마크·검은 마지막 프레임: 미검출
- 권리 상태: `licensed`, Pexels 증빙 해시 기록
- 의도된 경고: 완성 음식 훅 이후 재료 손질로 돌아가 `scene-02`에서 원본 시간 순서가 한 번 되감김
- 프론트엔드 빌드: 수행하지 않음

## 게시 상태

- 형식 검토용 창작 샘플이며 `publish_blocked=true`를 유지한다.
- `story_reviewed`, `visual_reviewed`, `upload_reviewed`는 사용자가 승인하지 않아 false다.
- 로컬 검토 성공은 플랫폼 승인, 수익화 또는 조회수 성과를 보장하지 않는다.
