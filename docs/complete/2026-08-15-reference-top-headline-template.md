# 30초 정보형 쇼츠 템플릿 반영 완료

## 반영 내용

- 제공된 쇼츠 분석에서 추출한 공통 정보 위계를 모든 신규 집중 유지형 포맷에 적용했다.
  - 검은색 상단 약 25% 영역의 고정 2줄 헤드라인
  - 헤드라인의 한 핵심 구절만 노란색으로 강조
  - 장면별로 바뀌는 중앙 증거 이미지 또는 영상
  - 검은색 외곽선을 둔 하단 노란 자막
- 새 프로젝트 기본값을 30초 `fact-stack`으로 바꾸고, 고정 헤드라인은 프로젝트 제목으로 초기화한다.
- `quick-reveal`, `fact-stack`, `story-explainer`는 이제 서사 구조만 선택하며 동일한 화면 템플릿을 사용한다.
- 새 집중 유지형 프로젝트는 렌더 명령에서도 레거시 화면 포맷으로 바꿀 수 없게 했다.
- 신규 집중 유지형 장면은 4초를 넘으면 검증 경고를 내도록 조정했다.
- 기존 `broadcast-card`, `classic-card`는 기존 결과물의 렌더 호환성을 위해 남겼다.

## 참고 및 경계

- 참조 쇼츠의 로고, 원본 영상, 음성, 음악, 폰트, 자막 문구, 장면 순서는 재사용하지 않는다.
- 기사·사진·영상의 출처, 사용권, 합성 미디어 표시는 기존 검증 절차를 그대로 적용한다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
- `plugins/news2shorts/.codex-plugin/plugin.json`
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`
- `plugins/news2shorts/skills/news2shorts/templates/storyboard.template.json`
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`
- `plugins/news2shorts/skills/news2shorts/references/reference-formats.md`
- `plugins/news2shorts/README.md`
- `README.md`
