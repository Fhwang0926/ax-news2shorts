# healing2shorts 감동형 BGM·내레이터 인용 개선 완료

> 같은 프로젝트의 `outputs/review.mp4`는 이후 상단 호기심 주제 밴드를 적용한 버전으로 대체되었다. 현재 화면 결과는 `2026-08-25-healing2shorts-curiosity-topic-band.md`를 기준으로 확인한다.

## 완료 범위

- 사용자의 피드백에 따라 기존 단음 앰비언트를 장면별 화음이 진행되는 자체 생성 감동형 BGM으로 교체했다.
- BGM은 `synthetic_original`로 기록하고 원본 영상 음악은 계속 음소거했다.
- `할머니:`, `나:` 같은 화면 화자 라벨을 제거하고 중앙에는 현재 발화의 핵심 문구만 두 줄 이내로 표시했다.
- 다은 내레이터가 `제가 이유를 물어보니, 할머니는 이렇게 말했어요`처럼 상황을 짧게 연결한 뒤 문정 할머니가 직접 답하는 Typecast 순서로 원고를 재구성했다.
- 새 형식이 계속 유지되도록 신규 v3 후보에서 화자 라벨 자막을 거부하고, 감동형 BGM 설정과 편집용 장면별 BGM WAV를 렌더 계약에 추가했다.
- 실제 업로드와 게시 승인은 수행하지 않았다.

## 변경 파일

- `plugins/healing2shorts/scripts/healing2shorts.py`: 감동형 화음 생성, BGM 음량 설정, 편집용 BGM WAV, 렌더 보고서 기록, 화자 라벨 검증을 추가했다.
- `plugins/healing2shorts/tests/test_healing2shorts.py`: 화자 라벨 거부와 감동형 BGM 화음·에코 검증을 추가했다.
- `plugins/healing2shorts/skills/healing2shorts/SKILL.md`: 내레이터 연결 뒤 인물 직접 인용이 이어지는 제작 흐름을 기본값으로 변경했다.
- `plugins/healing2shorts/skills/healing2shorts/references/story-patterns.md`: 내레이터·인물 인용 구조와 반복 연결 문장 제한을 기록했다.
- `plugins/healing2shorts/skills/healing2shorts/references/candidate-contract.md`: 라벨 없는 자막과 내레이터→인물 turn 순서를 기록했다.
- `plugins/healing2shorts/skills/healing2shorts/references/output-contract.md`: 감동형 BGM과 장면별 편집 음원 계약을 기록했다.
- `plugins/healing2shorts/README.md`, `plugins/healing2shorts/.codex-plugin/plugin.json`: 사용자-facing 기능 설명을 갱신했다.
- `projects/2026-08-25-healing2shorts-dialogue-sample-intake/story-candidates.json`: 11개 내레이터·할머니 발화로 원고를 교체했다.
- `projects/2026-08-25-healing2shorts-dialogue-sample/`: 프로젝트 음성 매핑, 스토리, 스토리보드, 대본, 검토 MP4와 편집 패키지를 다시 생성했다.

## 샘플 결과

- 영상: `projects/2026-08-25-healing2shorts-dialogue-sample/outputs/review.mp4`
- 출력 SHA-256: `6d3213fe4f48e4db8b868cb7619627bfb97d776c4a1bfa6a05b73a644f0e7118`
- 내레이터: Typecast 다은, `warm-story-narrator`, tempo 1.10
- 할머니: Typecast 문정, `warm-elderly-character`, tempo 1.08
- BGM: `synthetic_emotional`, volume 0.90, rights `synthetic_original`
- 편집 패키지: 각 장면의 내레이션 WAV와 `scene-XX-bgm.wav`를 별도로 제공한다.

## 검증 결과

- 설치 버전: `healing2shorts@news2shorts-local` `0.4.1+codex.20260825121916`
- 소스·설치 캐시 Plugin validator와 Skill validator: 통과
- Python 문법 및 플러그인 단위 테스트: 18개 통과
- 프로젝트 review-ready 검증: 오류 없음, 원본 구간이 `scene-02`에서 한 번 되감기는 기존 경고 1개
- 영상 속성: H.264/AAC, 540x960, 약 30fps, 43.240초
- 전체 음량: 평균 -21.5dB, 최대 -4.8dB
- 장면 2 대사 평균: -14.9dB
- 장면 2 BGM 혼합 기준 평균: -32.7dB로 대사보다 약 18dB 낮음
- 검은 프레임 검사: 미검출
- 대표 장면 육안 확인: 상단 제목, 중앙 문구, 화자 라벨 없음, 자막 배경 없음, 세로 안전영역 정상
- 프론트엔드 빌드: 수행하지 않음

## 게시 상태

- 영상 권리 상태는 기존 `licensed`와 Pexels 증빙을 유지한다.
- `publish_blocked=true`를 유지한다.
- `story_reviewed`, `visual_reviewed`, `upload_reviewed`가 사용자 승인 전이므로 실제 업로드를 수행하지 않았다.
- 로컬 검토본과 Typecast·BGM 생성 성공은 플랫폼 승인, 수익화 또는 조회수 성과를 보장하지 않는다.
