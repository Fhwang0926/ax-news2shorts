# Motion2D Studio URL·YouTube 모션 쇼츠 개선 완료

## 요청 반영

- 입력이 없으면 프로젝트를 만들지 않도록 `init` 입력을 필수화했다.
- 고정 데모는 사용자가 `--demo`를 명시한 경우에만 생성한다.
- 공개 URL, YouTube 영상, 검토된 source JSON, 대본, 장면 흐름을 입력으로 지원한다.
- 새 프로젝트의 기본 결과를 9:16 모션 쇼츠로 변경했다.
- 대본, 장면 역할, 화면 문구, 포인트, 후속 설명과 모션 계획을 입력마다 다시 생성한다.
- YouTube는 영상 파일을 내려받지 않고 공개 메타데이터와 게시자/자동 자막을 `inputs/source.json`에 기록한다.
- 장면별 한국어 검토 TTS는 진입 전환 이후 한 번 시작하고, 다음 전환 전 여백을 보존한다.
- 사용자 품질 피드백용 실제 입력 검토본은 `--draft --review-sample`로 표시 렌더할 수 있게 했다. 최종 승인·권리 관문은 우회하지 않는다.

## 변경 파일

- `plugins/motion2d-studio/scripts/motion2d_studio.py`
  - URL·YouTube 수집, source JSON 입력, 필수 입력 관문, 재계획, 1080x1920 캔버스, 세로형 역할별 레이아웃, 검토 샘플 렌더를 추가했다.
  - 검토본 720x1280/30 FPS, 최종본 1080x1920/30 FPS 프로필을 적용했다.
- `plugins/motion2d-studio/skills/motion2d-studio/SKILL.md`
  - URL/YouTube/대본/흐름 입력, 데모 제한, 원본 미디어 비재사용, 입력별 모션·후속 설명 생성 절차를 명시했다.
- `plugins/motion2d-studio/skills/motion2d-studio/references/*.md`
  - 입력·세로형 모션·출력·권리·승인 계약을 9:16 쇼츠 기준으로 갱신했다.
- `plugins/motion2d-studio/skills/motion2d-studio/templates/*.json`
  - 프로젝트, 브리프, 모션 캔버스, TTS, 권리 기본값을 세로형 쇼츠 기준으로 변경했다.
- `plugins/motion2d-studio/.codex-plugin/plugin.json`, `skills/motion2d-studio/agents/openai.yaml`, `plugins/motion2d-studio/README.md`, `README.md`
  - 플러그인 설명, 호출 예시, UI 문구와 사용법을 새 목적에 맞게 변경했다.
- `projects/2026-08-18-motion2d-youtube-a4d5wx01vv0-source.json`
  - 예시 YouTube 영상의 공개 출처, 자막 근거 시점, 광고 제외와 의료 표현 경계, 7장면 편집 흐름을 기록했다.
- `projects/2026-08-18-motion2d-youtube-a4d5wx01vv0/`
  - 입력 기록, 브리프, 스토리보드, 모션 계획, 가이드 TTS, 대표 프레임과 로컬 검토본을 생성했다.

## 예시 결과

- 소스: `https://www.youtube.com/watch?v=a4D5wX01vV0`
- 구성: 훅 → 빛·밥·관계·움직임·잠 → 빛 → 식사 → 관계 → 움직임·잠 → 전문 도움 경계
- 광고 구간과 원본 영상 프레임·음원·브랜드는 제외했다.
- 출력: `projects/2026-08-18-motion2d-youtube-a4d5wx01vv0/outputs/preview.mp4`
- 실제 미디어: 720x1280, 30 FPS, H.264/AAC, 49.37초
- 장면 수: 7
- 모든 장면 TTS `audio_duration > 0`, 전체 `transition_safe: true`

## 확인

- 설치 버전: `motion2d-studio@news2shorts-local` `0.1.0+codex.20260817153925`, installed/enabled
- 설치 캐시의 CLI·SKILL SHA-256이 작업공간 원본과 일치
- `doctor --json`: Python, Pillow, FFmpeg, FFprobe, macOS guide TTS 준비 확인
- YouTube 직접 `--source-url` 초기화: 7장면 source-url 프로젝트 생성과 정적 검증 통과
- `plan --source-url`: URL 변경 시 storyboard와 motion-plan 동시 재생성 확인
- 예시 프로젝트 `validate`: 오류·경고 없음
- 실제 검토본 FFprobe: 720x1280, 30 FPS, H.264/AAC, 49.37초
- 대표 7장면 프레임을 시각 확인: 텍스트 잘림과 세로 안전영역 이탈 없음

## 남은 경계

- 소스 권리는 `unknown`이며 원본 미디어는 사용하지 않았다. 결과는 로컬 품질 검토용이다.
- 로컬 macOS TTS는 최종 납품용 권리·품질 확인 음성이 아니다.
- 우울감 관련 내용은 원본 영상의 설명을 요약한 것이며 의학적 진단이나 치료 지침으로 검증된 최종본이 아니다.
- 사용자 승인, 독립적인 사실 검토, 최종 음성 권리와 게시 허가는 아직 완료되지 않았다.
