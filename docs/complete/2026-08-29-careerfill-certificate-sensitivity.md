# CareerFill v0.3.1 자격증·민감자료 분류 보완

## 목적

`/Users/hdh/Documents/Resume/`처럼 평평한 폴더에서도 자격증 약칭 파일을 S2 증적 후보로 분류하고, 병적증명서와 증명사진을 S3로 차단하도록 CareerFill 분류 규칙을 보완했다.

## 반영 내용

- macOS NFD 한글 파일명을 NFC로 정규화한 뒤 분류
- 다음 자격증 표식을 S2로 추가
  - 국가기술자격, 기능사
  - 정보처리기사, 정보보안산업기사
  - 컴퓨터활용능력, 컴활
  - ITQ, GTQ, DAsP, 데이터아키텍처
  - 리눅스마스터, 네트워크관리사
- 다음 민감 표식을 S3로 추가
  - 병적, 병역, 군복무
  - 증명사진, 프로필사진, 신분사진

## 안전 경계

- 원본 Resume 폴더 쓰기 금지
- S2 자격증은 `candidate_only`, `content_verified: false` 유지
- S3 병적증명서·증명사진은 Claim과 Evidence 검색 대상에서 제외
- 자격증 자동 첨부 및 Claim 자동 승인 금지
- 데이터베이스 생성·초기화·재설정 없음

## 검증 범위

- 플러그인 validator
- Python AST·JSON 정적 검사
- `git diff --check`
- 실제 Resume 폴더 인덱싱 후 문서별 sensitivity와 evidence 상태 확인

사용자 지시에 따라 빌드와 테스트 스위트는 실행하지 않는다.
