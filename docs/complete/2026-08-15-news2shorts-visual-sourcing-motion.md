# news2shorts 시각 소싱·모션 개선 완료

## 완료 내용

- 플러그인 버전을 `0.6.0+codex.20260815`로 올리고 Codex 설치 캐시를 갱신했다.
- 생성 이미지를 기본 720x1280 이하로 축소하는 `optimize-images` 명령과 최종 크기 검증을 추가했다.
- 소유·공식·퍼블릭 도메인·상업 이용 가능한 라이선스 자산을 생성 이미지보다 먼저 검토하도록 제작 순서를 강화했다.
- 생성 이미지는 현실적인 편집 사진풍 또는 평면 픽토그램 중 하나를 사용하고, 네온·홀로그램·로봇·광택 3D 아이콘 같은 전형적인 AI 표현을 피하도록 프롬프트 지침을 추가했다.
- 정지 장면에 `zoom-in`, `zoom-out`, `none`과 `focus_x`, `focus_y`를 지원하도록 렌더러를 확장했다.
- 이미지 모션과 텍스트 오버레이를 분리해 줌 중에도 상단 헤드라인과 하단 자막이 고정되도록 했다.
- 상단 헤드라인을 더 큰 ExtraBold 계열 글꼴과 중앙 정렬로 변경했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
- `plugins/news2shorts/.codex-plugin/plugin.json`
- `plugins/news2shorts/README.md`
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
- `plugins/news2shorts/skills/news2shorts/references/rights-policy.md`
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`
- `plugins/news2shorts/skills/news2shorts/templates/storyboard.template.json`

## 검증 결과

- Python 문법 검사 통과
- Skill `quick_validate.py` 원본 및 설치 캐시 검사 통과
- JSON 형식 검사 통과
- 복사 프로젝트의 생성 이미지 10장을 941x1672에서 720x1279로 정규화
- 줌인·줌아웃·고정 모션을 포함한 1080x1920 H.264/AAC 검토 영상 렌더 성공
- 상단 헤드라인의 굵기, 중앙 정렬, 모션 중 고정 상태를 프레임 비교로 확인
- 설치 캐시와 저장소 플러그인 내용 일치 확인
- Typecast 키체인 설정과 고정 Voice ID 유지 확인
- 프론트엔드 빌드는 수행하지 않았다.
