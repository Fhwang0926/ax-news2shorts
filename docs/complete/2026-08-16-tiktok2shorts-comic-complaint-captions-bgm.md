# 2026-08-16 TikTok2Shorts 코믹 하소연 자막·BGM 개선 완료

## 결과

- 기존 고양이 3마리 v1·스토리 v2 결과는 덮어쓰지 않고 `three-cats-office-complaint-v3` 프로젝트를 새로 만들었다.
- 실제 앞발 접촉, 고개 움직임, 앉은 자세 유지, 카메라 앞 위치를 회사의 추가 업무와 반복 수정에 지친 직장인 상황에 빗댄 15초 상황극으로 재구성했다.
- 렌더 화면의 `동물 해설`, `행동 해석`, `근거` 배지를 제거했다. 행동 근거와 감정 신뢰 구분은 `storyboard.json`, `edit-plan.md`, `delivery-note.md`에 그대로 보존했다.
- 별도 이미지, 페이드, 장면 전환 효과 없이 하나의 연속 원본 영상 위에서 상황 제목과 하소연 자막만 바뀌도록 유지했다.
- 외부 음원 없이 렌더러가 새로 생성하는 `playful` BGM을 정적인 코드 톤에서 통통 튀는 5음 아르페지오, 짧은 저음과 타격 리듬으로 변경했다.
- 설치된 `tiktok2shorts@news2shorts-local` 플러그인을 `0.2.2+codex.202608161438`로 갱신했다.

## 화면 자막

1. `회의 3분 전, 벌써 싸하다` / `카메라 앞인데 나만 벌써 피곤함`
2. `앞발로 툭 얹은 추가 업무` / `‘이거 금방 끝나죠?’가 제일 무섭다`
3. `앞발 한 번만인 줄 알았지` / `왜 ‘다시 해주세요’가 세 번째죠`
4. `오늘도 직장인의 표정 관리` / `앉은 자세는 유지, 멘탈은 퇴근함`
5. `그 와중에 주황 고양이` / `난 싸움 말고 카메라부터 챙김`

사람 상황은 코믹 비유로만 사용하고 동물이 실제 직업, 관계, 감정이나 의도를 가졌다고 단정하지 않았다. 민감한 동물 복지 영상에는 이 코믹 의인화 방식을 적용하지 않도록 플러그인 지침에 경계를 추가했다.

## 플러그인 변경 파일

- `plugins/tiktok2shorts/scripts/tiktok2shorts.py`: 화면 분석 배지와 근거 줄을 제거하고 상·하단 자막 여백을 재배치했다. `playful` BGM을 코믹 아르페지오와 짧은 타격 리듬으로 변경했다.
- `plugins/tiktok2shorts/.codex-plugin/plugin.json`: 버전을 `0.2.2+codex.202608161438`로 올리고 코믹 하소연 자막과 분석 배지 없는 출력 방식을 인터페이스 설명에 반영했다.
- `plugins/tiktok2shorts/README.md`: 상황극 자막, 내부 근거 보존, 새 `playful` 음악 동작을 기록했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/SKILL.md`: 실제 동작에 맞춘 사람 상황 비유, 한 장면 한 웃음 포인트, 분석 배지 비노출 규칙을 추가했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/output-contract.md`: 내부 검증 정보와 화면 표시를 분리하고 코믹 음악 출력을 계약에 반영했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/editorial-and-rights.md`: 코믹 의인화의 허용 범위와 민감 장면 제외 규칙을 추가했다.

## 결과 파일

- `outputs/tiktok2shorts/2026-08-16/three-cats-office-complaint-v3/outputs/short.mp4`
- `outputs/tiktok2shorts/2026-08-16/three-cats-office-complaint-v3/delivery-note.md`
- `outputs/tiktok2shorts/2026-08-16/three-cats-office-complaint-v3/edit-plan.md`
- `outputs/tiktok2shorts/2026-08-16/three-cats-office-complaint-v3/render-report.json`
- `outputs/tiktok2shorts/2026-08-16/three-cats-office-complaint-v3/outputs/final-contact-sheet.jpg`
- `outputs/tiktok2shorts/2026-08-16/three-cats-office-complaint-v3/outputs/transition-check.jpg`

## 검증

- 플러그인 스크립트 구문 검사, 매니페스트·프로젝트 JSON 파싱, skill-creator `quick_validate.py`를 통과했다.
- 프로젝트 `validate --final`을 통과했다.
- 최종 MP4는 15.021초, 720×1280, 30fps, H.264/AAC 스테레오다.
- BGM 포함 여부와 음량을 검사해 평균 `-35.9 dB`, 최대 `-21.9 dB`를 확인했다.
- 5장면 대표 프레임으로 모든 자막이 안전 영역 안에 있고 `동물 해설`, `행동 해석`, `근거` 배지가 화면에 남지 않은 것을 확인했다.
- 장면 경계 프레임으로 검은 화면, 페이드, 별도 이미지 전환 없이 원본 동작이 이어지는 것을 확인했다.
- 최종 MP4 SHA-256은 `e053420ec186608b8f870f2adde620abb5956a2ace519ec7862b41ebf15cccbc`다.
- 원본 권리 상태는 `unknown`, 사용 범위는 `local_personal_use`, 배포 모드는 `local_only`로 유지했다. 외부 업로드, 게시 권한, 공정 이용과 수익화 가능성은 검증하지 않았다.

## 프로젝트 변경 파일

- `outputs/tiktok2shorts/2026-08-16/three-cats-office-complaint-v3/project.json`: v3 프로젝트와 분석 배지 없는 템플릿 설명을 기록했다.
- `storyboard.json`, `script.json`, `commentary-plan.json`: 실제 장면과 직장인 하소연 자막·시나리오를 연결했다.
- `music-plan.json`: 코믹 `playful` BGM 선택 이유와 자체 생성 권리 정보를 기록했다.
- `viral-analysis.json`, `publish.json`: 사람 상황 비유의 경계, 제목 후보와 설명을 반영했다.
- `edit-plan.md`, `delivery-note.md`, `render-report.json`, `outputs/*`: 최종 편집·전달·렌더·검증 결과를 생성했다.
- `docs/complete/2026-08-16-tiktok2shorts-comic-complaint-captions-bgm.md`: 당일 작업과 검증 경계를 기록했다.
