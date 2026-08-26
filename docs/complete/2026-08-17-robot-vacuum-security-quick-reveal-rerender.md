# 로봇청소기 보안 개정안 quick-reveal 재제작 완료

## 완료 내용

- 기존 `projects/2026-08-16-robot-vacuum-security-bill` 프로젝트를 새 프로젝트로 복제하지 않고 재사용했다.
- 2026년 8월 17일 기준 국민참여입법센터 의안 상태와 국가법령정보센터 현행법을 다시 확인했다.
- 공식 KISA 자료와 범위가 다른 기사 내 `16개 보안 항목` 수치는 영상에서 계속 제외했다.
- 전체 사업자의 `품질개선 계획 회신`으로 공식 발표 범위에 맞추고, 장면 대사를 질문과 응답이 이어지는 흐름으로 다듬었다.
- 모든 장면에 보도 출처 라벨과 근거 source ID를 연결했다.
- 마지막 payoff에 새 편집형 결론 카드용 `payoff_title`, `payoff_detail`을 적용했다.
- 공식 공공누리 시각물의 기사 연관성과 생성 설명 그래픽의 시각 품질을 검토해 권리 기록에 반영했다.
- 첫 다은 미리보기가 50.1초로 늘어나 중복 전환 장면을 제거하고 대사를 7장면 quick-reveal로 압축했다.
- 다은 Voice ID `tc_692799c46508f6b9468c54c7`, Typecast `ssfm-v30`, tempo 1.15로 최종 영상을 렌더했다.

## 변경 파일

- `projects/2026-08-16-robot-vacuum-security-bill/project.json`: 새 결론 카드·출처 표시·검토 승인·다은 최종 렌더 상태 반영
- `projects/2026-08-16-robot-vacuum-security-bill/sources.json`: 2026년 8월 17일 확인 시점과 국가법령정보센터 현행법 추가
- `projects/2026-08-16-robot-vacuum-security-bill/fact-sheet.json`: 공식 개선 조치 범위와 현행 법안 상태 보강
- `projects/2026-08-16-robot-vacuum-security-bill/script.md`: 7장면 대화형 quick-reveal 대본으로 압축
- `projects/2026-08-16-robot-vacuum-security-bill/storyboard.json`: 출처 필드와 편집형 결론 카드, 목적형 모션 반영
- `projects/2026-08-16-robot-vacuum-security-bill/rights-manifest.json`: 실제 뉴스 연관성 및 생성 시각물 품질 검토 기록
- `projects/2026-08-16-robot-vacuum-security-bill/publish.json`: 확인 날짜와 현행법 출처 갱신
- `projects/2026-08-16-robot-vacuum-security-bill/render-report.json`: 다은 보이스와 최종 렌더 증거 기록
- `projects/2026-08-16-robot-vacuum-security-bill/short.mp4`: 최종 영상

## 검증

- `news2shorts validate --final`: 오류 0건, 경고 0건
- 최종 영상: 720x1280, H.264, 30fps, AAC 48kHz 모노, 32.427초
- TTS: Typecast `ssfm-v30`, Daeun `tc_692799c46508f6b9468c54c7`
- 장면 전환: 하드 컷
- 최종 프레임: 검은 화면 없음, 편집형 결론 카드·뉴스 출처·AI 재현 표시 육안 확인

## 미실행 범위

- 프론트엔드 빌드
- 데이터베이스 작업
- 업로드 또는 게시
