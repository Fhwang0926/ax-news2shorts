# 2026-08-16 TikTok2Shorts 상단 고정 채널·역할형 자막 개선 완료

## 결과

- 기존 v1·v2·v3 결과는 덮어쓰지 않고 `three-cats-roleplay-channel-header-v4` 프로젝트를 새로 만들었다.
- 상단에는 검증된 원본 채널 정보 `TikTok @nowmi413`만 고정하고 장면별 역할명·대사·하소연은 모두 하단에 표시했다.
- 회백색 고양이는 `팀장`, 줄무늬 고양이는 `대리`, 주황 고양이는 `눈치 빠른 신입`으로 역할을 정하고 다섯 장면에서 바꾸지 않았다.
- 역할은 실제 앞발 접촉, 고개 움직임, 앉은 자세 유지, 카메라 앞 위치에 맞췄다. 동물의 실제 직업·관계·감정·의도라는 주장은 하지 않았다.
- 기존 통통 튀는 자체 생성 `playful` 무보컬 BGM, 연속 원본 영상, 무전환 편집을 유지했다.
- 설치된 `tiktok2shorts@news2shorts-local` 플러그인을 `0.2.3+codex.202608161451`로 갱신했다.

## 역할과 하단 자막

1. `눈치 빠른 신입 · 주황 고양이` / `카메라 켰더니 팀장과 대리님이 벌써 분위기 잡고 있음`
2. `팀장 역할 · 회백색 고양이` / `‘이거 하나만 해줄래?’ 말보다 앞발이 먼저 나옴`
3. `대리 역할 · 줄무늬 고양이` / `한 번만 수정한다며? 앞발 또 오자 고개부터 피함`
4. `대리님의 마지막 이성` / `머리는 이미 퇴근했지만 앉은 자세만큼은 프로답게`
5. `신입 주황 고양이의 결론` / `둘이 해결하는 동안 나는 카메라부터 챙긴다`

## 플러그인 변경 파일

- `plugins/tiktok2shorts/scripts/tiktok2shorts.py`: 새 프로젝트에 원본 제작자 기반 `template.channel_label`을 생성한다. 렌더 상단에는 이 채널 정보만 고정하고 장면별 `headline`과 `korean_caption`은 모두 하단에 렌더한다. 상단 채널과 다른 보조 자산 출처는 하단 출처 표기를 유지한다.
- `plugins/tiktok2shorts/.codex-plugin/plugin.json`: 버전을 `0.2.3+codex.202608161451`로 올리고 고정 채널 헤더, 일관된 의인화 역할, 하단 전용 자막을 인터페이스 설명과 기본 요청에 반영했다.
- `plugins/tiktok2shorts/README.md`: 상단 고정 채널, 하단 역할·서사 자막, 역할 유지 규칙을 기록했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/SKILL.md`: 여러 동물의 역할표를 먼저 정하고 결론까지 화자·직급·관계를 유지하는 절차를 추가했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/output-contract.md`: `template.channel_label`, 하단 전용 화면 문구와 역할 관계 보존 계약을 추가했다.
- `plugins/tiktok2shorts/skills/tiktok2shorts/references/editorial-and-rights.md`: 상단에는 검증된 채널 정보만 두고 의인화 문구는 하단에만 두는 편집 경계를 추가했다.

## 결과 파일

- `outputs/tiktok2shorts/2026-08-16/three-cats-roleplay-channel-header-v4/outputs/short.mp4`
- `outputs/tiktok2shorts/2026-08-16/three-cats-roleplay-channel-header-v4/delivery-note.md`
- `outputs/tiktok2shorts/2026-08-16/three-cats-roleplay-channel-header-v4/edit-plan.md`
- `outputs/tiktok2shorts/2026-08-16/three-cats-roleplay-channel-header-v4/render-report.json`
- `outputs/tiktok2shorts/2026-08-16/three-cats-roleplay-channel-header-v4/outputs/final-contact-sheet.jpg`
- `outputs/tiktok2shorts/2026-08-16/three-cats-roleplay-channel-header-v4/outputs/transition-check.jpg`

## 검증

- 플러그인 스크립트 구문 검사, 매니페스트·프로젝트 JSON 파싱과 skill-creator `quick_validate.py`를 통과했다.
- 프로젝트 `validate --final`을 통과했다.
- 대표 프레임으로 상단 채널 정보가 모든 장면에서 같고 역할·대사·하소연이 하단에만 있는 것을 확인했다.
- 장면 경계 프레임으로 검은 화면, 페이드, 별도 이미지 전환 없이 원본 동작이 이어지는 것을 확인했다.
- 최종 MP4는 15.021초, 720×1280, 30fps, H.264/AAC 스테레오다.
- BGM 음량은 평균 `-35.9 dB`, 최대 `-21.9 dB`다.
- 최종 MP4 SHA-256은 `10a834ad82b87dc417508ad7874e07963fb3c05f0ba6558c8feddc7497375f1b`다.
- 원본 권리 상태는 `unknown`, 사용 범위는 `local_personal_use`, 배포 모드는 `local_only`로 유지했다. 외부 업로드, 게시 권한, 공정 이용과 수익화 가능성은 검증하지 않았다.

## 프로젝트 변경 파일

- `project.json`: v4 프로젝트명과 상단 고정 채널 정보를 기록했다.
- `storyboard.json`, `script.json`, `commentary-plan.json`: 고양이별 고정 역할과 실제 장면에 연결된 하단 자막·시나리오를 기록했다.
- `music-plan.json`: 역할형 상황극에 맞춘 `playful` BGM 선택 이유를 기록했다.
- `viral-analysis.json`, `publish.json`: 일관된 의인화 역할, 하단 전용 문구와 제목 후보를 반영했다.
- `edit-plan.md`, `delivery-note.md`, `render-report.json`, `outputs/*`: 최종 편집·전달·렌더·검증 결과를 생성했다.
- `docs/complete/2026-08-16-tiktok2shorts-fixed-channel-roleplay-captions.md`: 당일 작업과 검증 경계를 기록했다.
