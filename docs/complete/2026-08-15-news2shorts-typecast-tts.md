# news2shorts Typecast TTS 반영 완료

## 반영 내용

- 영상 렌더의 기본 TTS를 Typecast `ssfm-v30`으로 변경했다.
- Typecast Voice ID를 `tc_61f0859907085fc68561c9a1`로 고정했다.
- macOS에서는 `configure-typecast` 명령으로 `TYPECAST_API_KEY`를 키체인에 최초 한 번 저장하고 이후 렌더마다 자동으로 읽는다.
- CI나 macOS가 아닌 환경에서는 `TYPECAST_API_KEY` 환경변수를 우선 사용한다.
- 프로젝트 파일·로그·렌더 보고서에는 API 키를 기록하지 않는다.
- 장면별 내레이션에 앞뒤 장면 문맥을 함께 전달하는 Smart Emotion을 적용했다.
- 기본 음성 출력은 한국어 WAV, 1.05배 속도, -14 LUFS이며 재현 가능한 seed를 사용한다.
- 렌더 보고서에 TTS 제공자, 모델, Voice ID와 장면별 오디오 출처를 기록한다.
- Typecast를 사용하지 않는 개인 검토본은 `--tts-provider local`, 무음 검토본은 `--no-tts`로 기존 경로를 유지한다.
- SDK나 신규 패키지 없이 Python 표준 라이브러리로 공식 Typecast TTS API를 호출한다.

## 설정 및 검증 경계

- 키체인 최초 설정, 재설정, 상태 확인과 고정 Voice ID를 플러그인 README에 기록했다.
- Typecast 요청은 모의 WAV 응답으로 URL, 인증 헤더, 한국어·Smart Emotion·음량 설정을 확인했다.
- 실제 비밀값 없이 키체인 저장 명령, 자동 조회, 환경변수 우선순위를 모의 검증했다.
- Python 3.14 기본 CA 경로가 비어 있는 macOS 환경에서는 시스템 CA 번들을 사용하도록 보완했으며 TLS 인증서 검증은 유지한다.
- Python 문법, 플러그인 manifest JSON, CLI 도움말, `doctor`, 공백 오류를 확인했다.
- 설치된 플러그인을 `0.5.3+codex.20260815`로 갱신했다.
- 실제 Typecast 음성 생성은 사용자 API 키가 없어 수행하지 않았다.
- 사용자 macOS 키체인에는 임의 키를 저장하지 않았으며, 사용자가 숨김 프롬프트에서 최초 한 번 설정해야 한다.
- 프론트엔드나 DB 변경은 없으며 프론트 빌드는 수행하지 않는다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
- `plugins/news2shorts/.env.example`
- `plugins/news2shorts/.codex-plugin/plugin.json`
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
- `plugins/news2shorts/skills/news2shorts/references/rights-policy.md`
- `plugins/news2shorts/README.md`
- `README.md`
