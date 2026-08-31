# CareerFill v0.1 작업 완료

## 목적

지정한 로컬 CareerVault를 근거가 연결된 경력 자료로 정리하고, 사용자가 선택한 현재 Chrome 지원서 탭을 읽기 전용 분석해 항목·제한·근거가 연결된 답변 초안을 준비하는 Codex 플러그인 기반을 추가했다.

## 반영 내용

- `careerfill` 플러그인 manifest와 로컬 marketplace 항목 추가
- 로컬 STDIO MCP `careerfill-local` 추가
- `careerfill-setup`, `careerfill-apply`, `careerfill-review` 스킬 분리
- CareerVault 절대 경로 검증과 원본 쓰기 금지
- `90_private`, 숨김 디렉터리, 심볼릭 링크 제외
- 파일 크기, MIME 위장, ZIP 경로 이탈·암호화·과도한 압축 방어
- PDF(PyMuPDF가 있을 때), DOCX, HWPX, MD/TXT, YAML 추출
- JPG/PNG는 OCR 없이 증적 후보로만 목록화
- 원문 상대 경로·SHA-256·페이지·문단·HWPX 섹션이 연결된 Claim 후보 생성
- 모든 자동 Claim을 `review_required`로 생성하고 재스캔 시 같은 Claim의 검토 상태 보존
- 구조화된 프로필 값 충돌 탐지
- S1/S2 Evidence의 파일명 및 본문 토큰 해시 검색, S3 검색 제외
- 정확한 Chrome 탭 ID·URL·origin·회사·직무·페이지 지문을 저장하는 읽기 전용 지원서 세션
- 검증된 Claim, 프로필 출처, 글자 수/UTF-8 바이트 수, 필수 항목, 반복 Claim, 민감·법적 항목을 점검하는 초안 검토

## v0.1 안전 중단선

다음 기능은 구현하지 않았다.

- 브라우저 필드 입력 및 버튼 클릭
- 파일 첨부 및 임시 첨부 파일 생성
- 법적 동의·사실 확인·서약 체크
- 로그인, CAPTCHA, 보안 키패드 우회
- 지원서 저장·다음 단계 이동·최종 제출
- 데이터베이스 생성·초기화·재설정
- OCR 또는 외부 문서 변환 서비스

CareerVault 원본은 읽기 전용이고, 설정·JSON 인덱스·지원서 세션만 플러그인 전용 데이터 폴더에 저장한다.

## 변경 파일

- `.agents/plugins/marketplace.json`: `careerfill` 로컬 marketplace 항목 추가
- `README.md`: 플러그인 목록에 CareerFill 추가
- `plugins/careerfill/.codex-plugin/plugin.json`: 플러그인 메타데이터와 MCP/스킬 경로 정의
- `plugins/careerfill/.mcp.json`: Python STDIO MCP 실행 정의
- `plugins/careerfill/mcp/careerfill_core.py`: CareerVault 스캔·파싱·Claim/Evidence·초안 검토 코어
- `plugins/careerfill/mcp/server.py`: MCP 초기화, 도구 목록, 도구 호출 처리
- `plugins/careerfill/skills/*`: 설정·지원서 초안·검토 워크플로와 UI 메타데이터
- `plugins/careerfill/references/*`: Vault, 지원서, 보안 계약
- `plugins/careerfill/README.md`: v0.1 사용 순서와 제한

## 검증

- 플러그인 validator 통과
- 세 스킬 quick validator 통과
- Python AST, JSON, YAML, Markdown 참조 경로 정적 검사 통과
- `git diff --check` 통과

사용자 지시에 따라 프론트엔드 빌드와 테스트 스위트는 실행하지 않았다. 실제 CareerVault 인덱싱, 로그인된 Chrome 지원서 분석, 브라우저 입력·첨부·제출은 라이브 검증으로 주장하지 않는다.
