# 2026-08-16 TikTok2Shorts 원본 채널 배지 제거·라이선스 코믹 BGM 개선 완료

## 결과

- 기존 v1~v4 결과를 덮어쓰지 않고 `three-cats-famous-licensed-music-v5` 프로젝트를 새 버전으로 만들었다.
- 상단의 `원본 채널` 배지와 알약 모양을 제거하고 `TikTok @nowmi413` 채널명만 일반 텍스트로 유지했다.
- 역할명과 의인화 상황극 문구는 기존처럼 하단에서만 바뀐다.
- 배경음은 Kevin MacLeod의 `Monkeys Spinning Monkeys`로 교체했다. 이 곡은 저작권이 없는 음원이 아니라 CC BY 4.0 출처 표시 조건으로 사용할 수 있는 저작권 보호 음원이다.
- 곡명, 제작자, 공식 원본 페이지, 라이선스 URL, 필수 출처 문구, ISRC, 로컬 파일 SHA-256, 발췌·음량·페이드 수정 내역을 프로젝트에 기록했다.
- 원본 영상 권리 상태 `unknown`, 사용 범위 `local_personal_use`, 배포 모드 `local_only`, 업로드 기능 없음은 그대로 유지했다.

## 플러그인 변경 파일

- `plugins/tiktok2shorts/scripts/tiktok2shorts.py`: 상단 `원본 채널` 배지를 제거했다. `licensed_track` 음악 모드, 파일·라이선스·출처 검증, rights manifest SHA-256 검증, 라이선스 음원 반복·트림·페이드·믹스, 전달 문서와 렌더 보고서의 음악 출처 기록을 추가했다.
- `plugins/tiktok2shorts/.codex-plugin/plugin.json`: 버전을 `0.3.0+codex.202608161518`로 올리고 배지 없는 고정 채널명과 검증된 라이선스 무보컬 음악 흐름을 설명에 반영했다.
- `plugins/tiktok2shorts/README.md`: 생성 음악과 검증된 라이선스 음악의 두 경로, 필수 출처 기록, 상단 배지 제거를 안내했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/SKILL.md`: 저작권 없는 음원으로 오인하지 않는 규칙, 라이선스 음원 필수 필드와 SHA-256 검증, 배지 없는 상단 템플릿 계약을 추가했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/output-contract.md`: `licensed_track` 출력 계약과 권리 manifest 요건을 추가했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/editorial-and-rights.md`: 유명함·무료 다운로드·로열티 프리를 저작권 없음으로 간주하지 않는 음악 가드레일을 추가했다.

## 새 결과 프로젝트 변경 파일

- `project.json`: v5 프로젝트명과 배지 없는 채널명 템플릿 설명을 기록했다.
- `music-plan.json`: `licensed_track`, 곡·제작자·공식 출처·CC BY 4.0·필수 출처 문구·믹스 음량을 기록했다.
- `rights-manifest.json`: 음원 파일 출처, 라이선스, ISRC, SHA-256, 파일 크기, 원곡 길이와 출력용 수정 내역을 기록했다.
- `publish.json`: 설명과 별도 `music_attribution`에 필수 음악 출처와 변경 표시를 넣었다.
- `edit-plan.md`, `delivery-note.md`, `render-report.json`: 실제 사용 음원과 라이선스 출처, 최종 믹스 모드를 기록했다.
- `outputs/short.mp4`: 배지 없는 화면과 라이선스 코믹 BGM을 합성한 최종 로컬 MP4다.
- `outputs/final-contact-sheet.jpg`, `outputs/transition-check.jpg`: 대표 장면과 장면 경계 시각 검토 결과다.

## 음원 권리 기록

- 곡: `Monkeys Spinning Monkeys`
- 제작자: Kevin MacLeod
- 공식 원본: `https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1400011`
- 라이선스: CC BY 4.0
- 라이선스 URL: `https://creativecommons.org/licenses/by/4.0/`
- 필수 출처 문구: `"Monkeys Spinning Monkeys" Kevin MacLeod (incompetech.com) — Licensed under Creative Commons: By Attribution 4.0 — https://creativecommons.org/licenses/by/4.0/`
- 음원 파일 SHA-256: `a5bb345c23849ad0786aa0bc5157a9f2d4039660fe00282e55754d475f36dc14`
- 출력 변경: 15.021초 발췌, 배경 음량 조정, 시작·끝 페이드

## 검증

- 플러그인 스크립트 구문 검사와 매니페스트·프로젝트 JSON 파싱을 통과했다.
- skill-creator `quick_validate.py`에서 `Skill is valid!`를 확인했다.
- 프로젝트 `validate --final`을 통과했고 음원 로컬 파일 SHA-256과 rights manifest 기록이 일치했다.
- 대표 5장면과 4개 장면 경계 전후 프레임에서 `원본 채널` 배지 없이 채널명만 고정되는 것을 확인했다.
- 장면 경계에 페이드·검은 화면·별도 이미지 전환이 없는 것을 확인했다.
- 최종 MP4는 15.021초, 720×1280, 30fps, H.264/AAC 스테레오다.
- 최종 오디오 음량은 평균 `-29.9 dB`, 최대 `-13.5 dB`다.
- 최종 MP4 SHA-256은 `bcf5bff31cdc4be97c99d89f7668942fc267f150d2f26a46b6a75493cf9dfc70`다.
- 기술 검증은 저작권 허가, TikTok 원본의 게시 권리, 공정 이용, 플랫폼 승인이나 수익화 가능성을 보장하지 않는다.
