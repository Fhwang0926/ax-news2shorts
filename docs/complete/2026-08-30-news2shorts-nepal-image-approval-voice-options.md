# 2026-08-30 news2shorts 네팔 이미지 승인 및 음성 옵션 준비

## 작업 범위

- 사용자의 `다음` 응답을 실제 네팔 사고·수색 영상 중심 이미지 구성 v2의 승인으로 기록했다.
- 승인된 접촉시트의 SHA-256이 현재 파일과 일치하는지 확인했다.
- 음성은 생성하지 않고, 현재 선택 가능한 Typecast 및 macOS 한국어 음성과 무음 검토 옵션만 정리했다.

## 변경 파일

- `projects/2026-08-29-nepal-ebs-warning-quick-reveal/project.json`: 이미지 승인 기록과 음성 옵션 준비 상태를 추가했다.
- `projects/2026-08-29-nepal-ebs-warning-quick-reveal/voice-options.json`: 제공자, 화자, 속도, 비용, 사용 조건, 권리 영향, 실패 동작과 추천 여부를 기록했다.

## 확인 결과

- 이미지 승인 해시는 `e83b80caf142a12eb5621cb7358596f4a4677088c07d0430f9cb2131b77c35ed`로 현재 파일과 일치한다.
- Typecast 키체인 확인은 현재 Codex 실행에서 제한되어 키가 없다고 단정하지 않았다.
- Typecast 5개 후보와 현재 Mac에 설치된 한국어 음성 9개를 모두 선택지로 기록했다.
- 선택한 제공자가 실패해도 다른 음성으로 자동 대체하지 않도록 옵션 계약에 명시했다.
- 실제 음성 생성, 렌더링, 업로드는 수행하지 않았다.

## macOS Yuna 음성 결과

- 사용자가 `macos-yuna`를 선택해 Yuna, rate 220으로 연속 내레이션을 생성했다.
- 본문은 25.123초, CTA 화면 구간을 포함한 전체 청취 파일은 27.123초다.
- 기존 CTA 문장은 실제 음성이 v16의 2초 제한을 약 0.04초 넘겨, 의미를 유지한 `다음 소식도 전해드릴게요.`로 최소 축약했다.
- `audio/voice-review-yuna.wav`, `audio/narration-yuna.wav`, `audio/cta-yuna.wav`, `voice-review-yuna.json`, `captions-yuna.srt`를 생성했다.
- 첫 답변과 사실 제한은 3.17초에 시작해 필수 마감 시간을 통과했다. 첫 훅은 3.17초로 2.5초 편집 권장치보다 길어 청취 승인 때 함께 검토한다.
- JSON 문법, news2shorts 초안 검증, 오디오 형식·길이·음량, 파일 해시와 `git diff --check`를 확인했다. 검증 오류는 0건이며 남은 경고는 시각 자산 권리와 이후 렌더·업로드 단계 항목이다.
- 사용자가 실제 음성을 승인하기 전에는 렌더링 단계로 진행하지 않는다.

## Typecast Kangil 음성 재선택

- 사용자가 이전 Yuna 결과 대신 `typecast-kangil` 몰입형 다큐 음성을 선택했다.
- 키 값은 노출하지 않고 macOS 키체인에서 읽었으며, Typecast 연결과 Voice ID를 확인했다.
- Kangil, `ssfm-v30`, tempo 1.05로 본문 23.640초와 CTA 포함 전체 25.640초 음성을 생성했다.
- 첫 직접 답변과 사실 제한은 2.964초에 시작하고 결론 장면은 6.092초로 필수 타이밍 제한을 통과했다.
- `audio/voice-review-kangil.wav`, `audio/narration-kangil.wav`, `audio/cta-kangil.wav`, `voice-review-kangil.json`, `captions-kangil.srt`를 생성했다.
- 이전 Yuna 음성·타이밍·자막은 삭제하지 않고 비교 가능한 이전 결과로 보존했다.

## Kangil 음성 승인 및 렌더 옵션

- 사용자가 SHA-256 `1083e1a72160aad6d1c9fab3f09b4e88f1815c41583e990d2e23dbe8acdd638f`인 Kangil 전체 음성을 승인했다.
- `render-options.json`에 현재 실제 지원되는 렌더러, 모션, 타이밍, 자막, 음악, 검토 출력과 차단된 최종 출력을 기록했다.
- continuous-flow v16은 하드 컷, 음악 없음, 720×1280 출력을 고정 지원한다.
- 실제 선택 가능한 화면 움직임은 사진 정지 또는 Imja Lake 사진 한 장의 완만한 확대 두 가지다.
- 사용자가 렌더 조합을 선택하기 전에는 검토 MP4를 생성하지 않는다.

## 로컬 렌더 조합 선택

- 사용자가 1번 `원본 영상 움직임 + Imja Lake 사진 정지`를 선택했다.
- 렌더 조합은 quick-reveal standard, 승인 Kangil 타이밍, 하드 컷, 고정 헤드라인·2줄 자막·출처, 음악 없음, 720×1280 로컬 검토본으로 고정했다.
- `tools/render_with_approved_kangil.py`는 Typecast를 다시 호출하지 않고 승인된 본문·CTA WAV의 SHA-256을 확인해 렌더러에 공급한다.
- 권리 승인 이미지가 두 장 미만이므로 별도 썸네일은 이번 로컬 검토 렌더에서 차단 상태로 기록한다.

## 로컬 검토 렌더 결과

- 승인된 Kangil 본문·CTA WAV의 SHA-256을 확인한 뒤 Typecast를 다시 호출하지 않고 `outputs/local-review.mp4`를 생성했다.
- 결과는 720×1280, H.264/AAC, 30fps, 25.667초이며 SHA-256은 `540da678718c8164aa243038510f64f9a46ef54bf6ac5d2d7629978423983187`이다.
- 네 개 대표 프레임과 `outputs/review-frames/contact-sheet.png`를 만들고 화면 구성을 확인했다.
- 검은 화면 0구간, 0.5초 이상 무음 0구간, 검증 오류 0건이다.
- 결론 장면은 6.092초로 6.0초 권장치보다 0.092초 길지만 7.0초 최종 제한 안에 있다.
- CapCut/Vrew 호환 결과는 `edit-package/local-review/`에 생성했다.
- 실제 영상 권리와 썸네일 자산이 해결되지 않아 깨끗한 최종본은 계속 차단한다.

## 로컬 검토 영상 승인

- 사용자가 SHA-256 `540da678718c8164aa243038510f64f9a46ef54bf6ac5d2d7629978423983187`인 로컬 검토 영상의 편집 결과를 승인했다.
- 이 승인은 편집·음성·자막 결과에만 적용하며 ABC·Euronews·SBS 영상 사용 허가로 해석하지 않는다.
- editorial review와 Typecast 합성 음성 고지 확인은 완료로 기록하고 rights review는 미완료로 유지했다.
- 권리 승인 영상, 썸네일 정지 이미지, 완성된 업로드 정보가 없으므로 깨끗한 최종 MP4 생성과 업로드는 수행하지 않았다.

## YouTube 업로드 정보 및 미작성 금지 규칙

- 2026년 8월 30일 오전 최신 수색 상태를 연합뉴스 보도로 다시 확인하고 `source-09`와 `claim-06`에 반영했다.
- `publish.json`에 질문형 제목, 링크·해시태그 없는 설명, 태그 7개, 출처 문구 5개, 사실 우선 고정 댓글과 모든 업로드 결정을 작성했다.
- Typecast 합성 음성은 내부 `contains_synthetic_media=true`로 기록하고, 실제 사건을 변형하거나 가짜 장면을 만든 영상이 아니므로 YouTube 변경·합성 콘텐츠 공개 선택은 `no`로 정리했다.
- 피해자·시신 노출이 없는 현재 검토 영상 기준 연령 제한은 `none`, 시청자층은 아동용 아님, 공개 상태는 비공개로 기록했다.
- 권리 승인 정지 이미지가 두 장 미만이므로 썸네일 파일은 만들지 않고 `thumbnail_status=blocked_rights`와 필요한 입력을 명시했다.
- `outputs/youtube-upload-info.md`를 생성했으며 SHA-256은 `1ef22e71cf2e52b2e5bef9a8e6594d5fb11d8fa306f4437674d9d7b7b3f9adcf`다.
- news2shorts formatter가 필수 문구나 업로드 결정을 임의로 `미작성` 또는 `검토 필요`로 출력하지 않고 오류로 중단하도록 수정했다.
- Skill, 업로드 패키지 참고문서, 출력 계약과 README에 동일한 지침을 반영했다.
- 플러그인 버전을 `0.36.5+codex.20260830014852`로 갱신하고 `news2shorts-local`에서 재설치했다.
- 소스와 설치 캐시의 CLI, Skill, 업로드 지침 SHA-256이 각각 일치했다.
- 소스와 설치 캐시 양쪽에서 Plugin validator와 Skill validator를 통과했고, Python 문법, JSON 파싱, CLI 도움말, 완성 업로드 formatter, 불완전 입력 거부, 마켓 등록, `git diff --check`를 확인했다.
- 최종 검증에는 업로드 문구 미작성 오류가 남지 않았으며, 방송사 영상 권리와 별도 썸네일 권리 자산만 최종 차단 사유로 유지된다.
- 사용자 지침에 따라 단위 테스트와 프론트엔드 빌드는 실행하지 않았다.

## 업로드 태그 자동 해시태그

- 복사용 전체 태그 목록에도 모든 항목 앞에 `#`을 자동으로 붙이도록 formatter를 수정했다.
- 저장값에 이미 `#`이 있어도 먼저 제거한 뒤 정확히 한 번만 붙여 `##` 중복을 방지한다.
- 현재 프로젝트의 태그는 `#네팔홍수, #빙하붕괴, #한국인실종, #EBS, #라수와, #재난뉴스, #뉴스한면`으로 갱신했다.
- `outputs/youtube-upload-info.md`의 새 SHA-256은 `9659d73c72e0a0e66f09f6d397a8ccb2010900872d99e330983c55a2d6d9b228`다.
- 플러그인 버전을 `0.36.5+codex.20260830015743`으로 갱신하고 재설치했다.
- 소스와 설치 캐시의 CLI, Skill, 업로드 지침 SHA-256이 일치하고 양쪽 Plugin·Skill validator를 통과했다.
