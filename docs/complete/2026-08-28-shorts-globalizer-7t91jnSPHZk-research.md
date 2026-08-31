# Shorts Globalizer 7t91jnSPHZk 조사 완료

## 완료 내용

- 기존 `transcript_pending` 프로젝트를 검증된 `certifi` CA로 재개해 공개 자동 한국어 자막 수집에 성공했다.
- 원본 Shorts는 주제 신호와 구조 분석에만 사용하고 사실 출처에서는 제외했다.
- 서울시 공식 위촉 자료, 서울시 발표를 직접 취재한 SBS 보도, 서울신문·스포츠월드 보도, 동작구의회 공식 회의록, 머니투데이 보도를 분리해 기록했다.
- 홍보대사 위촉과 사임 의사, CCTV 공개 후 사과, 회의록의 강연 섭외 금액 언급을 확인 가능한 범위로 정리했다.
- 원본 Shorts의 ‘원래부터 분노가 많았다’, ‘강연료가 부족해서 예민했다’, ‘정확히 1,500만 원을 원했다’는 인물 성격·동기 해석은 확인되지 않은 주장으로 분리했다.
- Global Potential Score는 가중점수 `56.75`, 감점 `85`, 최종 `0.0 / SKIP`으로 계산됐다.
- `SKIP` 판정에 따라 영어 대본, 스토리보드, 에셋 계획, CapCut 인계 패키지는 생성하지 않았다.

## 변경 파일

- `projects/shorts-globalizer/2026-08-28/7t91jnSPHZk/project.json`
  - 상태를 `transcript_pending`에서 `ingested`, 최종 `blocked`로 갱신했다.
- `projects/shorts-globalizer/2026-08-28/7t91jnSPHZk/source.json`
  - 공개 메타데이터와 자동 한국어 자막 수집 정보를 기록했다.
- `projects/shorts-globalizer/2026-08-28/7t91jnSPHZk/transcript.txt`
  - 공개 자동 한국어 자막을 기록했다.
- `projects/shorts-globalizer/2026-08-28/7t91jnSPHZk/source-analysis.json`
  - 신호 구조, 민감 주제, 출처 순서, 글로벌 점수 근거를 기록했다.
- `projects/shorts-globalizer/2026-08-28/7t91jnSPHZk/sources.json`
  - 공식·1차·독립 출처 6개를 기록했다.
- `projects/shorts-globalizer/2026-08-28/7t91jnSPHZk/fact-sheet.json`
  - 확인·귀속·미확인 주장을 구분해 기록했다.
- `projects/shorts-globalizer/2026-08-28/7t91jnSPHZk/global-score.json`
  - CLI가 계산한 점수와 `SKIP` 판정을 기록했다.

## 검증 결과

- 라이브 YouTube 공개 메타데이터·자동 한국어 자막 ingest: 성공
- `validate --stage research`: 오류·경고 없이 통과
- `score`: `0.0 / SKIP`, `publication_ready: false`
- 프론트엔드 변경, DB 작업, 빌드, TTS, 렌더링, 영상 다운로드, 업로드는 수행하지 않았다.

## 범위 제한

- `SKIP` 프로젝트는 연구 승인을 진행하거나 영어 제작 초안을 만들 수 없다.
- 원본 Shorts 영상·음성·썸네일·자막·브랜딩은 에셋으로 재사용하지 않았다.
- 별도 영어권 원본 제작이 필요하면 확인 가능한 보편 주제를 가진 다른 Shorts를 선택해야 한다.
