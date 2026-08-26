# news2shorts 근거 기반 반응·토론형 결론 카드 개선 완료

## 완료 내용

- 논쟁 뉴스의 마지막 장면을 `확인된 결론 → 출처가 있는 현재 반응 → 맥락형 질문` 순서로 구성하도록 개선했다.
- `discussion_prompt` 필드를 추가해 사실 결론과 댓글 유도 질문을 서로 다른 시각 계층으로 표시한다.
- 질문은 `이게 맞나요?`만 단독으로 쓰지 않고 `청년 주거 대책으로, 이게 맞나요?`처럼 주제를 포함하도록 했다.
- 시민 전체의 합의나 반발로 일반화하지 않고 팩트시트가 뒷받침하는 보도 귀속 반응만 사용하도록 Skill과 플레이북을 보강했다.
- 질문은 완결된 사실 결론 다음에만 내레이션으로 읽도록 해 결론을 질문으로 대체하지 않게 했다.
- 행정 식별번호 억제 대상에 `discussion_prompt`를 포함하고, 질문 부호 누락과 36자 초과를 검증 경고로 추가했다.
- 기존 `discussion_prompt`가 없는 프로젝트의 결론 카드 배치는 그대로 유지한다.

## 현재 버스하우스 프로젝트 반영

- 팩트시트에 청년 주거를 가볍게 봤다는 비판과 이후 게시물 삭제·사과를 보도 귀속 주장으로 추가했다.
- 마지막 카드에 다음 문구를 적용했다.
  - 결론: `비판 속 철회된 개인 제안입니다`
  - 반응: `청년 주거를 가볍게 봤다는 비판 뒤 게시물을 삭제하고 사과했습니다`
  - 질문: `청년 주거 대책으로, 이게 맞나요?`
- 서현 보이스와 Typecast `ssfm-v30`으로 새 검토본 `preview-v2.mp4`를 렌더했다.
- 기존 `preview.mp4`는 덮어쓰지 않았다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 새 결론 카드 3단 레이아웃, 필드 정리, 길이·질문형 검증
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 출처가 있는 반응과 사실 결론 이후 토론 질문 규칙
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: `discussion_prompt` 출력 계약
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`: 반응 일반화 금지와 토론형 마무리 원칙
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`: 결론·반응·질문 시각 계층과 길이 기준
- `plugins/news2shorts/skills/news2shorts/templates/storyboard.template.json`: `discussion_prompt` 기본 필드
- `plugins/news2shorts/README.md`: 사용자 동작과 사실 보호 규칙
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전 `0.10.0+codex.20260817`
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/`: 팩트시트, 대본, 스토리보드, 프로젝트 상태, 렌더 보고서, 새 검토 영상

## 검증

- Skill Creator `quick_validate.py` 원본과 설치본 통과
- CLI 도움말과 프로젝트 일반 검증 통과: 오류 0건, 경고 0건
- 플러그인 매니페스트·템플릿·프로젝트 JSON 파싱 통과
- 새 결론 카드의 실제 렌더 프레임에서 제목·반응·질문·출처가 겹치거나 잘리지 않음을 육안 확인
- `preview-v2.mp4`: 720x1280, H.264/AAC, 25.150초, Typecast 서현, 렌더 경고 0건
- 설치본 `news2shorts@news2shorts-local` 버전 `0.10.0+codex.20260817`, installed/enabled 확인
- 원본과 설치 캐시의 CLI·Skill SHA-256 일치 확인

## 미실행 범위

- 정치 소재의 사용자 편집 승인 전이므로 최종 `short.mp4`는 생성하지 않았다.
- 업로드·게시, 프론트엔드 빌드, DB 작업은 수행하지 않았다.
