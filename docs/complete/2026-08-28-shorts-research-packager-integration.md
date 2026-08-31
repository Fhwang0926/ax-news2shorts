# Shorts Discovery 리서치 패키징 통합 완료

## 완료 내용

- 기존 `shorts-discovery`의 후보 조사·점수화·사용자 Candidate ID 선택 경계를 유지했다.
- 같은 `shorts-suite` 플러그인에 선택 후 심층 조사 역할 `shorts-research-packager`를 추가했다.
- `shorts-discovery`가 `video_signal`과 `story_event`를 구분하도록 확장했다.
  - 사건형 후보에는 대상, 사건, 한 문장 결말, 사건 클러스터 ID, 패키징 점수 근거가 필요하다.
  - 뉴스·공식 페이지·커뮤니티도 조사 출처로 기록할 수 있다.
  - 사건형 후보는 단일 재사용 영상이 없어도 공개 근거로 패키징 가능하면 후보가 될 수 있다.
- 기존 Discovery 점수와 별도로 사건형 Package 점수를 계산하고, 두 점수를 분리해 표시하도록 했다.
- 선택된 Candidate ID에서 다음 구조를 초기화하고 검증하는 표준 라이브러리 CLI를 추가했다.
  - 출처 그래프
  - Claim 시트
  - 에셋 manifest
  - 선택적 댓글 원본·익명화 캡처 기록
  - Claim 연결 내레이션
  - 렌더러 중립 장면 timeline
  - 자막·보고서·검토 디렉터리
- `research`와 `handoff` 검증 단계를 분리했다.
  - handoff는 사실·권리 검토, 자막, 장면, 실제 로컬 에셋과 교차 파일 ID 연결을 요구한다.
  - 구조 검증이 통과해도 `publish_ready: false`, `publish_blocked: true`를 유지한다.

## 명령

```text
python3 plugins/shorts-suite/scripts/shorts_suite.py package doctor --json

python3 plugins/shorts-suite/scripts/shorts_suite.py package init \
  --shortlist <shortlist.json> \
  --candidate-id <selected-candidate-id> \
  --project-dir <package-dir>

python3 plugins/shorts-suite/scripts/shorts_suite.py package validate \
  --project-dir <package-dir> \
  --stage research|handoff
```

## 변경 파일

- `plugins/shorts-suite/scripts/research_package.py`: 선택 후보 패키지 초기화·교차 검증 CLI
- `plugins/shorts-suite/scripts/discover.py`: 사건형 후보·패키지 점수·사건 클러스터 지원
- `plugins/shorts-suite/scripts/shorts_suite.py`: `package` 역할 라우팅
- `plugins/shorts-suite/skills/shorts-research-packager/`: 패키징 스킬, 워크플로, 프로젝트 계약
- `plugins/shorts-suite/skills/shorts-discovery/`: 사건형 조사와 선택 후 인계 계약 보완
- `plugins/shorts-suite/skills/shorts-suite/`: 새 역할 라우팅 보완
- `plugins/shorts-suite/.codex-plugin/plugin.json`: 통합 기능 설명과 호출 예시 보완
- `plugins/shorts-suite/README.md`, `README.md`: 현재 역할 설명 갱신

## 보존 경계

- 후보를 자동 선택하지 않는다.
- 선택 전 모든 후보의 화면·댓글·에셋을 대량 보관하지 않는다.
- 공개 또는 정상 접근 권한 범위만 사용하며 로그인·CAPTCHA·유료벽·DRM·지역 제한을 우회하지 않는다.
- 댓글은 반응 증거로만 유지하고 독립 검증 없이 사실 Claim으로 승격하지 않는다.
- 권리 미확인·미검토 에셋은 로컬 검토만 허용하고 게시를 차단한다.
- 렌더링, 업로드, 게시, 권리 판정, DB, 스케줄러, 성과 자동 학습은 이번 범위에 포함하지 않았다.

## 검증 범위

- Plugin validator: 통과
- 변경된 Skill 3개 validator: 모두 통과
- `discover`, `research_package`, 공통 `package` 라우터 도움말·doctor: 정상 로딩
- 설치 버전: `shorts-suite@news2shorts-local` `0.1.0+codex.20260828092117`
- 설치본과 소스의 `research_package.py`, `shorts-research-packager/SKILL.md` SHA-256: 각각 일치
- 자동화 테스트, 프론트엔드 빌드, 영상 렌더, 외부 다운로드, DB 작업은 수행하지 않는다.
