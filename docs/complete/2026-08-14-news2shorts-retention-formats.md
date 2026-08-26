# news2shorts 집중 유지 포맷 반영 완료

## 요청 반영

- 사용자 제공 쇼츠와 채널별 편집 패턴을 분석해 복제하지 않고 공통 유지 원리를 추출했다.
- 정확한 정보 전달만으로 끝내지 않고 반전, 대비, 결과 선공개, 증거 누적, 중간 재후킹, 최종 보상으로 재미와 집중을 유지하도록 제작 규칙을 강화했다.
- 참사, 범죄 피해, 미성년자, 건강 위기 등 민감한 소재는 농담이나 과장 대신 명확한 전개와 검증된 보상만 사용하도록 제한했다.

## 포맷과 후킹

- 후킹 전략을 화면 포맷과 분리했다.
- 후크 유형으로 `counterintuitive`, `result-first`, `comparison-reversal`, `change-impact`, `numeric-gap`을 추가했다.
- 프로젝트의 `shorts_profile`에 선택 후크, 오픈 루프, 중간 재후킹, 보상, 선택적 루프 종료를 기록한다.
- 신규 포맷을 추가했다.
  - `quick-reveal`: 12-35초, 4-9장면
  - `fact-stack`: 20-55초, 6-12장면
  - `story-explainer`: 35-120초, 8-20장면
- 기존 `broadcast-card`, `classic-card`는 이전 프로젝트 호환용으로 유지했다.

## 사용자 확인 흐름

- 뉴스 후보 수집과 교차검증이 끝난 뒤 주제와 결과물 범위를 확인하는 기존 게이트를 유지했다.
- 대본 이상을 제작하고 포맷이 지정되지 않았으면 주제에 맞는 세 포맷을 추천 순서로 보여주고 사용자 선택을 받도록 했다.
- Codex 기본 사용자 선택 입력을 사용할 수 있으면 주제, 범위, 포맷을 한 번에 최대 세 문항으로 확인한다.

## 이미지와 영상 자산

- 스토리보드 장면에 `beat`, `progress`, `fact_index`, `video`, `video_start`, `motion` 필드를 추가했다.
- 신규 포맷에서 프로젝트 내부 영상 클립을 9:16으로 채우기 크롭하고, 장면 길이로 자르고, 짧은 클립은 마지막 프레임을 유지하도록 렌더링한다.
- 영상 원본 음성 대신 검증된 내레이션 트랙을 사용한다.
- 정적 이미지는 기본적으로 미세한 줌을 사용하며 문서나 차트는 `motion: "none"`으로 고정할 수 있다.
- 웹 검색으로 확보한 이미지와 영상은 같은 권리 매니페스트에서 원본 페이지, 제작자·게시자, 라이선스 또는 사용 근거, 표시 문구, 수집 시각을 검사한다.
- 검색 결과 썸네일, 임베디드 플레이어 캡처, 권리 불명 클립은 사용할 수 없다.

## 집중 유지 검증

- 첫 장면의 `beat: "hook"`, 포맷별 장면 길이, 전체 권장 길이와 장면 수를 검사한다.
- `fact-stack`과 `story-explainer`는 중간 `rehook` 또는 `turn`을 요구한다.
- 모든 신규 포맷은 오프닝 약속을 회수하는 `payoff` 장면을 요구한다.
- 긴 한 화면 자막, 연속된 동일 자산, 실제 이미지나 영상이 없는 장면을 경고하거나 최종 렌더에서 차단한다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 포맷·후크 스키마, 집중 유지 검증, 정적 모션, 영상 클립 렌더 추가
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 포맷 확인과 집중 유지 제작 흐름 추가
- `plugins/news2shorts/skills/news2shorts/references/reference-formats.md`: 채널별 패턴과 포맷 라우터 추가
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`: 후크 엔진과 장면별 집중 유지 규칙 추가
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`: 신규 3개 포맷과 영상 장면 계약 추가
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: 신규 프로젝트·스토리보드 필드 추가
- `plugins/news2shorts/skills/news2shorts/references/rights-policy.md`: 웹 영상 검색과 클립 권리 기준 추가
- `plugins/news2shorts/skills/news2shorts/templates/*.json`: 신규 기본 포맷과 장면 필드 추가
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전과 사용자 설명 갱신
- `README.md`, `plugins/news2shorts/README.md`: 기능과 사용 예시 갱신

## 확인 결과

- Python 구문 검사 통과
- Codex Skill 구조 검사 통과
- 플러그인·마켓플레이스·템플릿 JSON 형식 검사 통과
- `doctor` 필수 렌더 환경 확인 통과
- 이미지 1장과 1.2초 영상 클립을 섞은 대표 검토본 렌더 통과
- 대표 검토본 4.154초, 1080x1920, H.264 영상, AAC 음성 확인
- 이미지와 영상 프레임에서 헤드라인, 강조색, 진행 표시, 자막, 출처, 합성 이미지 표시, 검토용 워터마크 시각 확인
- 로컬 Codex 플러그인 재설치 성공: `news2shorts@news2shorts-local` 버전 `0.4.0+codex.20260814`, enabled 상태 확인
- 프론트엔드 변경과 빌드·테스트는 수행하지 않았다.
