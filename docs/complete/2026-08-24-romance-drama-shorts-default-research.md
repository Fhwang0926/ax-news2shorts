# 연애 드라마 Shorts 기본 리서치 계약 적용 완료

## 요청

- 사용자가 한·미·일, 플랫폼, 후보 수, 제목 공식, 출력 항목과 Candidate ID 대기를 매번 길게 입력하지 않아도 같은 리서치 방식이 기본으로 동작하게 한다.

## 반영 내용

- `연애 쇼츠 찾아줘`, `연애 소재 조사해줘`, `요즘 웹드라마 후보 보여줘` 같은 짧은 요청에도 리서치 기본 계약을 자동 적용한다.
- 기본 국가는 미국·한국·일본이며 YouTube Shorts·TikTok·Instagram Reels의 9개 국가·플랫폼 조합을 모두 확인한다.
- 나라별 최대 10개, 최근 30일 우선, 부족한 국가만 90일까지 확장한다.
- 제목은 `왜 ○○할까?`, `○○하는 사람의 심리`, `○○할 때 나타나는 신호 3가지` 중 하나만 사용한다.
- URL, 제작자, 게시일, 공개 반응, 줄거리 요약, 대본·자막 가능 여부, 권리 상태와 기존 근거·스토리 비트를 기본 출력한다.
- 후보를 자동 선택하지 않고 나라별 결과를 제시한 뒤 Candidate ID 선택에서 멈춘다.
- 사용자가 국가·플랫폼·개수·기간 중 일부를 지정하면 그 항목만 덮어쓰고 나머지 기본값은 유지한다.
- 플러그인 카드의 첫 시작 문구도 `최근 연애·웹드라마 쇼츠 후보를 조사해줘.`로 단순화했다.

## 변경 파일

- `plugins/romance-drama-shorts/skills/romance-drama-research/SKILL.md`: 짧은 요청에 적용되는 기본 리서치 계약과 부분 재정의 규칙 추가.
- `plugins/romance-drama-shorts/skills/romance-drama-research/agents/openai.yaml`: 기본 스킬 호출 문구에 전체 기본 계약 연결.
- `plugins/romance-drama-shorts/.codex-plugin/plugin.json`: 기본값 설명과 짧은 시작 문구 반영.
- `plugins/romance-drama-shorts/README.md`: 짧은 사용 예시와 자동 적용 항목 설명.

## 검증

- Skill 구조, 플러그인 매니페스트, JSON 형식과 `git diff --check` 검증을 통과했다.
- 캐시 버전을 `0.1.0+codex.20260824122314`로 갱신해 로컬 마켓플레이스에 재설치했다.
- 설치 상태가 `installed, enabled`인지 확인하고 설치본과 소스의 리서치 Skill·매니페스트 SHA-256 일치를 확인했다.
- 설치본 `doctor --json`에서 미국·한국·일본, 나라별 10개, 30일 우선·90일 확장 기본값을 확인했다.
- 실제 외부 플랫폼 리서치, Typecast 호출, 영상 렌더와 YouTube 업로드는 수행하지 않는다.
- 프론트엔드 빌드와 DB 작업은 대상이 아니며 실행하지 않는다.
