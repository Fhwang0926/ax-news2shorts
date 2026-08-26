# 연애 드라마 Shorts 플러그인 개발 완료

## 요청

- 최근 연애·웹드라마 숏폼을 YouTube Shorts·TikTok·Instagram Reels에서 미국·한국·일본별로 조사한다.
- 나라별 후보를 최대 10개씩 제시하고 대본 또는 요약 추출 상태를 함께 제공한다.
- 선택한 소재를 컷별로 구성하고 영상화한 뒤 YouTube 배포까지 연결한다.
- 제목은 `왜 ○○할까?`, `○○하는 사람의 심리`, `○○할 때 나타나는 신호 3가지` 중 하나로 일관되게 사용한다.

## 반영 내용

- `romance-drama-research`, `romance-cut-director`, `romance-video-producer`, `romance-youtube-publisher` 네 스킬을 하나의 플러그인으로 구성했다.
- 리서치는 30일을 우선 확인하고 부족한 국가만 90일까지 확장하며, 9개 국가·플랫폼 조합의 성공·차단·사용 불가 상태를 공개 화면 근거와 함께 요구한다.
- 후보 자동 선택을 금지하고 Candidate ID 선택에서 멈추도록 했다.
- 제3자 공개 자막은 내부 분석과 요약에 사용하되 전체 대본 재배포는 차단하고, 소유·라이선스·명시적 허가가 있는 경우만 원본 컷을 허용한다.
- 6~8장면, 성인 2인, CTA 포함 20~30초, 첫 훅·중간 이전 반전·40~60% 재훅·마지막 20% 결론 계약을 검증한다.
- 오리지널 AI 시네마틱 컷과 권리 승인 원본 타임스탬프 컷 두 제작 모드를 지원한다.
- 기존 Pillow, FFmpeg, Typecast 연결을 재사용해 720×1280 H.264/AAC 영상과 썸네일, 업로드 패키지를 만든다.
- YouTube Desktop OAuth는 업로드와 대상 채널 확인에 필요한 두 범위만 요청하고 토큰을 macOS 키체인에 저장한다.
- 최종 파일 해시, 대상 채널, 권리, 아동용 여부, 합성 콘텐츠 표시, 모든 승인을 확인한 뒤 `private`, 구독자 알림 없음으로 한 번만 업로드한다.
- 로컬 마켓플레이스 `news2shorts-local`에 새 플러그인 항목을 추가했다.
- `romance-drama-shorts 0.1.0+codex.20260824`를 Codex에 설치하고 활성 상태를 확인했다.

## 변경 파일

- `plugins/romance-drama-shorts/.codex-plugin/plugin.json`: 플러그인 매니페스트와 사용자 표시 정보.
- `plugins/romance-drama-shorts/skills/`: 리서치, 컷 디렉팅, 영상 제작, YouTube 비공개 배포 스킬.
- `plugins/romance-drama-shorts/references/`: 제목, 후보 입력, 프로젝트, 권리, OAuth 계약.
- `plugins/romance-drama-shorts/scripts/romance_drama_shorts.py`: 후보 정렬, 프로젝트 생성·승인·검증, 로컬 렌더, 업로드 게이트 CLI.
- `plugins/romance-drama-shorts/scripts/youtube_oauth.py`: PKCE OAuth, 키체인 저장, 채널 확인, 재개 가능 비공개 업로드와 썸네일 설정.
- `plugins/romance-drama-shorts/README.md`: 설치 후 사용 흐름과 제한 사항.
- `.agents/plugins/marketplace.json`: 로컬 마켓플레이스 등록.
- `README.md`: 저장소 플러그인 목록과 업로드 지원 범위 갱신.

## 검증

- Python 문법과 CLI 도움말, 로컬 의존성 진단을 확인했다.
- 세 제목 공식의 정상·비정상 입력, 후보 국가·플랫폼 계약, 사용자 선택 프로젝트 초기화와 승인 게이트를 점검했다.
- 합성 로컬 이미지·음성을 이용한 검토 MP4 렌더와 메타데이터 생성을 확인했다.
- 오디오가 포함된 합성 승인 원본을 이용해 타임스탬프 컷 모드도 21.82초 H.264/AAC 검토본으로 렌더했다.
- 네 Skill 구조, 플러그인 매니페스트, 마켓플레이스 JSON과 `git diff --check`를 검증했다.
- 설치 캐시와 저장소 원본의 핵심 파일 해시를 비교했다.

## 외부 확인 경계

- 실제 TikTok·Instagram·YouTube 후보 30개 조사는 플러그인 사용 시 브라우저 공개 화면으로 수행한다.
- 실제 Typecast 호출은 수행하지 않았고 로컬 검토 음성으로 렌더 동작을 확인했다.
- Google OAuth 동의와 실제 YouTube 비공개 업로드는 계정 권한과 최종 콘텐츠 승인이 필요한 외부 작업이므로 수행하지 않았다.
- 프론트엔드 빌드와 DB 작업은 대상이 아니며 실행하지 않았다.
