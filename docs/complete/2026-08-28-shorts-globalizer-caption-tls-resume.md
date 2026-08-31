# Shorts Globalizer 자막 TLS 및 pending 재개 작업 완료

## 원인

- Python 3.14 기본 CA 경로 `/Library/Frameworks/Python.framework/Versions/3.14/etc/openssl/cert.pem`에 파일이 없어 표준 `urllib` 자막 요청이 `CERTIFICATE_VERIFY_FAILED`로 중단됐다.
- 같은 Python 환경에는 정상 `certifi` CA 번들이 이미 설치돼 있었고, 해당 CA를 명시한 임시 검증에서는 자동 한국어 자막 수집과 ingest 검증이 성공했다.

## 완료 내용

- 자막 HTTPS 요청은 Python 기본 CA 파일·디렉터리를 먼저 사용한다.
- 기본 CA가 없을 때만 이미 설치된 `certifi` CA 번들을 자동 선택한다.
- 모든 경로에서 `ssl.create_default_context`를 사용하며 TLS 인증서 검증을 끄지 않는다.
- 신뢰 가능한 CA가 전혀 없으면 `doctor --json`의 `ready`를 false로 만들고 자막 요청 전에 명확한 오류로 중단한다.
- `doctor --json`에 `caption_tls.available`, `mode`, `cafile`을 추가했다.
- 설치 캐시에서 실행할 때도 현재 로컬 마켓플레이스 작업공간을 찾아 저장소의 `projects/shorts-globalizer`를 기본 출력 경로로 사용하도록 수정했다.
- 동일 URL의 기존 프로젝트가 정확히 `transcript_pending`, 빈 transcript, 미승인 상태일 때만 `init` 재실행으로 이어받도록 구현했다.
- 다른 영상·URL, 비어 있지 않은 transcript, 승인된 상태, `ingested` 이후 상태는 기존처럼 덮어쓰기를 차단한다.
- 안전한 재개는 `project.json`, `source.json`, `source-analysis.json`, `transcript.txt`의 ingest 정보만 갱신하고 research·script·preview 승인과 게시 차단 상태를 보존한다.
- 플러그인 캐시 버전을 `0.1.0+codex.20260828021031`로 갱신해 `news2shorts-local` 마켓플레이스에서 재설치했다.

## 현재 프로젝트 복구

- 프로젝트: `projects/shorts-globalizer/2026-08-28/jc_BRabpPfc`
- 재실행 결과: `status: ingested`, `transcript_source: automatic`, `resumed: true`
- 자막 크기: 774바이트
- ingest 검증: 오류·경고 없이 통과
- 기존 topic 승인만 유지하고 research·script·preview 승인은 false로 보존
- `publish_blocked: true`, `video_downloaded: false` 유지

## 변경 파일

- `plugins/shorts-globalizer/scripts/shorts_globalizer.py`
- `plugins/shorts-globalizer/README.md`
- `plugins/shorts-globalizer/skills/shorts-globalizer/SKILL.md`
- `plugins/shorts-globalizer/skills/shorts-globalizer/references/workflow.md`
- `plugins/shorts-globalizer/skills/shorts-globalizer/references/project-contract.md`
- `plugins/shorts-globalizer/tests/test_shorts_globalizer.py`
- `plugins/shorts-globalizer/.codex-plugin/plugin.json` 캐시 버전

## 검증 결과

- Python 테스트 14개 통과
- CA 선택과 검증 SSL context 전달 테스트 통과
- 안전한 `transcript_pending` 재개와 비-pending 덮어쓰기 차단 테스트 통과
- Python 구문 검사 통과
- 플러그인 validator 통과
- 스킬 validator 통과
- `doctor --json`: `caption_tls.mode: certifi-fallback`, `available: true`, `ready: true`
- 설치 캐시에서 실행한 `doctor --json`도 저장소 출력 경로를 찾아 `ready: true` 확인
- 환경변수 없이 실제 공개 자동 한국어 자막 수집 성공
- 현재 프로젝트 `validate --stage ingest` 통과
- 프론트엔드 변경과 DB 작업은 없으며 프론트엔드 빌드는 수행하지 않았다.

## 유지되는 제한

- 자동 자막이 실제로 존재하지 않는 영상은 계속 `transcript_pending`으로 중단한다.
- 인증서 오류를 이유로 TLS 검증 비활성화, 영상 다운로드, ASR 설치, 로그인·쿠키 사용을 하지 않는다.
- 이 복구는 ingest 완료만 증명한다. 원 Shorts의 사실성, 독립 출처, 원작성, 권리, 미리보기, 게시 준비 상태를 증명하지 않는다.
