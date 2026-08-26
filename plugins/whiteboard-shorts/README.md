# Whiteboard Shorts

TikTok2Shorts에서 선택·다운로드·검토한 원본을 가져와, 확인된 9:16 장면 이미지를 의미 순서대로 그리는 로컬 화이트보드 애니메이션 Codex 플러그인입니다.

## 범위

- TikTok 원본 URL·제작자·권리·해시·장면 근거를 보존한 프로젝트 가져오기
- 바이럴 점수와 화이트보드 적합도, 실제 프레임 검토, 장면 다양성 사전 검사
- TikTok 장면의 한국어 narration을 SRT로 변환하고 독립 프로젝트 생성
- 로컬 SRT 입력 호환
- 픽셀 좌표 기반 `annotation.json` 검증
- 영역 확인 이미지와 `540x960` 검토용 영상
- `1080x1920`, 30 FPS H.264 장면 렌더, 장면별 펀치 줌과 병합
- 훅→재훅→반전으로 이어지는 36자 이내 쇼츠형 장면 자막
- 실제 짧은 영상 사용 근거, 공식 다운로드, 라이선스와 해시가 확인된 무보컬 음원
- 전체 병합본 결말 뒤 1.8초 무음 `구독 · 좋아요` CTA 샷
- 제목·설명·태그·썸네일·고정 댓글·설정이 담긴 YouTube 업로드 준비 패키지
- SRT·장면 이미지 권리 상태와 사용자 승인 기록

TikTok 후보 조사와 공개 영상 취득은 `tiktok2shorts`가 담당합니다. 이 플러그인은 검토된 프로젝트만 가져오며 장면 근거가 있는 5단계 한국어 반전 자막, 검증된 라이선스 음원 또는 직접 생성한 안전 음원, 필요한 장면 줌을 로컬 초안에 적용합니다. TikTok·스트리밍 음원 복사, 상용 차트곡 직접 삽입, ASR, TTS, 보컬, 실제 YouTube 업로드는 포함하지 않습니다. 상용 플랫폼 음원은 업로드 후 YouTube Shorts 공식 음악 선택기에서 추가해야 합니다.

## 시작

```bash
python3 scripts/whiteboard_shorts.py doctor
python3 scripts/whiteboard_shorts.py preflight \
  --source-project ../../outputs/tiktok2shorts/2026-08-16/example
python3 scripts/whiteboard_shorts.py init \
  --project-dir ../../projects/2026-08-16-tiktok-whiteboard \
  --source-project ../../outputs/tiktok2shorts/2026-08-16/example
python3 scripts/whiteboard_shorts.py music-fetch \
  --project-dir ../../projects/2026-08-16-tiktok-whiteboard
```

`--source-project`는 `tiktok2shorts score --target-format whiteboard`를 통과하고 `download`, `preview`, 원본 프레임과 storyboard 검토까지 마친 프로젝트여야 합니다. `preflight`는 점수 70점, 최소 프레임 6장, 서로 다른 행동 3개, hook·변화/payoff·conclusion 역할을 확인합니다. 원본 MP4, `source.json`, `storyboard.json`을 프로젝트 안으로 복사하며 권리 상태를 상향하지 않습니다.

기존 로컬 SRT 입력도 호환용으로 지원합니다.

```bash
python3 scripts/whiteboard_shorts.py init \
  --project-dir ../../projects/2026-08-16-srt-whiteboard \
  --srt /path/to/story.srt \
  --rights-status owned
```

`setup`은 OpenCV, NumPy, PyAV, Pillow가 격리 환경에 없을 때만 명시적으로 실행합니다.

```bash
python3 scripts/whiteboard_shorts.py setup
```

이미지와 annotation을 준비한 뒤 정적 검증과 미리보기를 실행합니다.

```bash
python3 scripts/whiteboard_shorts.py validate --project-dir <project> --render-ready
python3 scripts/whiteboard_shorts.py preview --project-dir <project> --scene scene-01 --regions-only
python3 scripts/whiteboard_shorts.py render --project-dir <project> --all
python3 scripts/whiteboard_shorts.py upload-package --project-dir <project>
```

전체 렌더는 `youtube-upload.json`과 `youtube-upload.md`를 만들며 시청자층·합성 콘텐츠·프로모션·연령 제한·미확정 권리는 검토 대상으로 남깁니다.

기존 출력은 `--overwrite`를 직접 지정하기 전에는 덮어쓰지 않습니다. 권리 상태가 불명확한 자산은 표시가 포함된 로컬 초안만 허용하며, 로컬 렌더 성공은 게시 권리를 증명하지 않습니다.
