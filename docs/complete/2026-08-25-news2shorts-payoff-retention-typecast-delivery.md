# news2shorts 마지막 붙잡기·Typecast 전달 개선

## 완료 일자

- 2026-08-25

## 요청과 원인

- 기존 결론 카드는 `확인된 사실 / 조사 중`을 다시 요약해 마지막 장면에서 새 보상이 약했다.
- 모든 장면이 같은 Typecast Smart Emotion 요청을 사용해 결론의 고저·속도 차이가 구조적으로 없었다.
- 민감 사고 뉴스에 무리한 분노·유머·밝은 반전을 넣지 않으면서도 마지막 이탈을 막는 재사용 규칙이 필요했다.

## 반영 내용

- 새 프로젝트를 project version 11, storyboard version 6으로 올렸다.
- 결론에 `payoff_punch`를 추가해 `확인된 답 → 실질 의미·다음 조건 → 마지막 붙잡기`를 서로 다른 역할로 표시한다.
- `payoff_punch`는 앞선 결론을 반복하지 않고 남은 핵심 답, 시민 영향, 검증된 모순 또는 정확한 다음 사건을 추가해야 한다.
- 결론 카드의 마지막 구역은 `payoff_punch`를 큰 노란 글씨로 표시한다. 이 값이 있으면 `discussion_prompt`는 결론 카드와 경쟁하지 않고 댓글 CTA 선택에만 유지된다.
- 장면별 `voice_delivery`를 추가했다.
  - `auto`: 기존 Typecast Smart Emotion 문맥 유지
  - `contrast`: 공식 `toneup` 프리셋과 제한된 피치·속도 조절
  - `verdict`: 공식 `tonedown` 프리셋과 낮은 피치·느린 속도 조절
- 새 결론은 `contrast` 또는 `verdict`를 사용하고, 화면 마지막 문구의 핵심 표현을 두 박자 이상의 내레이션에서도 말해야 한다.
- 민감 뉴스는 낮고 단호한 `verdict`를 우선하며 angry 프리셋, 고함, 피해를 소비하는 반문을 금지한다.
- 기존 project version 10·storyboard version 5 이하는 렌더 호환을 유지한다.

## 기준 사례 재생성

- 월미도 디스코팡팡 사고 프로젝트를 새 계약으로 올렸다.
- 결론 마지막 문구: `왜 밖으로? · 답은 아직`
- 결론 내레이션: `사고는 이미 났습니다. 그런데 왜 밖으로 떨어졌는지, 답은 아직 없습니다.`
- 민감 뉴스 자동 보이스 `Seohyeon`을 유지하고 결론에 `voice_delivery: "verdict"`를 적용했다.
- 실제 Typecast 렌더에서 결론 장면은 5.517초, 전체 미리보기는 27.206초였다.
- 추출 프레임에서 720x1280 결론 카드의 세 구역, 글자 크기, 안전 여백과 겹침 없음 상태를 확인했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 결론 마지막 구역, 장면별 Typecast 프리셋 요청, 새 검수와 렌더 보고서 필드.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 주제 공통 마지막 붙잡기·음성 전달 제작 규칙.
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`: 요약 반복 금지와 민감도별 결론 리듬.
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: project 11, storyboard 6 계약.
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`: 새 project version.
- `plugins/news2shorts/skills/news2shorts/templates/storyboard.template.json`: `payoff_punch`, `voice_delivery` 기본 필드.
- `plugins/news2shorts/.codex-plugin/plugin.json`: `0.31.0+codex.20260825000009` 버전.
- `plugins/news2shorts/README.md`, `README.md`: 사용자 동작 설명.
- `projects/2026-08-24-wolmido-disco-pangpang-accident-review/project.json`: version 11 기준 사례.
- `projects/2026-08-24-wolmido-disco-pangpang-accident-review/storyboard.json`: 새 결론 문구·대사·전달.
- `projects/2026-08-24-wolmido-disco-pangpang-accident-review/script.md`: 마지막 붙잡기와 Typecast 전달 설계 기록.
- `projects/2026-08-24-wolmido-disco-pangpang-accident-review/preview.mp4` 및 렌더 산출물: 개선본 미리보기.

## 검증 결과

- Python AST와 JSON 파싱 통과.
- Skill Creator 빠른 구조 검사에서 소스·설치본 모두 통과.
- 소스와 설치본 검증에서 현재 월미도 프로젝트 오류·경고 없음.
- Typecast API 실제 렌더 성공; `render-report.json`에 `payoff_punch`, `voice_delivery: "verdict"`, Seohyeon 보이스와 측정 길이 기록.
- 설치본 `doctor --json`의 로컬 렌더 요구사항 `ok: true` 확인. 샌드박스 키체인 조회는 제한 상태지만 승인된 실제 렌더에서는 기존 키체인 자격으로 Typecast 호출 성공.
- 소스·설치 캐시의 렌더러와 Skill SHA-256 일치.
- `news2shorts@news2shorts-local` `0.31.0+codex.20260825000009` installed·enabled 확인.
- `git diff --check` 통과.
- 프론트엔드 빌드, DB 작업, YouTube 업로드는 수행하지 않았다.

## 근거 경계

- Typecast 공식 TTS API와 모델 문서가 preset emotion, intensity, pitch, tempo 및 `toneup`·`tonedown`을 지원한다. 단어 단위 SSML 악센트는 확인되지 않아 제공한다고 주장하지 않는다.
- 이 편집 규칙은 마지막 이탈을 줄이기 위한 제작 가설이며 조회수나 바이럴 성과를 보장하지 않는다.
