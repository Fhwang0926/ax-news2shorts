# 힐링쇼츠

내레이터의 짧은 연결 뒤에 인물의 직접 인용이 이어지는 익명·재구성 힐링 썰을 음식 조리 영상 위에 Typecast 음성과 큰 자막으로 전달하는 로컬 Codex 플러그인입니다.

## 포함 기능

- 직접 입력한 익명 사연, 공개 사연 탐색, 사용자가 재구성에 동의한 기사 소재의 세 가지 시작 흐름
- 내레이터와 1~2명의 인물, 10~14개 발화, 화자 교대 7회 이상, 대화 비중 60% 이상을 통과한 후보만 비교하는 대화형 힐링 썰 게이트
- 스토리 후보 최대 3개를 사건·대화·반전 중심 100점 기준으로 비교해 70점 이상 BEST 하나를 표시하고, 사용자 선택 후 음식 영상 후보 최대 3개를 제시하는 승인 게이트
- 기사 사실·출처와 익명 사연의 비식별화·재구성 표시를 분리한 기록
- 로컬 음식 영상 해시, 제작자, 원본 URL, 워터마크 존재 여부와 권리 협의 상태 기록
- 중국어 없는 음식 영상 우선 추천과 장면별 원본 문자 상태 검증
- 제작자·라이선스 제공처가 준 권리 확인 HTTPS 직접 원본의 제한적 자동 가져오기
- 첫 대사 콜드 오픈, 중간 재후킹, 반전, 따뜻한 회수와 마지막 구독·좋아요 CTA의 40~45초 7개 비트
- v3 상단 불투명 주제 여백, 결말을 숨긴 호기심 문구, 화자 라벨·배경 상자 없는 중앙 문구
- 내레이터→인물 직접 인용을 구분하는 화자별 Typecast 음성 연결
- Typecast 발화 길이와 맞춰 교체되는 2줄 이내 큰 자막, 영상 전체에 끊김 없이 이어지는 자체 생성 잔잔한 단조 BGM WAV
- 540x960 검토본, 720x1280 최종본, CapCut/Vrew용 720x1280 편집 패키지
- 검토용 렌더와 게시 준비 상태를 분리하는 권리·민감 주제 검증

DB, MCP, 웹 UI, 실제 업로드, 도우인 페이지·CDN 자동 다운로드, 로그인·보호 우회, 원본 문자·워터마크 제거는 포함하지 않습니다.

## 빠른 시작

```bash
python3 scripts/healing2shorts.py doctor

python3 scripts/healing2shorts.py init \
  --story-candidates ./story-candidates.json \
  --story-id story-01 \
  --video-candidates ./video-candidates.json \
  --video-id video-01 \
  --source-video ./food-video.mp4

# 제작자·라이선스 제공처가 준 HTTPS 직접 원본 URL을 사용할 때
python3 scripts/healing2shorts.py init \
  --story-candidates ./story-candidates.json \
  --story-id story-01 \
  --video-candidates ./video-candidates.json \
  --video-id video-01 \
  --authorized-source-url 'https://licensed.example/video.mp4' \
  --confirm-download-rights

python3 scripts/healing2shorts.py preview --project-dir <project-dir>
python3 scripts/healing2shorts.py validate --project-dir <project-dir>
python3 scripts/healing2shorts.py render --project-dir <project-dir> --draft --no-tts
python3 scripts/healing2shorts.py upload-package --project-dir <project-dir>
```

`--no-tts`는 무음 기술 검토용입니다. 기본 렌더는 기존 `news2shorts.typecast.api-key` 키체인 항목 또는 `TYPECAST_API_KEY` 환경변수의 Typecast 설정을 사용하며 임의의 로컬 TTS로 대체하지 않습니다.

권리가 `negotiation_pending`이면 추가 검토 워터마크가 없는 `outputs/review.mp4`와 편집 패키지를 만들 수 있지만 `publish_blocked` 상태를 유지합니다. 최종 렌더는 `owned`, `licensed`, `permission_confirmed` 영상과 필요한 검토 승인이 모두 있어야 합니다.

자동 원본 가져오기는 `owned`, `licensed`, `permission_confirmed` 후보에만 허용됩니다. 공개 도우인 URL은 출처 기록용이며 다운로드 입력으로 사용할 수 없습니다. 중국어가 보이는 장면은 문자를 지우지 않고 타임라인에서 제외하며, 확인되지 않은 장면은 게시 준비 검증을 통과하지 못합니다.
