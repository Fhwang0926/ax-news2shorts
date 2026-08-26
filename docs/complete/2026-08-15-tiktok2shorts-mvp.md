# 2026-08-15 tiktok2shorts MVP 작업 완료

## 작업 범위

- `news2shorts`와 같은 저장소 로컬 플러그인 구조로 `tiktok2shorts`를 추가했다.
- 공개 리서치 또는 허용된 TikTok 후보 수집 결과를 입력받아 확인된 절대 조회수·공유·상호작용·참여율과 출처 품질을 비교하는 CLI를 구현했다.
- 후보 리서치, 원본 다운로드, 분석, 편집 지시서, 로컬 MP4 렌더를 `local_only` 단일 흐름으로 통합했다.
- 권리 상태가 `unknown` 또는 `review_required`인 공개 후보도 로컬 프로젝트에서 계속 분석·다운로드·렌더할 수 있게 했다. 권리 상태를 임의로 승인 상태로 바꾸지는 않는다.
- 별도 `private_review` 모드, `--private-review` 옵션, `outputs/private-review.mp4`, 게시 금지 워터마크를 제거했다.
- `publish.json`의 `upload_status`와 렌더 보고서의 업로드 상태를 제거하고, 업로드 명령이나 외부 업로드 연동을 추가하지 않았다.
- 명시적으로 `not_permitted`인 원본과 보조 자산은 다운로드·렌더 단계에서 계속 차단한다.
- 원본 영상 전체 재업로드와 단순 번역 자막 덮어쓰기를 프로젝트 정책과 정적 검사에서 차단했다.
- 다운로드한 원본의 시간별 프레임과 `preview.json`, 장면별 구간·해설·자막·화면 수정 방식이 담긴 `edit-plan.md`를 생성한다.
- 짧은 원본 구간, 보조 이미지·영상, 기본 해설 카드를 조합해 720x1280 H.264/AAC `outputs/short.mp4`를 생성한다.
- 장면별 `narration_audio`를 우선 사용하고, 없으면 macOS 로컬 TTS로 한국어 내레이션을 생성한다.
- 세로 크롭, 중앙 리프레임, 완만한 확대, 정지 화면, 지정 좌표 화살표, 한국어 안전 영역 자막, 출처 표기, 원본 오디오 낮춤, AI 재현 표기를 지원한다.
- 바이럴 가능성 예측형 선정을 제거하고, 최소 100만 조회와 보조 도달·참여 신호가 이미 확인된 후보만 `ranked_candidates`에 남긴다.
- 300만 조회, 1만 공유, 10만 상호작용, 8% 참여율 중 하나 이상을 보조 신호로 요구하며 성장 속도와 가속도는 참고값으로만 기록한다.
- TikTok 원본 URL, 제작자, 게시 시각, 수집 경로, 지표 근거 URL, 20자 이상의 실제 장면 요약이 불완전한 후보는 `rejected_candidates`로 분리한다.

## 의도적으로 제외한 범위

- TikTok 직접 크롤링, 로그인·CAPTCHA·DRM 우회
- 원본 워터마크 제거와 원본 전체 재업로드
- DB, 정기 수집기, 외부 수집 API 연결
- 자동 ASR·VLM, 외부 TTS 서비스 연결
- TikTok, YouTube 또는 다른 서비스로의 업로드 기능

## 검증 경계

- Python 구문 검사와 플러그인·스킬·JSON 형식 검사를 수행했다.
- 실제 TikTok 원본 대신 권리 문제가 없는 합성 테스트 프로젝트로 `score`, `init`, `edit-plan`, `validate --final`, `render --no-tts`를 실행했다.
- 권리 상태가 `unknown`인 프로젝트가 `local_only`로 생성되고 로컬 다운로드 게이트에서 `local_personal_use`로 허용되는 것을 확인했다.
- 같은 게이트에서 `not_permitted`가 차단되는 회귀 검사를 수행했다.
- 생성된 17.488초 MP4가 H.264, AAC, 720x1280, 영상·오디오 스트림 포함 조건을 만족하는지 결과 보고서와 추출 프레임으로 확인했다.
- 추출 프레임에 `개인 검토용 · 게시 금지` 워터마크가 없고, 프로젝트·메타데이터·렌더 보고서에 개인 검토 또는 업로드 상태 필드가 없는 것을 확인했다.
- 이미 바이럴된 후보 회귀 테스트에서 단일 관측 520만 조회 후보는 `major_viral`로 통과했고, 한 시간에 89만 조회가 늘었어도 최신 조회수가 90만인 후보는 탈락했다.
- 1,200만 조회여도 제작자와 지표 근거 URL이 없는 후보는 추천 목록이 아닌 `rejected_candidates`로 분리되는 것을 확인했다.
- 외부 TikTok 수집, 실제 타인 영상 다운로드·처리, 원본 이용 허가의 법적 유효성, 플랫폼 업로드, 수익화 판정은 수행하지 않았다.
- AGENTS.md 지침에 따라 프론트엔드 빌드나 테스트는 수행하지 않았다.

## 변경 파일

- `.agents/plugins/marketplace.json`
- `plugins/tiktok2shorts/.codex-plugin/plugin.json`
- `plugins/tiktok2shorts/scripts/tiktok2shorts.py`
- `plugins/tiktok2shorts/skills/tiktok2shorts/SKILL.md`
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/candidate-schema.md`
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/output-contract.md`
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/editorial-and-rights.md`
- `plugins/tiktok2shorts/examples/candidates.sample.json`
- `plugins/tiktok2shorts/README.md`
