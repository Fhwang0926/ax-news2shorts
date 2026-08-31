# Discovery contract

YouTube Data API는 공개 영상의 제목, 채널, 게시 시각, 길이, 조회수, 좋아요, 댓글 수를 소재 수요 신호로 확인하는 데만 사용합니다.

## 자격 증명

- 환경변수 `YOUTUBE_API_KEY`를 먼저 사용하고 macOS에서는 `senior-shorts.youtube-data-api-key` 키체인 항목을 두 번째로 사용합니다.
- 키를 명령 인자, URL 쿼리, 저장소, 프로젝트 JSON, 로그에 기록하지 않습니다.
- `configure-youtube`는 macOS 키체인의 숨김 입력을 사용합니다.
- Python 기본 CA 경로가 없으면 `/etc/ssl/cert.pem`, `/opt/homebrew/etc/openssl@3/cert.pem` 순서로 시스템 인증서 묶음을 선택하며 TLS 인증서 검증을 끄지 않습니다.
- 공개 메타데이터 조회에는 API 키를 사용합니다. 비공개 채널 데이터, 업로드, 수정, 삭제에는 OAuth 2.0이 별도로 필요하며 이 플러그인 범위가 아닙니다.

## 신호 수집

`discover`는 기본 90일 동안 세 개의 한국어 검색어를 각각 한 페이지씩 조회하고, 180초 이하 공개 영상을 중복 제거합니다. 결과의 `score`는 다음 합계입니다.

- 조회 속도 40점
- 댓글 참여율 20점
- 최신성 20점
- 시니어 관련 제목 표현 20점

점수는 검색 후보를 정렬하는 내부 휴리스틱이며 바이럴 성과를 보장하지 않습니다.

## 창작 후보

YouTube 영상 하나를 사연 하나로 변환하지 않습니다. 서로 다른 신호에서 반복되는 시청자 관심과 갈등 유형만 추출한 뒤 `story-candidates.template.json` 형식으로 정확히 3개 창작 후보를 작성합니다.

각 후보에는 다음이 필요합니다.

- 고유 `id`
- 제목과 한 줄 `logline`
- 시니어 시청자의 고민 `audience_pain`
- 인물 사이의 `conflict`
- 원본 결말을 복제하지 않은 `twist_direction`
- 8장면으로 시각화 가능한 이유 `eight_scene_fit`
- 기존 영상과 달라지는 점 `originality_note`
- 근거가 된 `source_signal_ids`
- `rights_mode: original_fiction`
- 민감도와 0~100점 적합도

후보는 자동 선택하지 않습니다. 사용자에게 세 후보를 모두 보여주고 선택된 ID만 `select`로 기록합니다.

## 금지 사항

- 영상·썸네일·음성·자막·댓글 자동 다운로드
- 제목이나 설명을 대사로 복사
- 원본 인물, 사건 순서, 반전, 결말 재사용
- 공개 메타데이터를 사용 허가로 해석
- 사용자 선택 전 대본, 이미지, 음성, 렌더 생성
