# 2026-08-20 K-Export Shorts 재미 편집 게이트

## 완료 내용

- 영어권 K-pop 유머 Shorts 2개와 일본어권 K-pop Shorts 2개를 Codex Browser Use로 직접 확인했다.
- YouTube 공식 Shorts 분석 문서에서 `viewed versus swiped away`, 시청 시간, 유지율을 확인했다.
- TikTok 공식 Creative Codes에서 hook-body-close, 동적 편집, 움직임, 텍스트, 효과음 원칙을 확인했다.
- 기존 `viral-shorts` 식별자와 소스·장면·콘셉 선택 흐름을 유지하면서, 콘셉 선택 뒤 `fun-edit` 단계를 추가했다.
- 반응 선공개, setup-turn-payoff, 중간 재후킹, 짧은 평균 컷, 주인공 포커스, 정지·리플레이·급확대, 실제 합성 효과음을 Fun Score로 검증한다.
- 실제 프레임 검토 여부와 메모, 반응 강도, 결말 명확도를 필수 입력으로 만들었다. 각 값이 0.65 미만이면 다른 장면을 선택하도록 실패 처리한다.
- `focus_x`로 가로 주인공 위치를 렌더에 반영한다.
- `impact`, `record-stop`, `pop`, `whoosh` 효과음을 Python 표준 라이브러리로 로컬 합성해 원본 한국어 오디오에 섞는다. 외부 효과음이나 음악은 다운로드하지 않는다.
- 정지 화면의 오디오 길이도 함께 보정하고, 현재 `fun-edit.json`의 SHA-256과 렌더 보고서를 연결해 오래된 부분 렌더를 검출한다.
- 플러그인 기본 버전을 `0.5.0`으로 올리고 `0.5.0+codex.20260820105749`로 설치했다.

## 리서치 근거

- 영어권 짧은 행동·반응 루프: `https://www.youtube.com/shorts/IFG8o1zQqQc`
- 영어권 한 줄 밈 전제와 빠른 반응 연결: `https://www.youtube.com/shorts/xLwCCv_HGjg`
- 일본어권 지속 질문 헤더와 짧은 진행 자막: `https://www.youtube.com/shorts/3iUfVKoySCk`
- 일본어권 미세 반응 라벨과 별도 결말 문구: `https://www.youtube.com/shorts/6CTIPwkFfGg`
- YouTube Shorts 분석 지표: `https://support.google.com/youtube/answer/12942217?hl=en-GB&co=YOUTUBE._YTVideoType%3Dshorts`
- TikTok Creative Codes: `https://ads.tiktok.com/business/en/creative-codes`

참고 영상의 미디어, 브랜딩, 음원, 정확한 편집 순서는 복제하지 않고 구조만 정규화했다.

## 변경 파일

- `plugins/viral-shorts/scripts/viral_shorts.py`
  - `fun-edit` 명령, Fun Score, 시각 검토 게이트, 가로 포커스, 정지 프레임, 로컬 효과음 합성·믹싱, stale render 검증을 추가했다.
- `plugins/viral-shorts/.codex-plugin/plugin.json`
  - 0.5.0 버전과 재미 편집 기능 설명·호출 예시를 반영했다.
- `plugins/viral-shorts/README.md`
  - 새 제작 흐름과 명령, 제한을 설명했다.
- `plugins/viral-shorts/skills/viral-shorts/SKILL.md`
  - 콘셉 선택 뒤 Fun Edit를 필수 단계로 지정했다.
- `plugins/viral-shorts/skills/viral-shorts/agents/openai.yaml`
  - 기본 호출 문구에 재미 편집 게이트를 반영했다.
- `plugins/viral-shorts/skills/viral-shorts/references/fun-edit.md`
  - 리서치 근거, 입력 계약, 하드 게이트, 점수표를 추가했다.
- `plugins/viral-shorts/skills/viral-shorts/references/export-schema.md`
  - 콘셉 편집안과 최종 Fun Edit 계약을 분리했다.
- `plugins/viral-shorts/skills/viral-shorts/references/workflow.md`
  - Fun Edit 검토·렌더·검증 단계를 추가했다.
- `plugins/viral-shorts/skills/viral-shorts/references/output-contract.md`
  - `fun-edit.json`, `fun-edit.md`, 렌더 효과·점수·해시 계약을 추가했다.
- `plugins/viral-shorts/skills/viral-shorts/references/rights-policy.md`
  - 외부 음원·효과음 복제 금지와 로컬 합성 경계를 추가했다.
- `README.md`
  - 저장소 플러그인 설명 한 줄을 갱신했다.
- `docs/complete/2026-08-20-viral-shorts-fun-edit-gate.md`
  - 당일 완료 내용을 기록했다.

## 검증

- `python3 -B .../viral_shorts.py --help` 성공, `fun-edit` 명령 노출 확인.
- Skill quick validation 성공.
- Plugin validation 성공.
- 실제 아이브 프로젝트의 임시 복제본에서 양 시장 Fun Score 91.6/100을 생성했다.
- 임시 복제본으로 영어판·일본어판을 각각 13.27초, 720x1280, H.264/AAC, 30fps로 렌더했다.
- 각 결과에 `record-stop`, `impact`, `whoosh` 합성 효과음 기록과 `fun-edit.json` SHA-256 연결을 확인했다.
- `validate-export` 성공: Fun Edit, 양언어 메타데이터, MP4 SHA-256, 권리 경계 모두 통과했다.
- `viral-shorts@news2shorts-local`이 `0.5.0+codex.20260820105749`로 installed, enabled 상태임을 확인했다.
- 설치 캐시의 핵심 스크립트와 Skill SHA-256이 작업본과 일치한다.
- 프론트엔드와 DB 변경은 없으며 프론트 빌드는 수행하지 않았다.

## 제한

- Fun Score는 편집 적합성 게이트이지 조회수 예측이 아니다.
- 시각 검토값은 실제 프레임을 본 편집자가 정직하게 기록해야 한다. 약한 원본 반응은 효과음·자막만으로 보완하지 않는다.
- 기존 아이브 선택 장면은 반응이 비교적 약해 개선 렌더도 원본 한계를 가진다. 실제 재제작 시 더 강한 표정 반응이 있는 순간을 다시 고르는 편이 낫다.
- 원본 권리가 `unknown`이면 결과는 화면 배지 없이도 로컬 검토용이며 게시·수익화 승인이 아니다.
