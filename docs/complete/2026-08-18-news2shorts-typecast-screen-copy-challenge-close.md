# news2shorts Typecast 진단·명사형 화면 문구·상황형 반문 완료

## 요청

- Typecast API 키가 없거나 읽히지 않을 때 설정 방법을 바로 안내한다.
- 사실 결론 뒤에 상황에 맞는 따지는 반문을 남기고 Typecast 음성도 해당 문장 흐름을 사용한다.
- 결론 카드처럼 긴 서술문이 어색하게 줄바꿈되지 않도록 화면 문구는 짧은 명사형으로 제한한다.

## 완료 내용

- `doctor`가 Codex 샌드박스의 macOS 키체인 접근 제한과 실제 키 미설정을 구분해 안내한다.
- 제한 환경에서는 키가 없다고 단정하거나 로컬 TTS로 자동 대체하지 않고, 사용자 터미널 재확인 명령과 최초 1회 `configure-typecast` 명령을 출력한다.
- 실제 키체인 접근이 가능한 환경에서는 기존 Typecast 키가 `keychain` 원본으로 정상 인식되는 것을 확인했다.
- 새 프로젝트에 `visual_style.screen_copy_mode: "noun-phrases"`를 기본 적용했다.
- `display_headline`, 장면 헤드라인·강조·자막·결론 제목·상세·질문에 짧은 길이와 명사형 어미 검사를 추가했다.
- 화면 예시는 `비정상 상태 · 원인 미확인`, `현품 보관 · 제조사 조사`, `정상 제품?`처럼 작성한다.
- `discussion_prompt`가 있으면 내레이션이 사실 결론을 먼저 말하고 별도 상황형 반문으로 끝나는지 검사한다.
- Typecast Smart Emotion에는 별도 비공식 감정 매개변수를 추가하지 않고, 최종 내레이션의 자연스러운 문장과 물음표로 억양을 유도한다.
- 피해자 자극이나 근거 없는 책임 추궁이 될 때는 반문을 강제하지 않고 중립 결론을 유지하도록 Skill 규칙을 보완했다.
- 플러그인 버전을 `0.14.0+codex.20260818`로 올리고 재설치했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: Typecast 키체인 제한 진단, 설정 안내, 명사형 화면 문구·결론 내레이션 검증
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 키 미설정 대응, 화면 문구와 상황형 반문 작성 규칙
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`: 사실 결론 뒤 상황형 반문과 Typecast 억양 규칙
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`: 명사형 화면 문구 길이와 예시
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: `screen_copy_mode` 계약과 검증 범위
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`: 새 프로젝트 명사형 화면 모드 기본값
- `plugins/news2shorts/skills/news2shorts/templates/storyboard.template.json`: 명사형 예시 문구
- `plugins/news2shorts/README.md`: Typecast 재확인·설정 방법과 화면·음성 규칙
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전과 기능 설명

## 검증

- 원본 및 설치본 Skill 빠른 검사 통과
- 원본 CLI 도움말과 플러그인·템플릿 JSON 검사 통과
- 새 프로젝트 초기화 시 `screen_copy_mode: "noun-phrases"` 생성 확인
- 명사형 정상 문구는 통과하고 `미확인입니다`, `맞나요` 같은 화면 서술문은 검출하는 양·음수 확인
- 기존 0.13 프로젝트는 새 모드를 명시하지 않으면 기존 호환 규칙으로 검증 통과
- 샌드박스 실행은 `typecast_keychain_check_limited: true`와 안내 명령 출력 확인
- 키체인 접근 허용 실행은 `typecast_api_key_source: keychain` 확인
- 원본과 설치본 스크립트·Skill SHA-256 일치 확인
- 설치 상태 `news2shorts@news2shorts-local 0.14.0+codex.20260818`, enabled 확인

## 미실행 범위

- 기존 커피믹스 검토 영상은 다시 렌더링하지 않았다.
- Typecast API 키 값은 읽거나 출력하거나 프로젝트에 저장하지 않았다.
- 프론트엔드 빌드, DB 작업, YouTube 업로드는 수행하지 않았다.
