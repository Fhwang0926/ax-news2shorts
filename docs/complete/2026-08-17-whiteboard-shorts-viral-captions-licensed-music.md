# Whiteboard Shorts 바이럴 자막·검증 음원 개선 완료

## 목적

- 설명형 문구를 실제 쇼츠처럼 훅, 재훅, 반전이 이어지는 짧은 반응형 문구로 개선한다.
- 유명 멜로디를 흉내 낸 합성곡 대신, 실제 짧은 영상에서 반복 사용된 근거와 재사용 라이선스가 확인된 녹음을 사용한다.
- 상용 차트곡은 영상 파일에 임의 삽입하지 않고 플랫폼 공식 음악 선택기로 넘기는 안전 경계를 유지한다.

## 플러그인 변경

- 플러그인 버전을 `0.5.0+codex.20260817`로 올렸다.
- `viral-punch` 자막 스타일과 `hook → setup → rehook → escalation → payoff` 검증을 추가했다.
- `viral-punch` 문구는 장면당 36자, 최대 두 줄로 제한하고 첫 장면 훅, 중간 재훅, 마지막 반전을 강제한다.
- 자막 작성 기준과 피해야 할 낡은 문구를 `caption-writing.md`에 분리했다.
- 검증 음원 카탈로그와 `licensed_catalog` 모드를 추가했다.
- `music-fetch`가 제작자 공식 HTTPS 파일을 받고 고정 SHA-256과 일치할 때만 프로젝트에 저장하도록 했다.
- macOS Python 인증서 환경과 무관하게 시스템 `curl`을 우선 사용하되 HTTPS, TLS 1.2 이상, 공식 URL과 해시 검증을 유지한다.
- 렌더 보고서에 음원 ID, 제목, 아티스트, 라이선스, 출처, 필수 크레딧을 기록한다.
- 카탈로그 음원을 사용하면 `delivery-note.md`를 만들어 게시 전 크레딧과 플랫폼 음악 선택기 경계를 안내한다.
- `viral-punch`도 노란 첫 줄, 흰 둘째 줄, 검은 외곽선의 쇼츠 자막으로 렌더한다.

## 검증 음원

- 제목: `Monkeys Spinning Monkeys`
- 제작자: Kevin MacLeod
- ISRC: `USUAN1400011`
- 라이선스: Creative Commons Attribution 4.0 International
- 공식 음원 SHA-256: `a5bb345c23849ad0786aa0bc5157a9f2d4039660fe00282e55754d475f36dc14`
- 선택 근거: 동물과 엉뚱한 장면을 포함한 수백만 TikTok과 수십억 재생의 대표 음원으로 보도된 사용 근거를 카탈로그에 보존했다.

## v4 샘플 문구

1. `잠깐… 위에 뭐야? / 보더콜리 레이더 켜짐`
2. `고양이 발견! / 근데 프레임이 멈춤`
3. `새로고침해도 그대로 / 혹시 와이파이 끊김?`
4. `직접 확인하러 감 / 거리 1칸 남음`
5. `반전: 고양이 아니었음 / 장식품한테 완전히 낚임`

## 샘플 결과

- 프로젝트: `projects/2026-08-17-border-collie-fake-cat-whiteboard-viral-audio-v4`
- 출력: `outputs/preview.mp4`
- 영상 SHA-256: `033bc9cd37f4ccc5d0e0985d877f0b74dcf405120a1b2ec48e9280c65a4003a1`
- 미디어: 1080x1920, 30 FPS, H.264, AAC 48 kHz 스테레오, 15.5초
- 실측 음량: -14.0 LUFS, true peak -1.5 dBFS
- 대표 프레임: `previews/contact-sheet.png`

## 확인 결과

- Python AST와 전체 JSON 구문 검사 통과
- Skill Creator `quick_validate` 소스와 설치본 통과
- 프로젝트 정적 검사와 `--render-ready` 검사 통과
- 공식 음원 다운로드와 SHA-256 일치 확인
- 설치본 `music-fetch` 재사용 경로와 해시 재검증 통과
- 설치본에 검토된 TikTok 프로젝트 경로만 넘겼을 때 `viral-punch`, 다섯 beat, `licensed_catalog`, `monkeys-spinning-monkeys`가 추가 조건 없이 자동 선택됨
- 렌더 결과 해상도, 프레임률, H.264/AAC 스트림 확인
- Codex 플러그인 `0.5.0+codex.20260817` 설치·활성 확인
- 설치본 `doctor`의 `ready_for_render: true` 확인
- clean final 검사는 원본 TikTok·장면 이미지 권리와 네 가지 사용자 승인이 미확인이라 의도대로 차단됨

## 변경 파일

- `plugins/whiteboard-shorts/scripts/whiteboard_shorts.py`
- `plugins/whiteboard-shorts/.codex-plugin/plugin.json`
- `plugins/whiteboard-shorts/README.md`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/SKILL.md`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/agents/openai.yaml`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/references/caption-writing.md`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/references/shorts-music-catalog.json`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/references/rights-policy.md`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/references/post-production-contract.md`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/references/output-contract.md`
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/templates/post-production.template.json`
- `projects/2026-08-17-border-collie-fake-cat-whiteboard-viral-audio-v4/`

## 권리 경계

- `Monkeys Spinning Monkeys` 녹음은 CC BY 4.0 필수 크레딧 조건으로 기록했다.
- TikTok 원본과 그 프레임을 근거로 만든 장면 이미지는 `unknown` 상태를 유지한다.
- 현재 MP4는 권리 경고가 포함된 로컬 검토본이며 게시·수익화 가능성을 증명하지 않는다.
- 상용 플랫폼 음원은 이 플러그인이 직접 섞지 않는다. 업로드 후 YouTube Shorts 공식 음악 선택기에서 추가해야 한다.
