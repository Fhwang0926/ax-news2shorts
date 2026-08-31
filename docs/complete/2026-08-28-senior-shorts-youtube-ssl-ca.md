# 시니어 쇼츠 YouTube SSL CA 오류 수정 완료

## 원인

- 현재 Python 3.14가 기대하는 `/Library/Frameworks/Python.framework/Versions/3.14/etc/openssl/cert.pem` 파일이 없었다.
- `ssl.get_default_verify_paths()`의 실제 `cafile`과 `capath`가 모두 비어 있어 Google API TLS 인증서 체인을 검증하지 못했다.
- macOS 시스템 인증서 묶음 `/etc/ssl/cert.pem`과 Homebrew 인증서 묶음은 정상적으로 존재했다.

## 수정 내용

- Python 기본 CA 파일이 실제로 존재하면 그대로 사용한다.
- 기본 CA 파일이 없으면 `/etc/ssl/cert.pem`, `/opt/homebrew/etc/openssl@3/cert.pem` 순서로 존재하는 시스템 인증서 묶음을 선택한다.
- YouTube Data API HTTPS 요청에 선택한 CA 파일로 만든 `ssl.SSLContext`를 명시한다.
- `doctor`에 `youtube_api.ssl_ca_file`과 `ssl_verification_enabled`를 표시한다.
- 인증서 검증 비활성화, 무검증 SSL 컨텍스트, TLS 우회는 추가하지 않았다.
- 기존 키체인 API 키는 그대로 유지되므로 `configure-youtube`를 다시 실행할 필요가 없다.

## 변경 파일

- `plugins/senior-shorts/scripts/senior_shorts.py`: 검증된 시스템 CA 탐색과 YouTube HTTPS 컨텍스트를 추가했다.
- `plugins/senior-shorts/README.md`: macOS Python CA fallback과 진단 필드를 기록했다.
- `plugins/senior-shorts/skills/senior-shorts/references/discovery-contract.md`: TLS 검증 유지 원칙을 추가했다.
- `docs/complete/2026-08-28-senior-shorts-youtube-ssl-ca.md`: 원인, 수정 범위, 검증 경계를 기록했다.

## 검증 경계

- 기본 CA 부재와 `/etc/ssl/cert.pem` 존재를 현재 환경에서 확인했다.
- 수정한 SSL 컨텍스트로 Google 공개 API 문서 엔드포인트가 HTTP 200을 반환했고 `CERT_REQUIRED`, 호스트명 검증 활성 상태를 확인했다.
- `senior-shorts@news2shorts-local`을 `0.1.0+codex.20260828094046`으로 재설치했고 소스와 설치 캐시의 manifest, CLI, README, discovery 계약 SHA-256 일치를 확인했다.
- Plugin manifest, Skill, CLI 로딩, `git diff --check`를 확인한다.
- 실제 YouTube API 키 값은 읽거나 출력하지 않는다.
- 사용자 지침에 따라 단위 테스트, 영상 렌더, 프론트엔드 빌드는 수행하지 않는다.
