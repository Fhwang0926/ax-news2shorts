# Motion2D Studio 의미 기반 모션·한글 타이포 개선

## 완료 범위

- 역할별 고정 카드 템플릿 대신 장면의 `beat`, `kind`, `motion`, `concept`를 조합하는 의미 기반 프리미티브 플래너를 적용했다.
- `focus`, `constellation`, `reveal`, `compare`, `connection`, `movement`, `rhythm`, `sequence`, `boundary`, `spotlight` 시각 구성을 입력 명사·동사와 명시적 `visual_spec`으로 선택한다.
- 상단 진행 막대, 고정 영문 문구, 내레이션 전체를 복사한 하단 카드 구조를 제거했다.
- `screen_text`, 짧은 `caption_text`, 음성용 `narration`을 분리했다. `caption_text`의 `|` 구분자는 장면 안에서 순차 자막으로 렌더한다.
- Apple SD Gothic Neo Bold face index 6을 사용하고, 실제 픽셀 폭·박스 높이·최대 줄 수·최소 글꼴 크기로 한글을 맞춘다.
- `한 / 끼` 같은 고립 줄을 막기 위해 짧은 마지막 줄 앞의 어절을 재배치하고, 최소 크기에서도 넘치면 검증에서 실패하도록 했다.
- 선 끝점 `x2`, `y2` 키프레임을 지원해 연결선, 관절, 시계바늘을 직접 움직인다.
- 실제 TTS가 계획보다 길면 모든 키프레임과 자막 구간을 같은 비율로 확장한다.
- 다음 장면 내레이션을 시각 전환 중 시작하도록 바꿔 장면 사이 반복 무음을 줄이면서 음성 겹침 방지는 유지했다.
- 입력 기반 플랜의 자막 길이, 텍스트 맞춤, 하단 230px 안전영역, 인접 구성 반복, 앞부분 모션 집중을 검증한다.

## 재제작한 검토본

- 입력: `https://www.youtube.com/watch?v=a4D5wX01vV0`
- 프로젝트: `projects/2026-08-18-motion2d-youtube-a4d5wx01vv0-v2`
- 출력: `outputs/preview.mp4`
- 구성: 8장면, 48.177초, 720x1280, 30 FPS, H.264/AAC
- 관계 장면에서 근거에 없던 `전화`를 제거하고 `메시지 한 줄`로 맞췄다.
- `움직임`과 `잠`을 분리해 병렬 항목을 임의의 1~4단계로 표시하던 의미 오류를 제거했다.
- 커튼 열기, 한 끼 접시, 메시지 연결, 1분 스트레칭, 수면 시계, 도움 연결망으로 장면별 시각 대상을 다르게 구성했다.

## 검증 결과

- 프로젝트 정적 검증: 오류 0, 경고 0
- 장면 수: 8
- 모든 장면 `audio_duration > 0`
- 모든 장면 `transition_safe: true`
- 합본에서 0.75초 이상 무음 구간: 0건
- FFprobe: 720x1280, 30 FPS, H.264 영상, AAC 음성, 48.177초
- 검토본은 `LOCAL REVIEW` 표시가 있는 사용자 피드백용 초안이다.

## 변경 파일

- `plugins/motion2d-studio/scripts/motion2d_studio.py`: 의미 기반 플래너, 한글 자동 맞춤, 실제 TTS 길이 기반 타이밍, 연속 음성 타임라인, 품질 검증
- `plugins/motion2d-studio/README.md`: 새 모션 산정 기준과 TTS 연결 방식
- `plugins/motion2d-studio/skills/motion2d-studio/SKILL.md`: 입력 기반 시각 문법과 자막 규칙
- `plugins/motion2d-studio/skills/motion2d-studio/references/input-contract.md`: `art_direction`, `caption_text`, `visual_spec`
- `plugins/motion2d-studio/skills/motion2d-studio/references/visual-playbook.md`: 역할 템플릿에서 의미 기반 시각 문법으로 변경
- `plugins/motion2d-studio/skills/motion2d-studio/references/motion-schema.md`: 플랜 v3, 텍스트 맞춤, 선 끝점 모션
- `plugins/motion2d-studio/skills/motion2d-studio/references/output-contract.md`: 전환 중 시작하는 비중첩 내레이션 규칙
- `projects/2026-08-18-motion2d-youtube-a4d5wx01vv0-source-v2.json`: 근거·문구·시각 비트가 정리된 새 입력
- `projects/2026-08-18-motion2d-youtube-a4d5wx01vv0-v2/`: 이전 결과를 보존한 새 검토 프로젝트와 렌더

## 남은 경계

- 공개 원본의 권리 상태는 `unknown`이며 원본 영상·음원·프레임은 재사용하지 않았다.
- 로컬 macOS TTS는 검토용이며 최종 배포 음성 권리와 품질 승인은 별도다.
- 사실 정확성, 의료적 타당성, 게시 허가, 수익화 적합성은 렌더 성공으로 증명되지 않는다.
- 단계별 사용자 승인은 기록하지 않았으므로 clean final은 생성하지 않았다.
