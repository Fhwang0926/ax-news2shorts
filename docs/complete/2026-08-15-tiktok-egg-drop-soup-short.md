# 2026-08-15 TikTok 에그드롭 수프 해설형 Short 작업 완료

## 제작 결과

- 사용자가 선택한 `jujumaoo-egg-drop-soup-20260714` 후보를 한국어 해설 중심의 로컬 MP4로 제작했다.
- 완성본은 31.023초, 720×1280, H.264 영상과 AAC 한국어 내레이션(Yuna)으로 출력했다.
- 원문 영상은 재료 장면 5.2초, 육수 장면 4.8초, 달걀 리본 장면 5.8초로 총 15.8초만 근거 화면으로 사용했다.
- 원문 오디오는 근거 장면에서 낮추고, 원문 자막·워터마크를 지우지 않은 채 별도 한국어 해설 자막과 출처 표기를 배치했다.
- 원문 권리 상태는 `unknown`으로 유지했다. 결과물은 `local_only`이며 업로드·공개 권한 또는 수익화 가능성을 의미하지 않는다.

## 결과 파일

- `outputs/tiktok2shorts/2026-08-15/egg-drop-soup/outputs/short.mp4`
- `outputs/tiktok2shorts/2026-08-15/egg-drop-soup/render-report.json`
- `outputs/tiktok2shorts/2026-08-15/egg-drop-soup/edit-plan.md`
- `outputs/tiktok2shorts/2026-08-15/egg-drop-soup/rights-manifest.json`

## 검증 경계

- `validate --final`로 해설·자막·장면 수·원문 구간 제한·로컬 준비 상태를 확인했다.
- `ffprobe`로 완성 MP4의 H.264, AAC, 720×1280, 영상·음성 스트림, 31.023초 길이를 확인했다.
- 추출 프레임으로 한국어 자막 안전 영역, 출처 표기, 원문 구간 분리 화면을 확인했다.
- 외부 업로드, 게시 권한, 수익화 판단, 라이선스의 법적 유효성은 검증하지 않았다.
