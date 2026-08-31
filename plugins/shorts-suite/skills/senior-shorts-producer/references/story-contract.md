# Story contract

`story.json`은 모든 후속 단계가 공유하는 원본입니다.

## 최상위 필드

- `title`: 짧은 한국어 제목
- `hook`: 선택된 훅의 본문과 동일한 문장
- `selected_hook_id`: `hooks[].id` 중 최고점 항목
- `target_age`: 기본 `55-75`
- `target_duration`: 45~60초
- `fictionalization`: 항상 `fictionalized`
- `characters`: 1명 이상의 캐릭터 정의
- `hooks`: 정확히 5개
- `scenes`: 정확히 8개

## 훅 점수

각 훅은 다음 5개 항목을 0~20점으로 평가하고 `total`에 합계를 기록합니다.

- `curiosity`: 답을 확인하고 싶은가
- `emotion`: 감정적 이해관계가 즉시 보이는가
- `conflict`: 인물 사이의 갈등이 구체적인가
- `clarity`: 한 번에 이해되는가
- `spoiler_control`: 결말을 숨기면서 과장하지 않는가

## 장면 순서

1. `hook`: 0~4초, 가장 강한 갈등 또는 의문
2. `character_intro`: 인물과 평범한 상황
3. `incident`: 사건 시작
4. `conflict`: 첫 갈등
5. `escalation`: 갈등 심화
6. `pre_reveal`: 반전 직전의 새로운 단서
7. `reveal`: 앞 장면에서 준비한 반전
8. `afterglow`: 결말과 여운

각 장면에는 `scene`, `role`, `narration`, `subtitle`, `highlight`, `characters`, `visual_prompt`, `emotion`, `motion`, `video_mode`, `duration`이 필요합니다.

## 창작·안전 규칙

- 실명, 실제 주소, 특정 회사나 기관을 창작 사연의 사실처럼 넣지 않습니다.
- 범죄, 사망, 자해, 의료 피해, 미성년자 학대처럼 민감한 소재는 자동 진행하지 않습니다.
- 재산, 상속, 연금, 세금, 건강 조언을 설명하는 정보형 문장으로 확장하지 않습니다.
- 영상 설명에는 `AI로 제작한 창작 사연입니다.`와 동등한 고지를 포함합니다.
