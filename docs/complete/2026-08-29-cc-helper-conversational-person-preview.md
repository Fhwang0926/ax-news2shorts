# cc-helper 대화형 내레이션·인물 화면·CapCut 미리보기 개선

## 완료 내용

- 새 프로젝트에 `narration_flow_mode: conversational-chain`을 기본 적용했다.
- 각 narration beat가 `hook → setup → trigger → explanation → reaction → response → consequence → resolution → aftermath` 순서로 이어지는지 검증한다.
- 인접한 `~데/~는데` 종결과 마지막 두 beat의 `~함 → ~함` 반복을 오류로 처리한다. 모드가 없는 기존 프로젝트는 기존 동작을 유지한다.
- 새 프로젝트에 `person_visual_mode: stylize-or-remove`를 기본 적용했다.
- 표시 화면의 공개 인물은 검수된 실제 인물 자료에서 만든 `editorial-animation`만 허용하고, 기사·공식 페이지의 관련 없는 얼굴은 크롭 제거하며, 비공개 인물·직원은 비식별 대체 화면만 허용한다.
- 공개 인물 editorial-animation의 실제 parent로 검수된 `source_photo`, `official_evidence`, `source_capture`를 허용하되 합성 parent와 비공개 인물 parent는 계속 거부한다.
- `retime-capcut`이 승인된 WAV의 길이만 갱신하면서 기존 오디오 track/material/segment ID, 시작 0초, 볼륨 0dB를 보존한다.
- 1080×1920 정규화 장면의 위치·크롭·배율을 active root/template/mini draft에서 전체 화면 기준으로 초기화한다.
- 활성 timeline UUID의 prerender 캐시 한 폴더만 백업·무효화하고 실패 시 복구한다. sibling timeline 캐시는 건드리지 않는다.
- scene 1에서 active draft cover를 다시 만들고 기존 cover도 retime 백업에 포함한다.

## 박위 프로젝트 반영

- 내레이션을 배경 → KTX 영상 → 해명 → 반응 → 사과 → 취소·민원 → 사임 → 현재 상태 순으로 재작성했다.
- Typecast 다은 음성을 동일 모델·속도(`ssfm-v30`, `1.05`)로 다시 생성했다.
- 실제 WAV 44.952381초에 맞춰 CapCut 길이를 44.966666초(30fps 1349프레임)로 재타이밍했다.
- 15개 구조 슬롯과 14개 하단 자막을 유지하면서 9개 실제 화면만 사용해 전환을 8회로 줄였다.
- 박위·송지은 위촉식, 박위 설명·반응 장면을 동일한 editorial-animation 화풍으로 만들었다.
- KTX 장면은 직원과 당사자 특징을 재현하지 않은 비식별 재구성으로 교체했다.
- 사과문, 사임 기사, 서울시 공식 명단 화면은 관련 없는 얼굴을 제외한 실제 원문 크롭으로 교체했다.
- CapCut 초안과 활성 timeline prerender 캐시를 각각 백업한 뒤 재타이밍했다.
- CapCut UI에서 6초, 12초, 31초, 37초, 42초 지점을 확인해 새 이미지와 현재 자막이 player에 표시되는 것을 확인했다.

## 검증

- `python3 -B -m unittest discover -s plugins/cc-helper/tests -p 'test_*.py'`: 46건 통과
- `validate --stage assets`: 오류 0
- `validate --stage capcut`: 오류 0
- Typecast audio ID와 segment ID, 시작 0초, volume 1.0 유지
- active draft mirror, template, mini draft의 15 scene 경로·타이밍·full-frame geometry 일치
- CapCut UI total progress: 00:00:44:29
- 최종 렌더링·업로드·권리 승인은 수행하지 않았다.

## 주요 경로

- 프로젝트: `projects/cc-helper/2026-08-27/CCH-20260827-01-park-wi-seoul-ambassador`
- CapCut 초안: `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/cc-20260827-222857-park-wi-seoul-ambassador-resignation`
- retime 백업: `projects/cc-helper/2026-08-27/CCH-20260827-01-park-wi-seoul-ambassador/backups/capcut-retime-20260829-114539`
- 해당 단계 설치 버전: `cc-helper 0.1.2+codex.20260829040611`

## 최종 화면 깨짐 방지 추가 개선

- `full-frame reset`을 제거하고 read-only `news2shorts` base template의 장면별 segment·material geometry를 `capcut-map.json` snapshot으로 저장·복원하도록 변경했다.
- 같은 beat의 follower는 경로뿐 아니라 segment transform과 video material crop까지 leader와 동일하게 만든다.
- root draft, active template, mini draft에서 segment와 material geometry를 각각 검증한다.
- scene 14→15는 template 기준 `transform.y=-0.33322197475872306`, material crop `0.17637567934782608–0.8420006793478261`로 동일하게 복원했다.
- 새 `display_validation_mode: short-preview`에서 normalized foreground 비율과 PNG SHA를 기록한다.
- 일반 화면은 foreground 폭 55%·높이 28%·면적 22%, source-text 화면은 높이 35%·면적 30%를 최소 기준으로 검증한다.
- `compose-readable-source` 명령을 추가해 문서 원문 픽셀만 crop·확대하는 1000×720 가독성 카드를 만들 수 있게 했다.
- `review-asset`에 `display_focus`, 360×640 preview 확인, text evidence readability, anchor term 검수를 추가했다.
- `final_visual_review_mode: player-check`에서 실제 CapCut player beat midpoint screenshot과 visual timeline/storyboard/map 해시가 모두 일치해야 `validate --stage capcut`이 통과한다.
- player 검수는 흰색·노란색 제목, 하단 자막, 올바른 이미지, source-text 가독성, blank·clipping·overlap을 확인한다.

### 현재 박위 프로젝트 재적용

- scene 09: 실제 사과문 원문 확대 카드
- scene 10: 실제 강남문화재단 강연 취소 공지 확대 카드
- scene 11: 실제 서울신문 해촉 요구 민원 문단 확대 카드
- scene 12–13: 실제 자숙 사임·내부 절차 기사 확대 카드
- scene 14–15: 실제 서울시 명단 이름·공공누리·수정일 확대 카드
- 강연 취소와 해촉 민원을 서로 다른 narration beat와 화면으로 분리했으며 기존 Typecast WAV는 변경하지 않았다.
- 10개 narration beat midpoint를 실제 CapCut player에서 캡처해 두 제목 줄과 자막·화면을 확인했다.
- scene 14→15 경계 1프레임 전후를 확인해 이미지 이동·확대·검정 프레임이 없음을 확인했다.
- 최종 QC: `handoff/final-visual-qc.json`
- 새 retime 백업: `backups/capcut-retime-20260829-125733`
- 해당 단계 설치 버전: `cc-helper 0.1.2+codex.20260829040611`
- 단위 테스트 54건, skill/plugin validator, assets/capcut validator 모두 통과했다.

## 사람다운 외부 음성·인물 모션·눈가림 후속 개선

- 새 프로젝트 기본 계약에 `narration_performance_mode: reviewed-external`, `public_figure_style_mode: obvious-editorial-eye-band`, `person_motion_mode: subtle-deterministic`를 추가했다. 모드가 없는 기존 프로젝트는 기존 음성·화풍·정지 화면 동작을 유지한다.
- cc-helper 안에서 Typecast 음성을 생성하지 않는다. 외부에서 생성한 WAV, Typecast용 스크립트, timestamp 또는 CapCut waveform timing을 `handoff/narration-performance.json`의 경로·SHA-256으로 묶고, storyboard의 beat ID·내레이션 별도 해시까지 검증한다.
- 10개 narration beat 각각에 smart/preset 감정, tone-up/down 강약, 0.96–1.02 tempo, 0.18–0.28초 비트 사이 휴지를 배치했고 마지막 beat의 후행 휴지는 0초로 유지했다.
- 현재 WAV는 49.224195초, -16.27 LUFS, -1.49 dBTP이며 CapCut은 30fps 49.233333초에 맞췄다. 비트 경계 휴지는 WAV에서 -40 dB·0.08초 기준으로 다시 측정해 기록값과 0.04초 이내인지 확인한다. 스크립트·음원·timing·storyboard 내레이션 중 하나가 바뀌면 성능 검수를 stale로 처리한다.
- 현재 기록은 감정 프로필·timestamp·WAV 휴지·음량·피크에 대한 `automated_reviewed` 상태다. 사람 청취로만 판단할 수 있는 자연스러움, 강약, 호흡, 발음, 속도, 오디오 깨짐 여부는 게시 전 사용자 승인 경고로 남겼다.
- 실제 공개 인물 원본에서 만든 4개 화면을 Shorts 크기에서도 합성임이 분명한 editorial-animation으로 다시 만들고, 눈 영역에 가로 `editorial-ruler-eye-band`와 눈금을 넣었다. 신원·의상·사실 맥락은 parent 자료와 함께 보존한다.
- 눈가림 띠는 편집 모티프일 뿐 비식별 처리, 동의, 라이선스 또는 초상권 해결책이 아니다. 공개 인물은 계속 식별 가능한 상태로 기록하고 `rights_status: unreviewed`, `publish_blocked: true`, `local_review_only`를 유지한다.
- 느린 줌·좌우 이동은 storyboard에 실제로 선택된 `editorial_animation` 화면에만 SHA 기반으로 결정해 적용한다. 기사·공식문·KTX 비식별 화면은 정지 상태를 유지한다.
- scene 02→03과 scene 07→08처럼 한 beat가 두 슬롯으로 나뉜 경우, follower의 시작 scale/position을 leader의 종료값과 같게 만들어 자막 경계에서 모션이 다시 시작되거나 튀지 않게 했다.
- CapCut player 최종 검수 항목에 화풍의 명확성, 눈가림 띠와 눈금 표시, 모션 부드러움, 얼굴 안전 영역, 제목·하단 자막과의 충돌 방지를 추가했다. 4개 motion beat의 시작·끝과 scene 02→03, 07→08 경계 전후 한 프레임도 SHA-256 증거로 묶었다.
- 비활성 `template.json`은 CapCut 자체 저장 표현이 달라질 수 있으므로 root geometry와 동일성 비교하지 않고, 현재 `draft_info.json`·`template-2.tmp` 미러만 동일성 검사하도록 수정했다.
- 단위 테스트 65건과 assets/capcut 검증이 통과했다. 사람 청취와 권리 검토는 경고 상태로 유지한다.
- 플러그인·skill 검증과 소스/설치본 비교를 통과한 뒤 `cc-helper 0.1.2+codex.20260829121647`로 재설치했다.

## 유튜브 업로드 문구 인계 개선

- 새 프로젝트의 `project.json`에 `youtube_upload_mode: copy-handoff`와 `youtube_upload` 계약을 추가했다. 업로드 문구 수정이 storyboard 기반 시각 QC를 만료시키지 않도록 분리했다.
- 제목, 설명, 해시태그, 검색 태그, 고정댓글, 카테고리, 언어, 아동용 여부, 변형·합성 콘텐츠 표시, 권장 공개 범위, 썸네일 문구, 대표 출처를 검증한다.
- YouTube 공식 제한에 맞춰 제목은 100자, 설명은 5,000자 이하로 제한한다.
- `publish_blocked: true` 프로젝트는 `recommended_visibility: private`만 허용하고, 업로드 문구를 게시 승인으로 취급하지 않는다.
- 최종 인계에 `handoff/youtube-upload.json`과 복사 가능한 `handoff/youtube-upload.md`를 생성하고, 최종 응답에서도 전체 항목을 표시하도록 skill을 수정했다.
- 박위 프로젝트에 실제 업로드 문구를 채웠으며 대표 출처는 서울신문, 서울특별시, 한국일보로 연결했다.
- 단위 테스트 67건, skill/plugin validator, assets validator를 통과하고 `cc-helper 0.1.2+codex.20260829124258`로 재설치했다.
- 최신 retime 백업: `backups/capcut-retime-20260829-204417`
- 최종 렌더링·업로드·게시 권리 승인은 이번 범위에 포함하지 않았다.
