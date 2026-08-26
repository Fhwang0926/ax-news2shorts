# 포름알데히드 배추 쇼츠 검토 영상 완료

## 요청

- 선택한 뉴스 후보를 `영상까지` 범위로 제작한다.
- 확인된 중국 현지 위법 행위와 미확인인 한국 유입을 구분한다.
- 사건 영상·방송 캡처를 권리 근거 없이 사용하지 않는다.

## 반영 내용

- 캉바오현 공식 통보 재게시, SBS, 매일경제, IARC 자료를 교차 확인했다.
- `fact-stack` 7장면으로 후크, 공식 확인, 불법 사용, 유해성 분류, 유통 추적, 한국 유입 미확인, 결론을 구성했다.
- 내레이션은 공백 제외 189자로 정리했다.
- 7개 장면 모두 서로 다른 이미지를 사용했다.
- Wikimedia Commons의 CC0·퍼블릭도메인 실제 사진과 지도·분자 자료 5개를 수집했다.
- 재사용 권한이 확인되지 않은 사건 영상과 기사·방송 이미지는 제외했다.
- 공식 확인과 해외 유입 미확인 장면은 텍스트 없는 자체 평면 도식 2개로 제작했다.
- 생성 이미지 비율은 2/7, 약 28.6%로 제한했다.
- 화면에는 검토 문구나 합성 미디어 뱃지를 추가하지 않고 합성 여부를 프로젝트 메타데이터에만 기록했다.
- YouTube 제목, 설명, 태그, 썸네일 문구, 고정 댓글과 비공개 업로드 설정을 작성했다.
- Typecast 민감 뉴스용 자동 보이스 `Seohyeon`으로 장면별 음성과 CTA 음성을 합성했다.
- 첫 렌더에서 4.5초를 넘은 장면 두 개의 내레이션을 압축해 다시 렌더했다.
- 브랜드 인트로, 7개 뉴스 장면, 결론, 구독 CTA 순서의 36.53초 세로형 검토 영상을 만들었다.
- 3개 권리 승인 자산을 조합한 720×1280 썸네일을 만들었다.

## 변경 파일

- `projects/2026-08-24-formaldehyde-cabbage/project.json`: 버전 8 프로젝트 설정, 이슈 렌즈, 후크, 시선 장치.
- `projects/2026-08-24-formaldehyde-cabbage/sources.json`: 공식·독립·보건 출처 5개.
- `projects/2026-08-24-formaldehyde-cabbage/fact-sheet.json`: 확인 사실 4개와 미확인 사실 1개.
- `projects/2026-08-24-formaldehyde-cabbage/script.md`: 후크 비교, 최종 대본, 검증 메모.
- `projects/2026-08-24-formaldehyde-cabbage/storyboard.json`: 7장면 fact-stack 스토리보드.
- `projects/2026-08-24-formaldehyde-cabbage/rights-manifest.json`: 이미지 검색 판단과 자산별 사용권·관련성 기록.
- `projects/2026-08-24-formaldehyde-cabbage/assets/collected/`: 실제 사진·지도·분자 자료.
- `projects/2026-08-24-formaldehyde-cabbage/assets/generated/`: 자체 평면 도식과 재생성 스크립트.
- `projects/2026-08-24-formaldehyde-cabbage/validation-report.json`: 플러그인 검증 결과.
- `projects/2026-08-24-formaldehyde-cabbage/publish.json`: 링크 없는 YouTube 업로드 정보와 비공개 설정.
- `projects/2026-08-24-formaldehyde-cabbage/render-report.json`: Typecast 음성, 장면별 실측 길이, CTA와 썸네일 기록.
- `projects/2026-08-24-formaldehyde-cabbage/preview.mp4`: 720×1280 H.264/AAC 검토 영상.
- `projects/2026-08-24-formaldehyde-cabbage/thumbnail.jpg`: 720×1280 업로드용 썸네일.

## 검증

- 최신 설치본 `news2shorts 0.27.0`의 `doctor` 통과.
- 프로젝트 JSON 7개 파싱 통과.
- 플러그인 초안 검증 `ok: true`, 오류 0건.
- 장면 이미지 7개, 고유 경로 7개, 중복 0건.
- 권리 승인 자산 7개, 생성 자산 2개, 생성 비율 28.6%.
- 수집·생성 이미지를 직접 확인해 워터마크, 가짜 현장 재현, 깨진 도형, 의도하지 않은 문구가 없음을 확인했다.
- macOS Keychain의 Typecast 연결을 확인했고 키 값은 프로젝트·로그에 기록하지 않았다.
- 영상은 H.264 720×1280, 음성은 AAC 48kHz 스테레오, 총 길이는 36.528초로 확인했다.
- 일반 장면은 모두 4.5초 이하, 결론 장면은 5.636초로 권장 범위를 충족했다.
- 영상 접촉 시트와 썸네일을 직접 확인했고 UI 겹침, 워터마크, 검토·합성 뱃지가 없음을 확인했다.
- `upload-package` 출력에 미작성·검토 필요 항목이 없음을 확인했다.

## 남은 단계

- 건강 관련 민감 이슈이므로 현재 결과는 `preview.mp4` 검토본이며 최종 `short.mp4`는 만들지 않았다.
- 사용자가 영상과 업로드 정보를 승인하면 편집·권리·합성 공개 검토 상태를 기록한 뒤 최종본을 렌더한다.
- 사건 영상의 재사용 권리가 확인되지 않아 모든 근거 장면이 정지 이미지라는 권고 한 건이 남아 있다.
