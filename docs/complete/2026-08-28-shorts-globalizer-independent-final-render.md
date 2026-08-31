# Shorts Globalizer 독립 영문 최종 렌더 작업 완료

## 완료 내용

- 승인된 `shorts-globalizer` 영문 대본과 8장면 패키지를 기반으로 1080x1920 영문 로컬 최종본을 제작했다.
- 원 뇌전구 영상, CCTV, 음성, 자막, 썸네일, 채널 브랜딩은 사용하지 않았다.
- 장면 1·2·4·5·7·8은 프로젝트 로컬 Pillow 렌더러로 직접 만든 그래픽을 사용했다.
- 장면 3·6은 실제 인물과 무관한 비식별 합성 일러스트를 OpenAI 내장 이미지 생성으로 제작했다.
- 모든 장면에 `AI VOICE • SOME SYNTHETIC VISUALS`를 표시하고 합성 장면에는 `SYNTHETIC VISUAL`을 별도 표시했다.
- Typecast 공식 V2 음성 목록에서 Shorts·뉴스·다큐 용도가 표시된 원본 보이스 Walter를 선택했다.
- Typecast `ssfm-v30`, 영어, 연속 합성 1회로 음성과 단어 타임스탬프를 만들었다.
- 40.982초 Typecast 원본 음성을 1.037519배 보정해 39.5초 타임라인에 맞췄고, `-16 LUFS` 목표로 정규화했다.
- 외부 배경음악은 사용하지 않았다.
- 장면별 최종 SRT, 렌더 스크립트, 음성 생성 스크립트, 출처·합성 고지·QA 보고서를 저장했다.
- v0.1 패키지의 미디어 금지 계약을 유지하기 위해 실제 제작물은 프로젝트 폴더가 아니라 별도 `outputs/shorts-globalizer` 경로에 저장했다.

## 산출물

- `outputs/shorts-globalizer/2026-08-28/jc_BRabpPfc/outputs/short_en_final.mp4`
- `outputs/shorts-globalizer/2026-08-28/jc_BRabpPfc/outputs/thumbnail.png`
- `outputs/shorts-globalizer/2026-08-28/jc_BRabpPfc/subtitles-final.srt`
- `outputs/shorts-globalizer/2026-08-28/jc_BRabpPfc/provenance.json`
- `outputs/shorts-globalizer/2026-08-28/jc_BRabpPfc/reports/production-report.json`
- `outputs/shorts-globalizer/2026-08-28/jc_BRabpPfc/reports/qa-report.json`
- `outputs/shorts-globalizer/2026-08-28/jc_BRabpPfc/generate_typecast.py`
- `outputs/shorts-globalizer/2026-08-28/jc_BRabpPfc/render_final.py`

## 검증 결과

- MP4: H.264 High, yuv420p, 1080x1920, 30fps, 39.5초
- Audio: AAC, 48kHz, stereo, 192kbps
- 전체 1,185프레임 FFmpeg 디코딩 통과
- `blackdetect=d=0.20:pic_th=0.98`: 검은 구간 미검출
- `silencedetect=n=-45dB:d=1.0`: 1초 이상 무음 미검출
- 최종 음량: -16.1 LUFS, LRA 2.0 LU, true peak -4.4 dBFS
- SRT 8개 cue, 단조 증가, 마지막 종료 39.5초
- 8장면 contact sheet와 실제 렌더 프레임 strip 육안 검토 통과
- 출력 SHA-256: `eaf62d31ced8be0b67acfe70aecf8b139429904cbeaf58c1e9df603446e324d1`
- 제작물을 별도 outputs 경로로 분리한 뒤 원래 v0.1 package 검증도 오류·경고 없이 재통과
- 프론트엔드 빌드와 DB 작업은 수행하지 않았다.

## 제한 및 게시 경계

- 로컬 최종 편집본과 전체 디코딩을 검증했지만 YouTube 업로드·게시를 수행하지 않았다.
- 사용자 미리보기 승인과 업로드 승인이 별도로 기록되지 않아 `preview_approved: false`, `publish_blocked: true`를 유지한다.
- 게시 전 플랫폼의 합성 콘텐츠 설정을 활성화해야 한다.
- Typecast 음성에는 사용 계정의 제공자 약관이 적용된다.
