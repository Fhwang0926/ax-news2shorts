# Shorts Studio

승인된 로컬 입력을 한국어 9:16 쇼츠로 제작하는 플러그인입니다. `story`, `romance`, `price` 세 모드가 하나의 CLI와 승인·권리·출력 계약을 사용합니다.

후보 조사, 공개 URL 다운로드, 기존 `story2short`·`romance-drama-shorts`·`price-breakdown-shorts` 프로젝트 가져오기, YouTube 직접 업로드는 지원하지 않습니다.

## 공통 흐름

```bash
python3 scripts/shorts_studio.py doctor --json
python3 scripts/shorts_studio.py <mode> init --input ./input.json --project-dir ./projects/shorts-studio/YYYY-MM-DD/<slug>
python3 scripts/shorts_studio.py <mode> approve --project-dir <project> --stage assets --confirm-assets
python3 scripts/shorts_studio.py <mode> approve --project-dir <project> --stage content --confirm-content
python3 scripts/shorts_studio.py <mode> render --project-dir <project> --draft --no-tts
python3 scripts/shorts_studio.py <mode> approve --project-dir <project> --stage publish --confirm-publish
python3 scripts/shorts_studio.py <mode> validate --project-dir <project> --publish-ready
python3 scripts/shorts_studio.py <mode> render --project-dir <project> --final
python3 scripts/shorts_studio.py <mode> upload-package --project-dir <project>
```

승인 순서는 `assets → content → publish`입니다. `unknown`과 `review_required`는 검토본까지만 허용하고 `not_permitted`는 초기화부터 차단합니다. 최종본은 프로젝트와 모든 사용 자산이 `owned`, `licensed`, `permission_confirmed` 중 하나여야 합니다.

## 입력 계약

공통 필드는 `slug`, `title`, `rights`, `audio`, `scenes`입니다. 모든 경로는 입력 JSON 파일 기준 상대경로 또는 절대경로입니다.

- `story`: `source_video`와 장면별 `source_start`, `source_end`, `observed_action`, `caption`, `narration`이 필요합니다.
- `romance`: 장면별 `visual`, `speaker`, `dialogue`, `caption`, `narration`이 필요합니다. 합성 자산이 있으면 content 승인 때 `--confirm-synthetic-disclosure`를 함께 전달합니다.
- `price`: `menu_price`, `components`, `evidence`가 필요합니다. 회원가·쿠폰·첫 구매·적립금 할인은 계산에서 거부하고 피할 수 없는 배송비만 합산합니다.

최종 음성은 `audio.provider: typecast`만 허용합니다. 승인된 로컬 Typecast WAV가 없으면 publish 승인 시 `news2shorts.typecast.api-key` 키체인 항목 또는 `TYPECAST_API_KEY`로 한 번의 연속 음성을 생성합니다. 검토본만 `--no-tts`를 허용하며 로컬 TTS 자동 대체는 없습니다.

## 출력

- `outputs/review.mp4`: 540×960 검토본
- `outputs/short.mp4`: 720×1280 최종본
- `thumbnail.jpg`, `captions.srt`, `render-report.json`, `rights-manifest.json`
- `edit-package/`: 장면 클립, 자막, 음성, 타임라인
- `youtube-upload.json`, `youtube-upload.md`: 복사용 업로드 정보

실제 게시, 수익화 가능성, 출처 권리와 플랫폼 승인은 렌더 성공만으로 증명되지 않습니다.
