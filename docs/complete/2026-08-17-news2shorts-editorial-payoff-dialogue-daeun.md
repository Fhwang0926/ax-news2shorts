# news2shorts 편집형 결론·대화 흐름·다은 보이스 개선 완료

## 완료 내용

- 일반 하단 외곽선 자막 위에 `결론` 배지를 띄우던 구성을 새 프로젝트에서 사용하지 않도록 변경했다.
- payoff 장면을 반투명 편집 카드로 분리하고 `payoff_title`의 직접 답과 `payoff_detail`의 실용적 의미·확인 조건을 서로 다른 시각 계층으로 표시한다.
- 새 프로젝트는 `visual_style.payoff_panel_style: "editorial-card"`를 기본 사용하며, 기존 프로젝트는 해당 옵션이 없으면 종전 렌더링을 유지한다.
- 최종 검증에서 편집형 결론 카드의 `payoff_title`과 `payoff_detail` 누락을 차단하고 긴 문구는 경고한다.
- 장면 대사를 독립적인 뉴스 문장 목록이 아니라 질문, 반전, 응답이 다음 장면으로 이어지는 대화형 릴레이로 작성하도록 Skill과 플레이북을 보강했다.
- Typecast 공식 인기 캐릭터 Top5 안내와 실제 `/v2/voices` API 메타데이터를 비교해 기본 보이스를 지훈에서 다은으로 변경했다.
  - 이름: `Daeun`(다은)
  - Voice ID: `tc_692799c46508f6b9468c54c7`
  - 공식 API 용도: `TikTok/Reels/Shorts`, `Conversational`
  - 공개된 바이럴 성과 수치는 없으므로 형식 적합도에 따른 기본값으로만 사용한다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 편집형 결론 카드 렌더링·검증, 다은 Voice ID와 이름 반영
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 대화형 대사 연결, 결론 카드 필드, 다은 보이스 운용 규칙 반영
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`: 장면 간 대화 릴레이 규칙 추가
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`: 결론 카드 레이아웃과 글자 길이 기준 추가
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: 새 필드와 최종 검증 계약 추가
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`: 편집형 결론 카드 기본값 추가
- `plugins/news2shorts/skills/news2shorts/templates/storyboard.template.json`: `payoff_title`, `payoff_detail` 필드 추가
- `plugins/news2shorts/README.md`: 결론·대사·보이스 사용법 갱신
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전 `0.8.0+codex.20260817`과 기능 설명 갱신

## 검증

- Skill 구조 검사 통과
- CLI 도움말 실행 및 JSON 템플릿 파싱 통과
- 새 프로젝트 초기화 시 `payoff_panel_style: "editorial-card"` 기본값 확인
- 기존 에어컨 프로젝트의 마지막 사진으로 결론 프레임을 샘플 렌더해 제목, 설명, 자산 크레딧, 뉴스 출처가 겹치거나 잘리지 않음을 육안 확인
- 다은 보이스로 Typecast WAV 샘플 생성 성공: PCM 16-bit mono, 44.1kHz, 7.857초
- 기존 에어컨 v2 프로젝트 최종 검증 통과: 오류 0건, 기존 출처 게시일 누락 경고 2건
- 설치본과 소스의 CLI·Skill SHA-256 일치 확인
- 설치본 `doctor`에서 Keychain API 키, 다은 Voice ID, FFmpeg, FFprobe, Pillow, 한글 폰트 정상 확인
- `news2shorts@news2shorts-local`을 `0.8.0+codex.20260817`로 재설치 완료

## 조사 근거

- Typecast 공식 인기 캐릭터 Top5: https://typecast.ai/kr/learn/typecast-new-editor-characters/
- Typecast 공식 캐릭터 목록 API: https://typecast.ai/docs/ko/api-reference/voices/list-voices

## 미실행 범위

- 기존 완성 MP4는 덮어쓰지 않았다.
- 프론트엔드 빌드와 DB 작업은 수행하지 않았다.
