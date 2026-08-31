# Shorts Globalizer v0.1 작업 완료

## 완료 내용

- `cc-helper`, `news2shorts`와 분리된 저장소 로컬 플러그인 `shorts-globalizer`를 추가했다.
- 단일 YouTube Shorts URL에서 공개 메타데이터와 한국어 자막만 수집하는 ingest 흐름을 구현했다.
- 자막은 수동 한국어를 우선하고 자동 한국어를 차선으로 선택한다. 자막이 없으면 `transcript_pending`으로 중단하며 사용자 제공 UTF-8 transcript만 대체 입력으로 허용한다.
- 원 Shorts를 사실 출처에서 제외하고, 일반 핵심 주장은 서로 다른 출처 도메인 2개 이상, 민감 핵심 주장은 공식·1차 출처 1개와 독립 출처 도메인 2개 이상을 요구하도록 검증했다.
- 고정 가중치와 감점, Origin 강제 판정을 적용하는 Global Potential Score를 구현했다.
- research/script 승인 게이트, 80~120단어 영문 대본, 8~10장면·30~40초 스토리보드, claim 연결 검증을 구현했다.
- LCS 기반 구조 유사도와 별도 의미 검토 결과가 `PASS`일 때만 package를 만들도록 Originality Guard를 구현했다.
- script, narration, SRT, 강조 자막, scenes, assets CSV, 검색 가이드, 출처·사실·원작성 자료, `global-short-v1` CapCut 인계 manifest를 프로젝트 안에 유지한다.
- 에셋 경로는 빈 값, 에셋 상태는 `planned`, `preview_approved: false`, `publish_blocked: true`로 고정했다.
- 저장소 README와 로컬 marketplace에는 신규 항목만 추가했고, 기존 플러그인 변경 내용은 수정하지 않았다.

## 변경 파일

- 저장소 등록
  - `.agents/plugins/marketplace.json`
  - `README.md`
- 플러그인 메타데이터와 안내
  - `plugins/shorts-globalizer/.codex-plugin/plugin.json`
  - `plugins/shorts-globalizer/README.md`
- 실행 코드
  - `plugins/shorts-globalizer/scripts/shorts_globalizer.py`
- Codex 스킬과 계약
  - `plugins/shorts-globalizer/skills/shorts-globalizer/SKILL.md`
  - `plugins/shorts-globalizer/skills/shorts-globalizer/agents/openai.yaml`
  - `plugins/shorts-globalizer/skills/shorts-globalizer/references/workflow.md`
  - `plugins/shorts-globalizer/skills/shorts-globalizer/references/editorial-and-rights.md`
  - `plugins/shorts-globalizer/skills/shorts-globalizer/references/project-contract.md`
  - `plugins/shorts-globalizer/skills/shorts-globalizer/templates/source-analysis.template.json`
  - `plugins/shorts-globalizer/skills/shorts-globalizer/templates/content-en.template.json`
  - `plugins/shorts-globalizer/skills/shorts-globalizer/templates/storyboard.template.json`
  - `plugins/shorts-globalizer/skills/shorts-globalizer/templates/originality.template.json`
- 테스트 fixture와 계약 테스트
  - `plugins/shorts-globalizer/tests/fixtures/caption-cases.json`
  - `plugins/shorts-globalizer/tests/fixtures/authorized-transcript-ko.txt`
  - `plugins/shorts-globalizer/tests/test_shorts_globalizer.py`

## 검증 결과

- `python3 -B -m unittest discover -s plugins/shorts-globalizer/tests -v`: 10개 테스트 통과
- Python 구문 검사: 통과
- 플러그인 validator: 통과
- 스킬 validator: 통과
- manifest와 marketplace JSON 구문 검사: 통과
- `doctor --json`: Python 3.14.5, 설치된 `yt_dlp` 모듈, 프로젝트 출력 경로 쓰기 가능 상태 확인
- CLI `--help`: `doctor`, `init`, `score`, `approve`, `validate`, `package` 노출 확인
- 프론트엔드 변경과 DB 작업은 없으며 프론트엔드 빌드는 수행하지 않았다.

## 미검증 및 범위 제한

- 라이브 YouTube URL에 대한 실제 네트워크 ingest는 실행하지 않았다. 공개 자막 가용성, YouTube 응답 제한, 지역·네트워크 상태는 fixture 테스트로 대체할 수 없다.
- CapCut Desktop/Web UI, 실제 draft 복제·수정, TTS, 에셋 다운로드, 영상 렌더링, 업로드·게시 기능은 v0.1 범위 밖이며 검증하지 않았다.
- 생성 package는 편집 인계용 초안이다. 에셋 권리 확인, 최종 미리보기 승인, 합성 콘텐츠 고지, 게시 승인은 별도 절차가 필요하다.
- 작업 시작 전부터 존재한 `cc-helper`, `news2shorts`, `s-finder` 및 기타 작업 트리 변경은 보존했다.
