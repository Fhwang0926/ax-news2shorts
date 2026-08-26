# 2026-08-19 Viral Shorts 로컬 쇼츠 렌더 확장 작업 완료

## 작업 범위

- `viral-shorts` 플러그인을 영상 후보 탐색·장면 분석에서 사용자가 선택한 장면의 로컬 검토용 9:16 MP4 렌더까지 확장했다.
- 영상 후보 선택과 장면 후보 선택을 서로 다른 사용자 게이트로 유지했다.
- YouTube Data API, API key, 브라우저 쿠키, 로그인을 사용하지 않는 공개 원본 취득 명령을 추가했다.
- 공개 자막, 메타데이터, 스토리보드를 출처 근거 자산으로 보존하고 SHA-256을 기록하도록 했다.
- YouTube의 공개 다운로드가 HTTP 403으로 막힐 때는 원격 EJS 구성요소를 자동 실행하지 않고, `--allow-remote-ejs`와 사용자 승인 메모가 모두 있을 때만 허용하도록 했다.
- 렌더는 원본음, 한국어 후킹, 자막, 흐린 9:16 배경과 원본 화면을 결합하고 `로컬 검토용`을 표시하도록 했다.
- 결과 계약을 720x1280, H.264, AAC로 검사하고 렌더 보고서에 해시와 선택 구간을 남기도록 했다.

## 아이브 제작 프로젝트

- 사용자가 선택한 ootb STUDIO의 `단독) 아이브 장원영 군입대 현장 공개 [서경대 군사학과] | 전과자 ep.97`을 프로젝트로 초기화했다.
- Codex Browser Use로 재생 화면과 공개 댓글의 타임스탬프 반응을 확인했다.
- 공개 한국어 자막 1,808개 구간과 스토리보드 근거를 로컬 저장했다.
- 겹치는 구간을 제거한 쇼츠 후보 3개를 사건 정규화, 자막, 화면, 공개 반응 근거로 점수화했다.
- 현재는 장면 후보 사용자 선택 전이며, 원본 MP4 공개 취득은 YouTube HTTP 403으로 완료되지 않았다.
- 원격 EJS 실행은 공급망 위험이 있어 명시적 사용자 승인 없이 수행하지 않았다. 따라서 최종 MP4도 아직 생성하지 않았다.

## 검증

- Python 소스를 AST로 정적 파싱했다.
- Skill validator와 Plugin validator를 실행했다.
- CLI `--help`, `doctor`, 프로젝트 `validate`를 실행했다.
- 소스와 설치 캐시의 `viral_shorts.py` SHA-256 일치 여부를 확인했다.
- 현재 구동 중인 Browser Use 세션을 기준으로 YouTube 화면을 확인했다.
- 프론트엔드 빌드·테스트와 DB 작업은 수행하지 않았다.
- 최종 MP4 기술 검증은 장면 선택과 원본 취득 후 수행할 예정이다.

## 변경 파일

- `README.md`
- `plugins/viral-shorts/.codex-plugin/plugin.json`
- `plugins/viral-shorts/README.md`
- `plugins/viral-shorts/scripts/viral_shorts.py`
- `plugins/viral-shorts/skills/viral-shorts/SKILL.md`
- `plugins/viral-shorts/skills/viral-shorts/agents/openai.yaml`
- `plugins/viral-shorts/skills/viral-shorts/references/workflow.md`
- `plugins/viral-shorts/skills/viral-shorts/references/rights-policy.md`
- `plugins/viral-shorts/skills/viral-shorts/references/output-contract.md`
- `docs/complete/2026-08-19-viral-shorts-local-render.md`
- `projects/viral-shorts/2026-08-19-ive-wonyoung-military-variety/`
