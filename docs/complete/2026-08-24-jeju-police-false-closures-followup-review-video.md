# 제주 실종사건 허위 종결 후속 쇼츠 검토 영상 완료

## 요청

- 제목을 `경찰이 무능한 소리 듣는다는 요즘`으로 고정한다.
- 한겨레의 제주 실종사건 허위 종결 후속 보도를 바탕으로 영상을 제작한다.
- 영상까지 만들되 민감 뉴스 검토 절차를 따른다.

## 반영 내용

- 한겨레 원문과 연합뉴스, SBS, 뉴시스 보도를 교차 확인했다.
- 동일 담당자의 실종 신고 두 건 허위 종결 조사, 실종 관리 자료 삭제, 다른 실종자의 사망 발견, 국수본 사과와 전국 전수조사를 분리해 기록했다.
- 법적·징계 책임, 사망 원인과 시점, 전수조사 결과는 미확인 사항으로 남겼다.
- `fact-stack` 6장면으로 질문형 훅, 두 건의 처리 정황, 피해 결과, 전국 전수조사, 관리자 책임 반문을 구성했다.
- 첫 질문을 `경찰관 한 명이 실종 신고 두 건을 허위 종결했다면, 누구를 믿습니까?`로 작성했다.
- 결론은 `관리자 승인과 기록 검증도 없었다면 개인 일탈로만 볼 수 있는가`를 묻도록 작성했다.
- 제주경찰청 실제 건물 사진, 경찰차, 제주·대한민국 지도, 경찰청 건물 사진을 사용했다.
- 모든 장면은 서로 다른 파일을 사용했고, 기사 사진·방송 캡처·실종자 사진은 재사용 권리와 사생활 문제로 제외했다.
- Typecast 민감 뉴스용 자동 보이스 `Seohyeon`으로 본문과 구독 CTA 음성을 합성했다.
- 장면 전환 효과는 사용하지 않고 첫 기관 책임 장면에 줌인, 전국 조사 장면에 줌아웃만 적용했다.
- 720×1280 H.264/AAC 검토 영상과 별도 합성 썸네일을 만들었다.
- CapCut Desktop, CapCut Web, Vrew, SRT 호환 편집 패키지를 함께 만들었다.
- 링크 없는 설명, 제목 해시태그, 태그, 세부 설정, 고정 댓글을 작성했다.

## 변경 파일

- `projects/2026-08-24-jeju-police-false-closures-followup/project.json`: 프로젝트 범위, 민감 주제, 질문형 훅과 이슈 렌즈.
- `projects/2026-08-24-jeju-police-false-closures-followup/sources.json`: 원문과 독립 교차 출처.
- `projects/2026-08-24-jeju-police-false-closures-followup/fact-sheet.json`: 확인 사실과 미확인 사실.
- `projects/2026-08-24-jeju-police-false-closures-followup/script.md`: 훅 후보, 최종 대본, 결론과 검증 메모.
- `projects/2026-08-24-jeju-police-false-closures-followup/storyboard.json`: 6장면 팩트스택, 증거 카드와 제한적 줌.
- `projects/2026-08-24-jeju-police-false-closures-followup/rights-manifest.json`: 이미지 출처, 라이선스, 관련성, 사용 승인 기록.
- `projects/2026-08-24-jeju-police-false-closures-followup/assets/collected/`: 권리가 확인된 실제 기관·경찰 관련 사진과 지도.
- `projects/2026-08-24-jeju-police-false-closures-followup/publish.json`: YouTube 업로드 정보와 비공개 설정.
- `projects/2026-08-24-jeju-police-false-closures-followup/render-report.json`: Typecast 보이스, 장면별 실측 길이, 썸네일과 편집 패키지 기록.
- `projects/2026-08-24-jeju-police-false-closures-followup/preview.mp4`: 720×1280 H.264/AAC 검토 영상.
- `projects/2026-08-24-jeju-police-false-closures-followup/thumbnail.jpg`: 실제 자산 세 개를 합성한 720×1280 썸네일.
- `projects/2026-08-24-jeju-police-false-closures-followup/edit-package/preview/`: 편집용 영상, SRT, 타임라인, 매니페스트와 사용 방법.

## 검증

- 최신 설치본 `news2shorts 0.29.0`의 초안 검증은 `ok: true`, 오류 0건이다.
- macOS Keychain의 Typecast 연결을 확인했고 키 값은 프로젝트와 로그에 기록하지 않았다.
- 영상은 H.264 720×1280, AAC 음성, 총 34.651초로 확인했다.
- 본문과 CTA의 모든 음성 소스는 Typecast이며 자동 선택 보이스는 `Seohyeon`이다.
- 접촉 시트와 결론 프레임, 썸네일을 직접 확인해 글자 겹침, 이미지 잘림, 워터마크, 검토 표시가 없음을 확인했다.
- 고유 장면 이미지 6개를 사용했고 반복 경로는 없다.
- `upload-package`에 제목, 설명, 태그, 세부 설정, 고정 댓글이 모두 작성돼 있다.
- 권리가 확인된 사건 동영상이 없어 근거 장면이 정지 이미지라는 권고가 남아 있다.
- Typecast 실측 길이 변동으로 일반 장면 세 개가 4.5초 권장치보다 0.1~0.3초 길지만 전체 영상은 34.651초다.

## 남은 단계

- 범죄·실종 관련 민감 뉴스이므로 현재 결과는 `preview.mp4` 검토본이다.
- 사용자가 대본과 표현을 승인하면 편집·권리·합성 공개 상태를 확정하고 최종 `short.mp4`를 렌더한다.
