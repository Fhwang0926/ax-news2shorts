# 전월세 안심신탁 퀵리빌 리뷰 영상 제작

## 요청

- 선택한 1번 주제인 전월세 안심신탁을 퀵리빌 영상으로 제작한다.
- 실제 관련 사진과 공식 자료를 사용하고, 생성 이미지는 장면별로 중복 없이 구성한다.
- Typecast 음성을 사용하고 결론은 사실을 먼저 밝힌 뒤 월세 전환 가능성을 반문한다.

## 결과

- 리뷰 영상: 6장면과 공통 CTA, 26.781초
- 출력: H.264, AAC, 720×1280
- 음성: Typecast `Seohyeon` (`tc_69f2e455ea79fd197aa0476f`), 자동 뉴스 전달형 선택
- 형식: 퀵리빌, 장면 전환 효과 없음, 첫 장면의 대상 강조에만 시간 지정 줌 인 적용
- 결론: 전세금 안정화 기구 예탁과 선택형 시범이라는 사실을 먼저 제시하고, 전세 공급 감소·월세 전환 우려를 반문형으로 마무리

## 사실·권리 처리

- 대한민국 정책브리핑·국토교통부 자료를 주 근거로 사용하고 뉴스1, 뉴스핌, 스카이데일리로 구조·일정·우려를 교차 확인했다.
- 모든 전세계약에 적용되는 의무 제도가 아니라는 조건을 두 번째 장면에서 명시했다.
- 연 4~5%는 정부 예상치이며 보장 수익률로 표현하지 않았다.
- CC BY 2.0이 확인된 서울 아파트 실사진과 국토교통부 공식 정책자료의 관련 부분을 사용했다.
- 기사 사진과 국토교통부 현장사진은 명시적 재사용 조건을 확인하지 못해 제외했다.
- 설명용 합성 픽토그램 네 장은 서로 다른 이미지이며 모두 720×1279 이하로 축소했다.

## 변경 파일

- `projects/2026-08-20-jeonse-trust-quick-reveal/project.json`: 자동 포맷, 후크, Typecast 자동 보이스, 검수 상태
- `projects/2026-08-20-jeonse-trust-quick-reveal/sources.json`: 공식·독립 출처와 조회 시점
- `projects/2026-08-20-jeonse-trust-quick-reveal/fact-sheet.json`: 확인 사실, 귀속 주장, 전문가 우려, 미확인 범위
- `projects/2026-08-20-jeonse-trust-quick-reveal/script.md`: 짧은 연결 대사와 반문형 결론
- `projects/2026-08-20-jeonse-trust-quick-reveal/storyboard.json`: 6장면 화면 문구, 시각 자료, 장면 연결, 제한적 줌
- `projects/2026-08-20-jeonse-trust-quick-reveal/rights-manifest.json`: 실사진·공식 문서·생성 이미지의 권리와 연관성 기록
- `projects/2026-08-20-jeonse-trust-quick-reveal/publish.json`: 링크 없는 제목·설명·태그·업로드 설정·고정 댓글
- `projects/2026-08-20-jeonse-trust-quick-reveal/assets/`: CC 사진, 공식 문서 확대 화면, 장면별 픽토그램
- `projects/2026-08-20-jeonse-trust-quick-reveal/preview.mp4`: 최종 승인 전 리뷰 영상
- `projects/2026-08-20-jeonse-trust-quick-reveal/review-contact.png`: 장면별 화면 검토용 접촉표
- `docs/complete/2026-08-20-jeonse-ansim-trust-quick-reveal-review.md`: 당일 제작·검증 기록

## 검증

- `validate` 통과: 오류 0건, 경고 0건
- 영상 확인: 26.781초, 720×1280, H.264/AAC, 음성 포함
- 평균 음량 확인: 주 음성 트랙 약 -14.3 dB
- SHA-256: `d9e869013c64ad8a08cba9729432d2e16e1a9fb7723745c879e32c991530a9fc`
- 금융·주거 민감 주제이므로 현재 파일은 리뷰본이며, 사용자 승인 뒤 최종 렌더할 수 있다.
- YouTube 업로드·게시·예약은 수행하지 않았다.
