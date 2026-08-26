# 2026-08-16 TikTok 고양이 3마리 행동 해설 Short 작업 완료

## 제작 결과

- 사용자가 선택한 `nowmi-three-cats-7659057655079718152` 후보를 5장면, 22.021초의 한국어 동물 행동 해설형 로컬 MP4로 제작했다.
- 후보 선정 시 TikTok 공개 페이지에서 조회 3,390만 회, 좋아요 1,040만 회, 댓글 4.34만 회, 공유 400만 회를 확인했다.
- 원본 프레임에서 회백색 고양이의 반복 앞발 접촉, 가운데 줄무늬 고양이의 고개·상체 회피와 앉은 자세 유지, 마지막 정지를 확인했다. 놀이·싸움·질투를 확정하지 않고 `관찰`과 `행동 해석`으로 구분했다.
- 가로 원본의 세 고양이가 모두 보이도록 원본 전체 프레임을 중앙에 둔 720×1280 세로 편집용 사본을 만들고 같은 영상의 흐린 배경으로 여백을 채웠다. 원본 파일과 SHA-256은 별도로 보존했다.
- 최종본은 720×1280, H.264/AAC, 30fps이며 TTS·외부 음원·업로드 기능을 사용하지 않았다. 원본 오디오는 낮추고 렌더러가 만든 무보컬 앰비언트를 합성했다.
- 원본 권리 상태는 `unknown`, 사용 범위는 `local_personal_use`, 배포 모드는 `local_only`로 유지했다.

## 원본 확보와 출처

- 원본: `https://www.tiktok.com/@nowmi413/video/7659057655079718152`
- 제작자: `@nowmi413`
- TikTok 공개 페이지에서 로그인 없이 재생과 공개 지표를 확인했다.
- 플러그인의 기본 공개 다운로드가 TikTok 메타데이터 응답 문제로 실패해, 계정·쿠키 없이 canonical TikTok URL만 TikWM 공개 변환 API에 전달하는 보조 경로로 재생용 MP4를 확보했다.
- 원본 SHA-256: `3b141f566a2530737f0a1683bd8c2290d1a1688f0cef1867d66d4b22e1deff45`
- 세로 편집용 사본 SHA-256: `5edff0072171e0c89d261f2ef92016db758d790a2a68b7a8e365ec89a91cf791`
- 최종 MP4 SHA-256: `9b50805f4947708315be03cce3b9d17a220481481ced0f4b94bdcdce407911dc`

## 결과 파일

- `outputs/tiktok2shorts/2026-08-16/three-cats-stare-and-paw-at-each-other/outputs/short.mp4`
- `outputs/tiktok2shorts/2026-08-16/three-cats-stare-and-paw-at-each-other/delivery-note.md`
- `outputs/tiktok2shorts/2026-08-16/three-cats-stare-and-paw-at-each-other/edit-plan.md`
- `outputs/tiktok2shorts/2026-08-16/three-cats-stare-and-paw-at-each-other/render-report.json`
- `outputs/tiktok2shorts/2026-08-16/three-cats-stare-and-paw-at-each-other/rights-manifest.json`
- `outputs/tiktok2shorts/2026-08-16/three-cats-stare-and-paw-at-each-other/assets/analysis/contact-sheet-1s.jpg`
- `outputs/tiktok2shorts/2026-08-16/three-cats-stare-and-paw-at-each-other/outputs/final-contact-sheet.jpg`

## 검증 경계

- 플러그인의 `validate --final`로 원본 구간 제한, 행동 근거 연결, 감정 표기, 마지막 결론 장면, 로컬 렌더 준비 상태를 확인했다.
- `ffprobe`로 22.021초, 720×1280, H.264 영상과 AAC 오디오, 30fps를 확인했다.
- 원본·1초 간격 프레임·최종 대표 프레임으로 세 고양이 가시성, 한국어 자막 안전 영역, 출처 표기와 첫 제목 줄바꿈을 확인했다.
- 외부 업로드, 게시 권한, 공정 이용, 수익화, 동물 행동의 전문적 진단은 수행하거나 보장하지 않았다.

## 변경 파일

- `outputs/tiktok2shorts/2026-08-16/three-cats-stare-and-paw-at-each-other/*`: 후보 근거, 원본·세로 편집용 사본, 행동 해설 대본, 스토리보드, 권리 기록, 편집 지시서, 전달 문서, 최종 MP4와 검증 자료를 생성했다.
- `docs/complete/2026-08-16-tiktok2shorts-nowmi-three-cats-short.md`: 당일 제작 결과와 검증 경계를 기록했다.
- 플러그인 코드와 외부 업로드 기능은 변경하지 않았다.
