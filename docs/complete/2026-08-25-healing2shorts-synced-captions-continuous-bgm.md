# healing2shorts 발화 동기화 자막·연속 BGM 개선 완료

## 완료 범위

- 상단의 작은 `오늘의 힐링썰` 분류 문구를 제거하고 주제와 호기심 질문만 남겼다.
- 한 장면에 여러 화자가 있어도 고정 자막 하나를 쓰던 문제를 수정했다. 각 Typecast 발화 WAV의 실제 길이로 자막 시작·종료 시간을 계산해 같은 대사 문구로 교체한다.
- 장면마다 배경음을 새로 생성하던 방식을 전체 길이 WAV 한 개로 바꿨다. 잔잔한 단조 화음 `synthetic_melancholy`를 최종 영상에 한 번만 혼합해 장면 경계에서 음악이 재시작되지 않는다.
- 중간에 `그런데 진짜 이유는 따로 있었습니다.` 재후킹을 추가했다.
- 마지막에 `이러한 이야기를 듣고 싶으면 구독과 좋아요 눌러주세요.` Typecast 발화와 같은 중앙 자막을 추가했다.
- 기존 편집 패키지에 남아 있던 장면별 BGM 파생 파일은 새 렌더 때 제거하고 `edit-package/audio/background-music.wav` 한 파일만 기록한다.

## 변경 파일

- `plugins/healing2shorts/scripts/healing2shorts.py`: 발화별 음성 길이·자막 cue, 다중 오버레이 렌더, 연속 BGM 생성·믹스, 음량 정규화, 작은 상단 분류 제거를 구현했다.
- `plugins/healing2shorts/tests/test_healing2shorts.py`: 12개 발화 계약, 발화별 자막 시간, 새 단조 BGM 생성을 검증하도록 갱신했다.
- `plugins/healing2shorts/skills/healing2shorts/SKILL.md`, `references/output-contract.md`, `README.md`: 재후킹·CTA·발화 동기화 자막·연속 BGM 제작 규칙을 반영했다.
- `plugins/healing2shorts/.codex-plugin/plugin.json`: 기능 설명과 캐시 버전을 갱신했다.
- `projects/2026-08-25-healing2shorts-dialogue-sample-intake/story-candidates.json`: 재후킹과 마지막 CTA를 포함한 12개 대사로 갱신했다.
- `projects/2026-08-25-healing2shorts-dialogue-sample/`: 프로젝트 설정, 스토리, 스토리보드, 대본, Typecast 검토 MP4, SRT, 편집 패키지와 QA 프레임을 다시 생성했다.

## 샘플 결과

- 영상: `projects/2026-08-25-healing2shorts-dialogue-sample/outputs/review.mp4`
- SHA-256: `f29367b778eeb7ed7f34583d2ee70ec97acf45538a3a0302c62f57552b7ca0bd`
- 규격: 540x960, 30fps, 43.236초, H.264/AAC
- 대사·자막: 12개 Typecast 발화와 12개 SRT cue, 모든 장면 `caption_mode=turn_synced`
- 배경음: `synthetic_melancholy`, 전체 43.186초 WAV 한 개, `continuous=true`, 권리 표시 `synthetic_original`
- 최종 음량: 평균 -15.0dB, 최대 0.0dB
- BGM 단독 음량: 평균 -29.7dB, 최대 -20.3dB

## 검증 결과

- Python 문법 검사: 통과
- 단위 테스트: 20개 통과
- JSON 검사: 통과
- 소스·설치 캐시 Plugin validator: 통과
- 소스·설치 캐시 Skill validator: 통과
- 소스·설치 스크립트 SHA-256: 일치
- 프로젝트 review-ready 검사: 오류 없음, `scene-02` 원본 구간 순서 경고 1개 유지
- FFprobe: 540x960, 30fps, 43.236초, H.264/AAC 확인
- 검은 프레임: 미검출
- 중간 무음: 미검출, 영상 끝 0.288초 자연스러운 여운만 검출
- 대표 프레임: 내레이터→할머니 자막 교체, 재후킹, 따뜻한 회수, 마지막 CTA와 상단 안전 영역을 확인했다.
- `git diff --check`: 통과
- 프론트엔드 빌드: 수행하지 않음

## 설치·게시 상태

- 설치본: `healing2shorts@news2shorts-local` `0.4.1+codex.20260825124423`, installed·enabled
- 영상 권리 상태: 기존 `licensed` 기록 유지
- 게시 상태: `publish_blocked=true` 유지
- 사람의 스토리·화면·업로드 최종 승인 전이므로 실제 업로드는 수행하지 않았다.
