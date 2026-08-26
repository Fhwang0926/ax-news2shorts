# 2026-08-16 Story2Short 원본 취득 흐름 고도화 완료

## 작업 범위

- 로컬 영상이 없어도 Story2Short 작업을 시작할 수 있도록 입력 방식을 공개 영상 URL, 기존 Shorts 프로젝트, 로컬 영상 세 가지로 확장했다.
- 원본이 전혀 없는 요청은 기존 `tiktok2shorts` 스킬로 공개 바이럴 후보를 최대 3개 조사한 뒤 사용자가 선택하고, 선택된 프로젝트를 Story2Short로 가져오는 흐름으로 연결했다.
- `init --source-url`은 URL과 권리 상태만 먼저 기록하고, 별도 `acquire` 명령에서 단일 공개 원본을 취득하도록 분리했다.
- 공개 URL 취득은 HTTP(S), 비로그인, 비쿠키, 단일 영상, 기존 파일 비덮어쓰기 조건으로 제한했다. 사용자 정보가 포함된 URL과 로컬·사설·예약 IP 주소는 거부한다.
- `init --source-project`로 TikTok2Shorts 또는 기존 Story2Short 프로젝트의 원본 영상을 복사하고 원본 URL, 제작자, 플랫폼, 권리 상태, 메타데이터, SHA-256, 후보 정보와 다운로드 출처를 보존한다.
- 공개 URL이나 기존 프로젝트의 기술적 취득 성공이 게시 권리를 뜻하지 않도록 `local_personal_use`와 `rights_cleared` 취득 범위를 분리했다.
- 원본이 아직 없는 `source_pending` 프로젝트는 샘플링·렌더 전에 명확히 중단하고 `acquire` 실행을 안내하도록 했다.
- 플러그인 설명, 기본 프롬프트, 권리 정책, 출력 상태 계약, 사용 문서를 새 입력 흐름에 맞게 갱신했다.

## 검증 경계

- Python 구문 검사와 CLI 도움말·doctor 실행을 완료했다.
- 기존 TikTok2Shorts 프로젝트를 임시 Story2Short 프로젝트로 가져와 원본 파일, 메타데이터, 권리 상태, 출처 이력과 SHA-256이 보존되는 것을 확인했다.
- 가져온 59.669초 원본에서 5초 간격 분석 프레임 4개와 접촉시트를 생성해 후속 분석 경로를 확인했다.
- 기존 Story2Short v0.1 프로젝트가 새 도구에서 검증을 통과하는지 확인하고, 같은 4장면을 16.021초 H.264/AAC 720x1280 검토 영상으로 다시 렌더링해 하위 호환성을 확인했다.
- 공개 URL의 `source_pending` 초기화와 원본 미취득 검증 오류를 확인했다.
- `not_permitted` 원본의 자동 취득 차단과 로컬·사설 URL 차단을 확인했다.
- 실제 외부 URL 재다운로드는 수행하지 않았다. `yt-dlp` 모듈 탐지와 기존에 취득된 프로젝트 가져오기까지 확인한 상태다.
- Plugin/Skill 구조 검사를 통과한 `0.2.0+codex.20260815160248`을 `story2short@news2shorts-local`로 재설치하고, 설치 캐시의 doctor 실행과 원본 스크립트 SHA-256 일치를 확인했다.
- 프론트엔드 변경, 빌드, 브라우저 테스트, DB 작업, 외부 업로드는 수행하지 않았다.

## 변경 파일

- `README.md`
- `plugins/story2short/.codex-plugin/plugin.json`
- `plugins/story2short/scripts/story2short.py`
- `plugins/story2short/README.md`
- `plugins/story2short/skills/story2short/SKILL.md`
- `plugins/story2short/skills/story2short/agents/openai.yaml`
- `plugins/story2short/skills/story2short/references/output-contract.md`
- `plugins/story2short/skills/story2short/references/rights-policy.md`
- `docs/complete/2026-08-16-story2short-source-acquisition.md`
