# Candidate contract

후보는 조사 결과를 기록하는 입력일 뿐이며 사용자 선택이나 권리 허가를 뜻하지 않습니다.

## Story candidates v3

신규 후보의 최상위 `version`은 `3`입니다. 최상위 객체는 `generated_at`, `selection_required`, `best_candidate_id`, `best_candidate_reason`, `candidates`를 함께 가지며 후보는 최대 3개입니다. v3는 대화형 힐링 썰 전용이며 `mode`는 `anecdote`입니다.

각 후보 필드:

- `id`, `contract_version: 3`, `mode: anecdote`, `title`, `selection_reason`, `emotional_arc`
- `story_engine`: `missing_routine`, `object_mystery`, `misunderstanding_reveal`, `quiet_sacrifice`, `returned_promise` 중 하나
- `anchor_event`, `protagonist`, `central_question`, `obstacle`, `reveal`, `payoff_object`
- `story_score`: `total`, 아래 여섯 점수 항목, `reason`
- `sensitive_topics`: 확인된 민감 주제 문자열 배열
- `sources`, `claims`: v3 사연에서는 빈 배열. 기존 v2 기사형 호환 입력에서만 출처와 claim/source ID 연결에 사용
- `anecdote`: 사연형 기원, 동의, 비식별화, 재구성 표시
- `dialogue_turns`: `id`, `speaker`, `text`를 가진 10~14개 발화. 기본 화자는 `내레이터`와 1~2명의 인물이며 연속 발화 사이 화자 교대가 7회 이상이어야 함. 내레이터의 질문·연결 뒤에는 인물의 직접 인용이 별도 turn으로 이어져야 함
- `beats`: `cold_open`, `setup`, `problem`, `clue`, `escalation`, `reveal`, `afterglow` 순서의 정확히 7개 비트

각 비트에는 짧은 `caption`, 구어체 `narration`, 1개 이상의 `dialogue_turn_ids`가 필요합니다. 모든 발화는 전체 순서대로 정확히 한 번 사용하며 해당 원문이 연결된 비트의 `narration`에 포함되어야 합니다. 발화 글자 수는 전체 내레이션 글자의 60% 이상이어야 합니다. 첫 장면은 설명형 질문 대신 인물의 대사로 시작합니다. `caption`에는 `할머니:`, `나:` 같은 화자 라벨을 넣지 않고 실제 화면 문구만 기록합니다.

재미 점수의 상한과 합계는 다음과 같습니다.

- `hook_and_open_loop`: 20
- `character_and_event`: 15
- `tension_and_progression`: 20
- `reveal_and_payoff`: 25
- `spoken_naturalness`: 10
- `food_action_sync`: 10

`total`은 여섯 항목의 합과 일치해야 합니다. 출처 확인과 민감도는 점수에 섞지 않고 프로젝트 검증의 별도 통과 조건으로 둡니다. `best_candidate_id`는 70점 이상인 최고점 후보를 가리켜야 합니다. 동점이면 `hook_and_open_loop`, `reveal_and_payoff`, `tension_and_progression` 순으로 비교합니다. 70점 이상 후보가 하나도 없으면 후보를 다시 조사합니다. `BEST`는 추천 표시일 뿐 자동 선택이 아니며 사용자 선택을 기다립니다.

기존 기사형 `version: 2`와 `version: 1` 후보는 이미 만든 프로젝트를 다시 열기 위한 호환 입력으로 계속 허용합니다. 새 힐링 후보 생성에는 사용하지 않습니다.

사연형 `origin_kind`는 `submitted`, `public_post`, `fictionalized` 중 하나입니다. `disclosure`와 `identity_fields_removed`가 필요합니다. 공개 게시물의 표현을 복사하지 않고 독립된 문장과 구성으로 재작성합니다.

## Video candidates

최상위 구조는 Story candidates와 같고 후보는 최대 3개입니다. 후보 필드:

- `id`, `platform`, `source_url`, `creator`, `scene_summary`
- `selection_reason`, `collected_at`, `watermark_present`
- `visual_text_status`: `none`, `non_chinese_only`, `chinese_present`, `unknown`
- `rights_status`: `owned`, `licensed`, `permission_confirmed`, `negotiation_pending`, `not_permitted`
- 선택적으로 `permission`, `recommended_segments`, `text_free_segments`, `visual_text_review_note`

`platform=douyin`은 발견 경로를 뜻할 뿐 다운로드나 사용 허가가 아닙니다. `not_permitted` 후보는 프로젝트에 연결하지 않습니다.

화면 중국어가 없는 후보를 먼저 보여줍니다. `chinese_present` 후보는 `start_seconds`, `duration_seconds`를 가진 서로 다른 `text_free_segments`가 신규 v3와 v2에서는 7개, 기존 v1에서는 6개 이상 확인된 경우에만 프로젝트에 연결할 수 있습니다. 원본 문자 삭제·블러·가림은 후보 적합성으로 인정하지 않습니다. `unknown`은 검토본에서 경고하고 게시 준비 단계에서 차단합니다.

자동 원본 가져오기는 후보의 공개 `source_url`이 아니라 제작자·라이선스 제공처가 별도로 준 HTTPS 직접 영상 URL을 CLI에 입력합니다. URL은 후보 JSON에 저장하지 않으며, 권리 상태가 `owned`, `licensed`, `permission_confirmed`이고 사용자가 다운로드·편집 권리를 확인해야 합니다.
