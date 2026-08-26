# 보더콜리 TikTok 화이트보드 프로젝트 가져오기

## 완료 내용

- 사용자가 선택한 1번 후보 `@kelsieg23`의 TikTok 원본을 로그인과 쿠키 없이 로컬 검토용으로 다운로드했다.
- 원본 URL, 제작자, 다운로드 방식, 파일 크기, 재생 시간, SHA-256과 `unknown` 권리 상태를 보존했다.
- 19.3초 원본에서 0~18초 구간의 미리보기 프레임 10장을 생성하고 직접 검토했다.
- 실제 프레임에서 확인한 보더콜리의 응시, 카메라 이동, 검은 고양이 장식 공개, 문 가까이 이동, 마지막 같은 화면을 기준으로 한국어 대본과 5개 장면을 작성했다.
- 샘플 프레임에서 명확히 확인되지 않은 후보 설명의 `앞발 들기`는 대본과 화이트보드 장면 근거에서 제외했다.
- TikTok2Shorts 최종 로컬 준비 검증과 Whiteboard Shorts 원본 적합성 사전 검사를 통과했다.
- 원본과 장면 근거를 새 화이트보드 프로젝트로 가져오고 SRT, 장면 계획, 원본·스토리보드 스냅샷을 생성했다.
- 실제 SRT 길이에 맞춰 화이트보드 장면 계획을 목표 15.5초, 허용 15~20초로 정리했다.
- 사용자가 5개 장면의 그림 전략을 승인했다.
- 검토한 원본 프레임을 바탕으로 글자·로고가 없는 1080x1920 화이트보드 장면 이미지 5장을 생성하고 직접 확인했다.
- 실제 이미지에 보이는 문, 검은 고양이 모양 장식, 보더콜리의 위치를 기준으로 장면별 공개 순서와 정수 좌표 annotation을 작성했다.
- 생성 이미지 5장의 SHA-256, 원본 TikTok URL, 제작자, `synthetic: true`, `permission_status: unknown`을 권리 기록에 추가했다.
- 1번 장면의 번호·영역·손 이동 경로를 확인할 수 있는 로컬 검토 이미지를 생성했다.
- 사용자가 1번 장면의 영역 구성을 승인했다.
- 1번 장면의 540x960, 15 FPS 검토 영상을 생성하고 시작·중간·완성 프레임을 확인했다.
- 5개 장면을 1080x1920, 30 FPS로 렌더링하고 15.5초 H.264 무음 로컬 초안으로 병합했다.
- 시스템 FFmpeg의 `drawtext` 미지원 문제를 플러그인 0.2.1의 Pillow 이미지와 FFmpeg `overlay` 방식으로 수정하고, 상단 권리 미확인 표시가 유지되는 것을 확인했다.
- 기존 무음 초안을 보존하고, 장면별 코믹 자막과 직접 생성한 무보컬 BGM을 적용한 별도 v2 프로젝트를 완성했다.

## 결과 경로

- TikTok2Shorts 검토 프로젝트: `outputs/tiktok2shorts/2026-08-16/수의실에서-가짜-고양이를-발견한-보더콜리`
- Whiteboard Shorts 프로젝트: `projects/2026-08-16-border-collie-fake-cat-whiteboard`
- 원본 SHA-256: `2b4619ba9b833d2affcb464dac87633bb271bc666ab7ec41e16a9c8de27c3829`

## 검증 결과

- TikTok2Shorts `validate --final`: 통과
- Whiteboard Shorts `preflight`: 95.35점, 미리보기 10장, 장면 5개, 실제 행동 5개, 오류 없음
- Whiteboard Shorts 정적 `validate`: 통과, 오류·경고 없음
- Whiteboard Shorts `validate --render-ready`: 통과, 오류·경고 없음
- 1번 장면 영역 검토 이미지: `projects/2026-08-16-border-collie-fake-cat-whiteboard/previews/scene-01-regions.png`
- 1번 장면 검토 영상: 540x960, 15 FPS, H.264, 3초, 무음
- 전체 로컬 초안: `projects/2026-08-16-border-collie-fake-cat-whiteboard/outputs/preview.mp4`
- 전체 로컬 초안 규격: 1080x1920, 30 FPS, H.264, 15.5초, 무음
- 전체 로컬 초안 SHA-256: `3c36b76f5e3f80aebdf8b6d4008847bba694a926e4ce33c28b34c3ccb5313e2b`
- 자막·BGM v2: `projects/2026-08-16-border-collie-fake-cat-whiteboard-caption-bgm-v2/outputs/preview.mp4`
- 자막·BGM v2 SHA-256: `715d63b3e3d564f38f187d830e268b8103f755737515b1d88f04812343d01ccd`
- 시작, 고양이 장식 공개, 보더콜리 복귀, 문 가까이 이동, 마지막 동시 화면 프레임 확인 완료
- clean final 검사: 권리 `unknown`과 미완료 사용자 승인 항목 때문에 의도대로 차단됨
- 권리 상태: `unknown`
- 배포 상태: 로컬 검토 전용, 업로드하지 않음

## 사용자 확인 후 다음 단계

- 로컬 초안의 장면 전환과 손그림 동작을 사용자에게 확인받는다.
- 기존 렌더러의 손·마커 이미지에 인쇄 문자가 보이므로 필요하면 별도 승인 후 깨끗한 자산으로 교체한다.
- 권리 상태가 `unknown`이므로 현재는 권리 표시가 있는 로컬 초안까지만 허용한다.
