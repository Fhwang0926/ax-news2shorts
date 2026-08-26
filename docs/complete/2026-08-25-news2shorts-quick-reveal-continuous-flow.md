# news2shorts quick-reveal continuous-flow 전용화 및 결과물 제작

## 완료 내용

- 새 프로젝트의 사용자 노출 포맷을 `quick-reveal` 하나로 제한했다.
- 새 프로젝트에 `delivery_mode: continuous-flow`를 고정하고 본문 내레이션 전체를 Typecast 한 요청으로 합성하도록 렌더러를 변경했다.
- 합성한 연속 음성을 구절 길이에 따라 장면 큐로 나누고, 하드 컷 이미지 위에 다시 입혀 장면별 TTS 이음새를 제거했다.
- 새 프로젝트의 장면별 `audio`를 금지하고, continuous-flow에서는 모든 `voice_delivery`를 `auto`로 유지하도록 검증 규칙과 문서를 맞췄다.
- 기존 fact-stack, story-explainer 등은 과거 프로젝트 재렌더 호환을 위해 내부에서만 유지하고 새 프로젝트 CLI 선택지에서는 제거했다.
- 플러그인 안내 문구와 기본 프롬프트를 quick-reveal·continuous-flow 기준으로 갱신했다.
- 플러그인 버전을 `0.32.0+codex.20260825111653`으로 올리고 로컬 설치 캐시를 갱신했다.

## 결과물

- 프로젝트: `projects/2026-08-25-hyundai-wage-vote-continuous-flow`
- 주제 발견: 2026-08-25 네이버 뉴스스탠드의 현대차 노사 잠정합의 헤드라인
- 사실 확인: 한국일보·한국경제 교차 확인
- 최종 영상: 720×1280, 28.976초, H.264/AAC
- 본문 음성: Typecast Piljae, 본문 TTS 요청 1회, 22.0초 연속 트랙
- 시각 자료: 기사 사진 미사용, 서로 다른 권리 승인 실제 사진 6장
- 결론: 8월 31일 조합원 찬반투표 전에는 최종 지급 확정이 아님

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 새 프로젝트 포맷 제한, 연속 음성 합성·큐 분배·리먹싱·보고서 기록
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: quick-reveal·continuous-flow 전용 제작 지침
- `plugins/news2shorts/skills/news2shorts/agents/openai.yaml`: 사용자 설명과 기본 프롬프트
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`: version 12·continuous-flow 기본값
- `plugins/news2shorts/skills/news2shorts/templates/storyboard.template.json`: quick-reveal 고정값
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: 연속 음성 출력·검증 계약
- `plugins/news2shorts/skills/news2shorts/references/reference-formats.md`: 신규 포맷 범위
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`: 신규 시각 형식 범위
- `plugins/news2shorts/README.md`: 실행 예시와 호환성 경계
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전과 UI 설명
- `projects/2026-08-25-hyundai-wage-vote-continuous-flow/*`: 근거, 권리, 스토리보드, 영상, 썸네일, 편집 패키지, 업로드 문구

## 검증

- Python 문법 검사 통과
- JSON 파싱 통과
- skill-creator 빠른 검증 통과
- 새 `init --help`의 포맷 선택지가 `{quick-reveal}`만 노출됨
- 프로젝트 최종 검증 오류·경고 0건
- Typecast 키체인 접근 확인
- 최종 `render-report.json`: `continuous_flow.enabled=true`, `body_tts_requests=1`, `audio_source=typecast-continuous`
- 최종 영상 blackdetect 이상 없음
- 원본과 설치 캐시의 렌더 스크립트·SKILL.md SHA-256 일치
- 프론트엔드 빌드와 외부 업로드는 수행하지 않음

## 호환성 경계

- 기존 프로젝트의 과거 포맷 재렌더는 유지한다.
- 새 프로젝트 본문만 한 호흡 Typecast 트랙이다. 공통 3.15초 인트로와 마지막 CTA는 기존 공용 자산·별도 음성을 유지한다.
- YouTube 업로드는 수행하지 않았으며 업로드 설정은 비공개로 준비했다.
