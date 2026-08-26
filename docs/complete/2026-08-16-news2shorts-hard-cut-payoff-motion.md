# news2shorts 하드 컷·결론·모션 개선 완료

## 반영 내용

- 정지 이미지와 영상 장면의 페이드 인·아웃을 제거하고 모든 장면을 하드 컷으로 연결했다.
- 초안 렌더의 화면 내 `검토용` 표시를 제거했다. 초안 여부는 `preview.mp4`, `project.json`, `render-report.json`에만 남는다.
- 마지막 `payoff`에 현재 답과 영향 또는 다음 조건을 완결된 문장으로 요구하고, 추상적인 결론을 검증 경고로 잡도록 했다.
- 핵심 `hook`, `turn`, `impact`, `payoff` 장면에 목적 있는 `zoom-in` 또는 `zoom-out`이 없으면 검증 경고를 표시하도록 했다.
- 렌더 보고서에 `scene_transition: "cut"`을 기록한다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/references/editorial-policy.md`
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`
- `plugins/news2shorts/.codex-plugin/plugin.json`
- `plugins/news2shorts/README.md`

## 확인 결과

- Python 구문 검사 통과
- Skill `quick_validate.py` 검사 통과
- 기존 프로젝트 검증에서 추상적인 결론 경고 발생 확인
- 임시 프로젝트 렌더 성공: 720x1280 H.264/AAC, 화면 내 초안 표시 없음
- 장면 경계 전후 프레임에서 페이드 없이 하드 컷 확인
- 렌더 보고서의 `scene_transition: "cut"`과 장면별 모션 기록 확인
- 재설치 버전: `news2shorts@news2shorts-local` `0.6.3+codex.20260816`
- 재설치 캐시에서도 Typecast 키체인과 고정 Voice ID `tc_61f0859907085fc68561c9a1` 인식 확인

## 범위

- 기존 제작 영상은 다시 렌더하지 않았다.
- 외부 업로드나 게시 작업은 수행하지 않았다.
