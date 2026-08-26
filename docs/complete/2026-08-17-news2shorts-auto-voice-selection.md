# news2shorts 콘텐츠별 보이스 자동 선택 개선 완료

## 완료 내용

- Typecast 보이스를 다은 한 명으로 고정하지 않고, 프로젝트의 형식·주제·목표 길이에 따라 플러그인이 자동 선택하도록 변경했다.
- 현재 자동 선택 후보는 Typecast `ssfm-v30`과 Smart Emotion을 지원하는 오리지널 보이스 5명으로 제한했다.
  - `Seohyeon`(서현): 민감 주제, 뉴스·팩트 중심, 수치·변화 설명
  - `Daeun`(다은): 빠른 반전, 비교, 일반 `quick-reveal`
  - `Piljae`(필재): 55초 미만의 이야기형 설명
  - `Kangil`(강일): 55초 이상 이야기형 설명
  - `Moonjung`(문정): 가이드, 절차, 사용법 중심 설명
- `--typecast-voice`에 후보 이름·한글 별칭·Voice ID를 주면 자동 선택을 덮어쓸 수 있게 했다.
- 선택된 보이스의 이름, ID, 프로필, 선택 사유를 프로젝트와 `render-report.json`에 기록하도록 했다.
- 기존 프로젝트에 보이스 설정이 없어도 자동 모드로 동작하며, 자동 판단이 명확하지 않으면 다은을 사용한다.
- 후보는 현재 Typecast 캐릭터 목록 API 응답에서 모델 지원 여부와 용도를 확인해 등록했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 후보 목록, 자동 라우팅, 수동 덮어쓰기, TTS 요청 연동, 선택 결과 기록과 검증 추가
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 콘텐츠별 자동 보이스 선택 절차와 예외 규칙 반영
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: 프로젝트·렌더 보고서의 보이스 선택 필드 계약 추가
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`: `narration_voice.mode: "auto"` 기본값 추가
- `plugins/news2shorts/README.md`: 자동 선택 기준과 `--typecast-voice` 사용법 추가
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전 `0.9.0+codex.20260817`과 기능 설명 갱신

## 검증

- 여섯 가지 자동 선택 시나리오 통과: 민감 뉴스, 빠른 반전, 팩트 중심, 짧은 이야기, 긴 이야기, 가이드
- 한글 별칭을 사용한 수동 선택 확인
- CLI와 렌더 도움말에서 `--typecast-voice` 옵션 확인
- Skill 구조 검사와 JSON 템플릿 파싱 통과
- 기존 로봇청소기 보안 프로젝트 최종 검증 통과: 오류 0건, 경고 0건
- 해당 민감 뉴스 프로젝트에서 서현 자동 선택 확인
- 선택된 서현 Voice ID로 Typecast WAV 생성 성공: PCM 16-bit mono, 44.1kHz, 2.857초
- 새 프로젝트 초기화 시 자동 모드 기본값 확인
- `news2shorts@news2shorts-local` 설치본을 `0.9.0+codex.20260817`로 갱신 완료

## 조사 근거

- Typecast 공식 캐릭터 목록 API: https://typecast.ai/docs/ko/api-reference/voices/list-voices
- Typecast 공식 인기 캐릭터 안내: https://typecast.ai/kr/learn/typecast-new-editor-characters/

## 미실행 범위

- 기존 완성 MP4는 다시 렌더하거나 덮어쓰지 않았다.
- 프론트엔드 빌드와 DB 작업은 수행하지 않았다.
