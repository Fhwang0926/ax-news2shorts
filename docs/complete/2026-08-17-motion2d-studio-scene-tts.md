# Motion2D Studio 장면 설명 TTS 적용 완료

## 완료 내용

- 대본은 외부 영상에서 자동 복사하지 않고 `brief.json`의 사용자 정보와 검증된 주장을 Codex가 `storyboard.json`의 장면별 `narration`으로 재구성하도록 출처 규칙을 명확히 했다.
- `storyboard.json.script_origin`에 대본 생성 방식, 사용 파일과 참고 자료 ID를 기록하도록 템플릿과 검증을 보완했다.
- 모션은 장면 역할, 내레이션의 설명 순서, 정보 계층과 읽기 시간을 기준으로 산정하도록 제작 규칙을 구체화했다.
- 애니메틱과 초안 렌더가 별도 옵션 없이 각 장면의 `narration`을 macOS `say`의 한국어 `Yuna`, 속도 190으로 읽도록 기본값을 변경했다.
- 대본, 음성, 속도가 같으면 `audio/guide/scene-XX.aiff`와 `scene-XX.tts.json`을 재사용하도록 TTS 캐시를 추가했다.
- 장면 길이는 계획 시간, 모션 시간, 실제 TTS 길이와 0.35초 여유 중 가장 긴 값으로 유지했다.
- macOS 음성 서비스가 성공 코드와 함께 0초 AIFF를 반환하는 경우 렌더 성공으로 처리하지 않고 명확한 권한 오류로 중단하도록 보완했다.
- 로컬 TTS는 검토본 전용으로 유지하고 clean final에는 권리와 품질을 확인한 장면별 음성 파일이 필요하도록 기존 관문을 유지했다.
- 플러그인 버전을 `0.1.0+codex.20260817143513`으로 갱신해 재설치하고 installed/enabled 상태를 확인했다.

## 변경 파일

- `plugins/motion2d-studio/scripts/motion2d_studio.py`: TTS 기본 설정, 음성 캐시, 실제 길이 검사, 장면 길이와 보고서 기록
- `plugins/motion2d-studio/skills/motion2d-studio/templates/storyboard.template.json`: 대본 출처 계약
- `plugins/motion2d-studio/skills/motion2d-studio/templates/post-production.template.json`: 검토용 TTS 기본값
- `plugins/motion2d-studio/skills/motion2d-studio/SKILL.md`: 대본 작성, 모션 산정, 기본 TTS와 권한 재시도 절차
- `plugins/motion2d-studio/skills/motion2d-studio/references/visual-playbook.md`: 장면 역할별 모션 기준
- `plugins/motion2d-studio/skills/motion2d-studio/references/output-contract.md`: 대본 출처와 TTS 메타데이터 계약
- `plugins/motion2d-studio/skills/motion2d-studio/references/workflow.md`: 스토리보드와 애니메틱 검토 항목
- `plugins/motion2d-studio/README.md`: 사용자용 대본·모션·TTS 설명과 실행법
- `plugins/motion2d-studio/.codex-plugin/plugin.json`: 설치 캐시 갱신 버전
- `projects/2026-08-17-motion2d-studio-demo/`: 대본 출처, TTS 설정, 7장면 음성, 메타데이터와 새 검토본

## 검증 결과

- Plugin validator와 Skill validator 통과
- Python 구문, JSON 파싱, CLI 도움말, `doctor --json`, `git diff --check` 통과
- 7개 장면 모두 `local-guide-tts`, `Yuna`, 속도 190으로 기록 확인
- 장면별 실제 TTS 길이 2.68~4.62초 확인
- TTS가 계획 장면보다 긴 장면은 `TTS 길이 + 0.35초`로 자동 확장 확인
- 재실행 시 같은 장면의 오디오와 렌더 캐시 재사용 확인
- 0초 AIFF가 생성되는 제한 환경에서는 의도한 오류로 중단하고, 음성 서비스 권한 실행에서는 실제 음성 생성 확인
- 새 검토본: 960x540, 15 FPS, H.264, AAC, 약 27.1초 확인
- 검토본 오디오: 평균 -17.6 dB, 최대 -3.4 dB로 무음이 아님을 확인
- 설치 캐시의 `doctor`와 새 렌더 옵션 확인

## 확인하지 않은 범위

- Typecast API 키가 현재 설정되어 있지 않아 외부 고품질 TTS와 네트워크 호출은 실행하지 않았다.
- 로컬 macOS 음성의 배포 권리는 확인하지 않았으며 최종 납품 음성으로 승인하지 않았다.
- 사용자 지침에 따라 프론트엔드 빌드는 수행하지 않았고 DB는 조회·변경하지 않았다.
