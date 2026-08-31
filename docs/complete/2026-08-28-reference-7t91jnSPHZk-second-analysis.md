# YouTube Shorts 7t91jnSPHZk 1초 단위 분석 완료

## 완료 내용

- 공개 Shorts 원본과 자동 한국어 자막을 로컬 분석 전용으로 저장했다.
- 1080×1920 원본에서 0~37초 1초 간격 프레임 38장을 추출했다.
- 10초 단위 접촉시트 4장, 1초별 화면·자막·발화 CSV, 장면 경계 CSV와 자동자막 구간 CSV를 생성했다.
- FFmpeg 장면 점수로 12개 컷과 13개 비주얼 그룹을 확인했다.
- 음성 속도, 저음량 구간과 음량을 측정하고 상단 제목·하단 자막의 역할과 강조색 사용을 정리했다.

## 주요 결과

- 상단 흰색·노란색 2줄 제목은 전 구간 고정이다.
- 비주얼 평균 유지 시간은 약 2.85초, 화면 자막 평균 유지 시간은 약 1.55초다.
- 같은 비주얼을 유지하면서 하단 자막만 의미 절마다 교체한다.
- 자동자막 기준 전달 속도는 약 7.25자/초이며 0.15초 이상 저음량 구간은 두 번뿐이다.

## 산출물

- `projects/shorts-globalizer/2026-08-28/7t91jnSPHZk/reference-analysis/frames-1s/`
- `projects/shorts-globalizer/2026-08-28/7t91jnSPHZk/reference-analysis/contact-sheets/`
- `second-by-second.csv`, `shot-boundaries.csv`, `auto-caption-cues.csv`
- `asset-manifest.json`, `analysis.md`

## 제한

- 원본 에셋 권리는 검토하지 않았으며 결과는 로컬 분석 전용이다.
- 원본 워터마크·출처 표기를 제거하지 않았다.
- 원본 영상·음성·자막·브랜딩을 제작물에 재사용하거나 업로드하지 않았다.
- 프론트엔드 빌드와 DB 작업은 수행하지 않았다.
