# healing2shorts story-01 검토본 제작 기록 · 재작업 필요

## 후속 품질 판정

- 사용자 검토 결과, 이 영상은 대사가 오가는 힐링 썰이 아니라 기사형 미담 요약에 가까워 최종본으로 진행하지 않는다.
- `outputs/review.mp4`는 실패 원인과 기존 계약 호환 확인을 위한 로컬 기록으로만 보존한다.
- 다음 제작은 대화형 story contract v3에서 새 스토리 후보를 선택한 뒤 별도 프로젝트로 진행한다.

## 완료 범위

- 사용자 선택 `story-01 + food-01`을 36초, 7장면 검토 프로젝트로 제작했다.
- 기사 표현을 그대로 낭독하지 않고 확인된 사건을 `cold_open → setup → problem → clue → escalation → reveal → afterglow` 구조로 다시 구성했다.
- 첫 훅은 Typecast 재생 시간이 장면 제한을 넘지 않도록 `왜 자리를 바꿨을까요?`로 압축했다.
- 사용 조건을 기록한 Katerina Holmes의 Pexels 조리 몽타주에서 서로 겹치지 않는 7개 구간을 사용했다.
- 첫 장면은 완성 요리를 먼저 보여주고 이후 손질, 팬 조리, 면 준비, 완성 컷으로 이어지게 편집했다.
- Typecast Daeun 내레이션, 큰 두 줄 자막, 저강도 자체 앰비언트를 포함한 540x960 검토 MP4를 생성했다.
- 장면별 MP4, Typecast WAV, SRT, CapCut/Vrew 메타데이터와 YouTube 업로드 문구 초안을 생성했다.
- 실제 업로드와 720x1280 최종 렌더는 수행하지 않았다.

## 생성·변경 파일

- `projects/2026-08-25-healing2shorts-story-01-intake/story-candidates.json`: `story-01` 출처, claim, 재미 점수와 7비트 대본을 기록했다.
- `projects/2026-08-25-healing2shorts-story-01-intake/video-candidates.json`: `food-01` 출처, 제작자, 원본 해시, 권리 범위와 7개 무문자 구간을 기록했다.
- `projects/2026-08-25-healing2shorts-story-01-intake/pexels-license-evidence.md`: Pexels 라이선스와 구성 원본 증빙을 기록했다.
- `projects/2026-08-25-healing2shorts-story-01/`: 프로젝트 메타데이터, 스토리보드, 권리 증빙, Typecast 음원, 프리뷰, 검토 MP4, 편집 패키지와 업로드 문구를 생성했다.
- `projects/2026-08-25-healing2shorts-story-01/qa-frames/`: 렌더 후 장면별 대표 프레임 7개를 생성했다.

## 검증 결과

- review-ready 검증: 통과
- 의도된 경고: 완성 요리를 첫 훅으로 선공개해 `scene-02`에서 원본 시간 순서가 한 번 되감김
- 검토 렌더: H.264/AAC, 540x960, 30fps, 36.087초
- 내레이션: Typecast Daeun, 7개 장면 모두 생성 성공
- 오디오: 평균 -21.5dB, 최대 -5.4dB
- 화면 검토: 두 줄 자막 안전 영역 정상, 세로 크롭 정상, 중국어·원본 워터마크 미검출
- FFmpeg blackdetect: 마지막 구간을 포함해 검은 프레임 미검출
- 편집 패키지: 장면 클립 7개, Typecast 음원 7개, SRT, 메타데이터 생성
- 권리 상태: `licensed`, YouTube·상업 이용·편집·음성 오버레이 허용 및 증빙 해시 기록
- 프론트엔드 빌드: 수행하지 않음

## 게시 가능 여부

- 로컬 검토본과 편집 패키지 제작은 완료했다.
- `rights_reviewed=true`지만 사용자의 `story_reviewed`, `visual_reviewed`, `upload_reviewed` 확인 전이므로 `publish_blocked=true`를 유지한다.
- 사용자 확인 후 publish-ready 검증과 720x1280 최종 렌더를 별도로 진행한다.
- 로컬 렌더와 라이선스 기록은 기사 사실성, 플랫폼 승인, 수익화 또는 조회수 성과를 보장하지 않는다.
