# Animal Viral Shorts 후보 내용 설명 개선 및 재조사

## 완료 일자

- 2026-08-25

## 반영 범위

- 후보 목록이 조회수와 한 줄 요약만 보여주지 않고, 시작부터 결말까지의 내용 흐름·흥미 포인트·활용 방향·현실적 한계를 함께 설명하도록 개선했다.
- 새 후보 입력에 `content_explanation.story_flow`, `appeal`, `adaptation_note`, `limitations`를 추가했다.
- 이전 버전 후보 파일은 계속 읽을 수 있도록 장면 변화에서 내용 흐름을 보완하는 하위 호환 처리를 유지했다.
- 플러그인 버전을 `0.4.3+codex.20260825`로 올리고 Codex 설치본을 갱신했다.
- 이전에 제시한 후보와 겹치지 않도록 TikTok과 YouTube Shorts 원본 계정에서 새 후보를 조사했다.

## 변경 파일

- `plugins/animal-viral-shorts/scripts/animal_viral_shorts.py`: 후보 설명 필드 정규화와 상세 Markdown 출력, 버전 갱신.
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/SKILL.md`: 새 후보의 상세 내용 설명과 사용자 선택 전 정지 규칙 강화.
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/references/candidate-schema.md`: `content_explanation` 계약과 하위 호환 규칙 추가.
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/references/workflow.md`: 후보 입력 필드 추가.
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/agents/openai.yaml`: 사용자 기본 안내에 상세 설명 요구 반영.
- `plugins/animal-viral-shorts/.codex-plugin/plugin.json`: 버전과 사용자 설명 갱신.
- `plugins/animal-viral-shorts/README.md`: 후보 설명 원칙 추가.
- `projects/2026-08-25-animal-viral-candidates-v2/`: 새 후보 원본 입력과 점수화된 JSON·Markdown 결과.

## 새 후보 조사 결과

- TikTok `@brodiethatdood`: 경기장 전광판 댄스 대결과 우승 결과가 완결된 후보.
- TikTok `@wally.meets.world`: 할머니 방문 뒤 작은 소 인형 묶음을 가져오는 선물 공개형 후보.
- YouTube Shorts `@imbluethesiberian`: 두 허스키에게 같은 지시를 주고 반응 차이를 반복 비교하는 후보.
- 세 후보 모두 공개 원본 계정과 공개 지표는 확인했지만 재사용·상업 이용 허가는 확인하지 못해 권리 상태를 `unknown`으로 유지했다.
- Brodie의 다른 여행 준비 영상은 조회수에 비해 참여가 낮고 `#IAMSPartner` 유료 제휴 표시가 있어 이번 후보에서 제외했다.

## 검증 결과

- 소스와 설치 캐시의 스킬 구조 검사를 통과했다.
- 소스와 설치 캐시의 `doctor --json`에서 메타데이터·프리뷰·렌더 준비 상태를 확인했다.
- `animal-viral-shorts@news2shorts-local` `0.4.3+codex.20260825` 설치·활성화를 확인했다.
- 소스와 설치 캐시의 핵심 스크립트·스킬 SHA-256이 각각 일치했다.
- 새 후보 3개가 모두 자격 조건을 통과했고, 자동 선택 없이 `selection_required: true`, `auto_selected: false`로 생성됐다.
- 후보 입력 JSON 형식과 상세 후보 Markdown 출력을 확인했다.
- 프론트엔드 빌드, DB 작업, 원본 다운로드, 영상 렌더, 외부 게시·업로드는 수행하지 않았다.

## 제한

- TikTok 프로필의 조회수·좋아요 표시는 공개 화면에서 반올림된 값이다.
- 편집 적합성 점수는 조회수·매출 예측이 아니며, 공개 영상 존재는 재사용 허가를 뜻하지 않는다.
- 실제 구매 연결은 판매 상품을 직접 확보해 크기·내구성·구성·정산 링크를 확인한 별도 촬영과 함께 검증해야 한다.
