# 월미도 디스코팡팡 추락 사고 쇼츠 검토 영상 완료

## 요청

- 선택한 2번 뉴스로 영상까지 제작한다.
- 현재 `news2shorts` 플러그인의 질문형 훅, 실제 지역·대상 사진, Typecast, 퀵리빌 규칙을 적용한다.

## 반영 내용

- 연합뉴스 원보도와 조선일보, 매일경제 보도를 교차 확인했다.
- 2026년 8월 23일 밤 인천 월미도에서 발생한 30대 탑승객 추락, 머리·목 통증, 병원 이송, 경찰 조사 방침을 확인 사실로 분리했다.
- 놀이기구 고장, 안전장치 문제, 안전수칙 위반, 운영 과실과 특정인의 책임은 미확인 사항으로 남겼다.
- 자동 선택 포맷은 `quick-reveal`이며 첫 질문은 `월미도 추락, 원인은 아직 모른다?`로 구성했다.
- 결론은 `추락·부상 확인 / 정확한 원인 조사 중`으로 첫 질문을 명확히 회수했다.
- 실제 월미도 놀이공원 사진 1장과 동일 Tagada 기종 자료사진 4장을 서로 다른 장면에 사용했다.
- 기사·통신사 사진은 상업적 재사용 근거가 확인되지 않아 사용하지 않았다.
- 동일 기종 자료사진에는 `사건 현장 아님`을 화면과 권리 기록에 명시했다.
- 강조 줌은 첫 훅의 원형 탑승부·난간에만 사용했다.
- Typecast 자동 선택 민감 뉴스 보이스 `Seohyeon`으로 본문과 구독 CTA를 합성했다.
- 별도 합성 썸네일과 CapCut Desktop, CapCut Web, Vrew, SRT 호환 편집 패키지를 만들었다.
- 링크 없는 설명, 제목 해시태그, 태그, 업로드 설정과 고정 댓글을 작성했다.

## 변경 파일

- `projects/2026-08-24-wolmido-disco-pangpang-accident-review/project.json`: 프로젝트 범위, 자동 포맷, 민감 뉴스 설정, 질문형 훅과 결론.
- `projects/2026-08-24-wolmido-disco-pangpang-accident-review/sources.json`: 원보도와 독립 교차 출처 2건.
- `projects/2026-08-24-wolmido-disco-pangpang-accident-review/fact-sheet.json`: 확인 사실 5건과 미확인 사항.
- `projects/2026-08-24-wolmido-disco-pangpang-accident-review/script.md`: 훅 후보, 최종 대본, 스토리 연결과 검증 메모.
- `projects/2026-08-24-wolmido-disco-pangpang-accident-review/storyboard.json`: 5장면 퀵리빌과 제한적 줌, 결론 카드.
- `projects/2026-08-24-wolmido-disco-pangpang-accident-review/rights-manifest.json`: 사진 원본, 라이선스, 관련성, 사용 승인과 오인 방지 기록.
- `projects/2026-08-24-wolmido-disco-pangpang-accident-review/assets/images/`: 실제 월미도 사진과 동일 기종 자료사진.
- `projects/2026-08-24-wolmido-disco-pangpang-accident-review/publish.json`: YouTube 제목, 링크 없는 설명, 태그, 고정 댓글과 비공개 설정.
- `projects/2026-08-24-wolmido-disco-pangpang-accident-review/render-report.json`: Typecast 보이스, 실측 장면 길이, CTA와 편집 패키지 기록.
- `projects/2026-08-24-wolmido-disco-pangpang-accident-review/preview.mp4`: 720×1280 H.264/AAC 검토 영상.
- `projects/2026-08-24-wolmido-disco-pangpang-accident-review/thumbnail.jpg`: 권리 승인된 서로 다른 사진을 합성한 720×1280 썸네일.
- `projects/2026-08-24-wolmido-disco-pangpang-accident-review/edit-package/preview/`: 편집용 영상, SRT, 타임라인, 매니페스트와 사용 방법.

## 검증

- 설치본 `news2shorts 0.30.2` 초안 검증은 `ok: true`, 오류 0건, 경고 0건이다.
- 영상은 H.264 720×1280, AAC 음성, 총 27.611초다.
- Typecast 제공자는 `typecast`, 모델은 `ssfm-v30`, 자동 선택 보이스는 `Seohyeon`이다.
- 첫 화면, 결론 카드, CTA, 썸네일을 직접 확인해 글자 겹침, 이미지 잘림, 깨진 크레딧 문자가 없음을 확인했다.
- 장면 이미지 5개는 모두 서로 다른 파일이며 재사용하지 않았다.
- `upload-package` 출력은 제목 54/100자, 링크 없는 설명 417/5000자다.

## 남은 단계

- 사고 관련 민감 뉴스이므로 현재 결과는 `preview.mp4` 검토본이다.
- 사용자가 대본과 표현을 승인하면 편집·권리·합성 공개 상태를 확정하고 최종 `short.mp4`를 렌더한다.
