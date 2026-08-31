# Output contract

## 프로젝트 구조

```text
project-dir/
├── project.json
├── story.json
├── image-prompts.json
├── discovery/
│   └── selection.json
├── images/
│   ├── scene01.png
│   └── scene08.png
├── audio/
│   ├── scene01.aiff
│   ├── scene08.aiff
│   └── audio-manifest.json
├── subtitles/
│   ├── subtitle.json
│   └── subtitle.ass
├── video/
│   ├── scene01.mp4
│   ├── scene08.mp4
│   └── combined.mp4
└── final/
    ├── review.mp4
    ├── final.mp4
    └── render-report.json
```

## 이미지

- 장면당 이미지 1개, 최소 세로형 구도
- 등장인물의 얼굴, 연령, 머리, 의상 유지
- 이미지 내부 글자, 로고, 워터마크 금지
- 손과 얼굴 오류는 자동 검증으로 확정하지 않고 실제 프레임 검토 필요

## 음성

- 장면당 음성 1개
- 빠르게 몰아 읽지 않고 시니어 시청자가 구분할 수 있는 속도
- 외부 TTS 키를 코드, 프로젝트 JSON, 대화에 기록하지 않음
- macOS TTS는 로컬 검토 편의 기능이며 상업적 사용 권리를 대신 판단하지 않음

## 자막

- 1080×1920 기준 중앙 하단
- 1~2줄, 한 줄 16자 이하
- 흰색 본문, 노란색 핵심어, 검정 외곽선
- 화면 안전 영역을 벗어나지 않음
- FFmpeg `ass`·`drawtext`가 있으면 ASS를 사용하고, 없으면 Pillow 투명 PNG와 FFmpeg `overlay`로 같은 자막 계약을 유지함

## 검증 수준

- `discover`: 공개 YouTube 메타데이터 신호 수집, 자동 선택·다운로드 없음
- `select`: 정확히 3개인 창작 후보 중 사용자가 지정한 ID 기록
- `validate`: JSON·대본 계약 정적 검사
- `validate --render-ready`: 승인, 이미지, 음성, ASS 파일 확인
- `render --draft`: 로컬 검토본 생성
- `validate --publish-ready`: 검토 승인까지 확인
- `render --final`: 로컬 최종본 생성
- `validate --final`: FFprobe로 해상도와 영상·음성 스트림 확인

이 검증은 실제 업로드, 플랫폼 승인, 수익화 적합성, 외부 서비스 동작을 증명하지 않습니다.
