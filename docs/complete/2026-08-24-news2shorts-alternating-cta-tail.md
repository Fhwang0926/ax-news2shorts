# news2shorts 구독형·댓글형 CTA 자동 선택 완료

## 요청

- 마지막 후킹을 구독·좋아요형과 `여러분의 생각을 댓글로 남겨주세요` 댓글형으로 번갈아 사용한다.
- 결론을 약화하거나 민감 뉴스에 무리한 참여를 유도하지 않는다.

## 반영 내용

- 기존 단일 CTA 렌더러를 재사용해 `subscribe`와 `comment` 두 변형을 추가했다.
- 민감 뉴스는 항상 `subscribe`를 선택한다.
- 일반 뉴스의 마지막 결론에 검증된 `discussion_prompt`가 있으면 `comment`를 선택하고 해당 질문을 CTA 화면 제목으로 이어 쓴다.
- 질문이 없는 일반 뉴스는 프로젝트 정보의 SHA-256 두 버킷으로 구독형·댓글형을 1:1 배분한다. 같은 프로젝트의 재렌더 결과는 바뀌지 않는다.
- 댓글형은 화면에 `댓글로 한마디`, 음성 문구에 `여러분의 생각을 댓글로 남겨주세요.`를 사용한다. 주제 질문이 없을 때만 `여러분은 어떻게 보세요?`를 앞에 보완한다.
- CTA는 사실 결론 뒤에 정확히 한 번 붙고 결론을 대신하지 않는다.
- 프로젝트 template을 version 8로 올리고 댓글형 화면·음성 기본값을 기록했다.
- `doctor`와 `render-report.json`에 변형 목록, 선택 전략, 선택 이유, 배분·버킷 정보를 추가했다.
- 플러그인 버전을 `0.27.0+codex.20260824002750`으로 갱신했다.
- `news2shorts@news2shorts-local` 설치 캐시를 같은 버전으로 재설치했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: CTA 선택·안전 규칙·두 화면 렌더·보고서·최종 검사.
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`: version 8 댓글 CTA 기본값.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 제작 시 CTA 선택 기준.
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: project와 render-report 계약.
- `plugins/news2shorts/README.md`, `README.md`: 사용자 동작 설명.
- `plugins/news2shorts/.codex-plugin/plugin.json`: 0.27.0 버전과 기능 설명.

## 검증

- Python AST, JSON 파싱, Skill Creator `quick_validate.py`, `git diff --check` 통과.
- 선택 함수에서 일반 결론 질문 프로젝트가 `comment`, 같은 프로젝트의 민감 뉴스 설정이 `subscribe`로 바뀌는 것을 확인했다.
- 질문 없는 프로젝트의 SHA-256 구독형 bucket 0과 댓글형 bucket 1 및 동일 프로젝트 재선택 안정성을 확인했다.
- 기존 고시원 프로젝트 복사본 두 개를 `--draft --no-tts`로 실제 병렬 렌더했다.
- 댓글형 화면 `욕조가 먼저? / 댓글로 한마디`와 구독형 화면 `빠른 소식 계속 / 구독 · 좋아요`를 추출 프레임으로 육안 확인했다.
- 두 결과 모두 28.23초, 720x1280, H.264/AAC이며 공통 인트로와 CTA가 함께 유지됐다.
- 설치 캐시의 렌더러·Skill SHA-256이 원본과 일치했고 설치본 `doctor`와 댓글형 실제 렌더도 통과했다.
- `--no-tts` 테스트이므로 Typecast 과금 호출은 하지 않았다. 실제 Typecast 음성 합성은 기존 공통 CTA 경로를 그대로 사용하며 설치본에서 별도 외부 호출 검증이 필요하다.

## 범위

YouTube 업로드, 댓글 게시, 성과 측정, CTA별 조회·전환 분석은 변경하지 않았다. 1:1은 콘텐츠 질문이 없는 일반 프로젝트에 적용하는 편집 배분이며 성과 보장이 아니다.
