# news2shorts 결론·이미지 중복·해상도 개선 완료

## 완료 내용

- 플러그인 버전을 `0.6.1+codex.20260815`로 올리고 Codex 설치 캐시를 갱신했다.
- 마지막 본문 장면을 `payoff`로 두고 화면용 결론 자막을 요구하도록 제작 규칙과 검증을 강화했다.
- 후크와 결론의 문장 유사도가 높으면 후크 반복으로 판단해 초안에는 경고, 최종본에는 오류를 표시하도록 했다.
- 한 쇼츠 안에서 동일한 정지 이미지 경로를 다시 사용하면 렌더 전 검증이 실패하도록 했다.
- 기존 9:16 화면 구성은 유지하면서 MP4 기본 출력 해상도를 1080x1920에서 720x1280으로 낮췄다.

## 변경 파일

- `README.md`
- `plugins/news2shorts/scripts/news2shorts.py`
- `plugins/news2shorts/.codex-plugin/plugin.json`
- `plugins/news2shorts/README.md`
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`

## 확인 범위

- 코드와 문서의 1080x1920 기본 출력 참조를 720x1280으로 변경했다.
- Codex 플러그인 목록에서 설치 버전 `0.6.1+codex.20260815`를 확인했다.
- 자동 테스트와 실제 영상 렌더는 작업 지침에 따라 수행하지 않았다.
