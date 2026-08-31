# news2shorts 제목·설명 중복 제거

## 완료 내용

- 새 `publish.json` 기본 버전을 5로 올렸다.
- 제목은 한 줄 질문·호기심 훅, 설명은 검증된 답·근거·조건·확인사항으로 역할을 분리했다.
- version 5 설명에 해시태그가 있거나 제목 문장이 그대로 반복되면 검증에서 경고 또는 오류로 처리한다.
- 기존 프로젝트의 업로드 패키지는 설명 해시태그와 제목 반복 문장을 출력 시 자동 제거한다.
- 설명의 링크·제작 내부 문구 제거와 기존 version 4 호환은 유지했다.
- 플러그인 버전을 `0.36.4+codex.20260827132439`로 올리고 설치 캐시를 갱신했다.

## 반영 파일

- `plugins/news2shorts/scripts/news2shorts.py`
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
- `plugins/news2shorts/skills/news2shorts/references/upload-package.md`
- `plugins/news2shorts/README.md`
- `plugins/news2shorts/.codex-plugin/plugin.json`
- `projects/2026-08-27-interest-rate-again/publish.json`

## 현재 프로젝트 문구

- 제목: `또? 또?? 또??? 내 대출은 언제?`
- 설명: 제목을 반복하지 않고 기준금리 결정, 상품별 반영 차이, 조건부 전체 이자 추산과 확인 항목만 작성했다.
- 설명의 중복 해시태그는 제거하고 태그는 제목 자동 보완과 별도 태그 필드에만 유지했다.

## 검증

- Python 구문 검사 통과
- 제목 반복 문장과 설명 해시태그 자동 제거 단위 확인 통과
- 현재 금리 프로젝트 검증: 오류 0건, 경고 0건
- Plugin validator 통과
- Skill validator 통과
- manifest·marketplace JSON 검사 통과
- `git diff --check` 통과
- 소스와 설치 캐시의 `news2shorts.py` SHA-256 일치
- 설치 캐시의 실제 `upload-package` 출력에서 제목·설명 중복 제거 확인

영상·음성·장면 구성은 변경하지 않았으므로 기존 검토 영상은 다시 렌더하지 않았다.
