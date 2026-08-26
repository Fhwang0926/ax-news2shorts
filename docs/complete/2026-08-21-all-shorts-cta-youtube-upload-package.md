# 전체 Shorts 플러그인 CTA·YouTube 업로드 정보 반영

## 완료 일자

- 2026-08-21

## 반영 범위

- `news2shorts`의 결론 후 CTA와 YouTube 업로드 정보 제공 방식을 나머지 영상 제작 플러그인 6종에 공통 적용했다.
- 본문 결론이 끝난 뒤 1.8초 무음 구독·좋아요 CTA 샷을 정확히 한 번 붙인다.
- 기존 플러그인의 최대 길이 제한에는 CTA 길이도 포함하고, 기존 최소 본문 길이는 유지한다.
- 전체 렌더 뒤 `youtube-upload.json`과 `youtube-upload.md`를 생성한다.
- 업로드 정보에는 영상 경로, 제목·글자 수, 설명·글자 수, 태그, 썸네일 안내, 재생목록, 시청자층, 카테고리, 언어, 변경·합성 콘텐츠, 유료 프로모션, 연령 제한, 댓글, 공개 상태, 예약 시간, 고정 댓글을 포함한다.
- 시청자층·변경/합성 콘텐츠·유료 프로모션·연령 제한·미확정 권리는 `검토 필요`로 남기고 실제 YouTube 업로드는 수행하지 않는다.
- 기존 사용자가 수정한 제목·설명·태그·썸네일·고정 댓글·업로드 설정은 다음 렌더에서도 보존한다.
- `viral-shorts`의 영어판과 일본어판은 각 시장 언어 CTA와 별도 업로드 패키지를 생성한다.

## 변경 파일

- 각 플러그인의 주 렌더 스크립트
  - `plugins/animal-viral-shorts/scripts/animal_viral_shorts.py`
  - `plugins/motion2d-studio/scripts/motion2d_studio.py`
  - `plugins/tiktok2shorts/scripts/tiktok2shorts.py`
  - `plugins/story2short/scripts/story2short.py`
  - `plugins/whiteboard-shorts/scripts/whiteboard_shorts.py`
  - `plugins/viral-shorts/scripts/viral_shorts.py`
- 각 플러그인의 `scripts/youtube_delivery.py`
  - 공통 CTA 샷 연결, 업로드 JSON/Markdown 생성, 업로드 정보 출력 기능을 추가했다.
- 각 플러그인의 `SKILL.md`, `references/output-contract.md`, `agents/openai.yaml`
  - 렌더 후 CTA, `upload-package` 명령, 최종 응답의 업로드 정보 제공 규칙을 반영했다.
- 각 플러그인의 `.codex-plugin/plugin.json`, `README.md`
  - 기능 설명과 버전을 갱신했다.
- 루트 `README.md`
  - 전체 영상 제작 플러그인의 공통 CTA·업로드 준비 패키지 동작을 기록했다.

## 설치 버전

| 플러그인 | 버전 |
| --- | --- |
| animal-viral-shorts | `0.3.0+codex.20260821` |
| motion2d-studio | `0.2.0+codex.20260821` |
| tiktok2shorts | `0.4.0+codex.20260821` |
| story2short | `0.3.0+codex.20260821` |
| whiteboard-shorts | `0.6.0+codex.20260821` |
| viral-shorts | `0.6.0+codex.20260821` |

## 검증 결과

- 13개 Python 스크립트 AST 정적 파싱 성공
- 6개 플러그인 manifest JSON 파싱 성공
- 6개 Skill 구조 검사 성공
- 공통 `youtube_delivery.py` 6개 SHA-256 일치
- 6개 플러그인 설치·활성화와 새 버전 확인
- 각 주 렌더 스크립트와 공통 전달 모듈의 소스–설치 캐시 SHA-256 일치
- `git diff --check` 성공

## 수행하지 않은 작업

- 프로젝트 지침에 따라 실제 영상 렌더, 외부 YouTube 업로드, DB 작업, 프론트엔드 빌드·테스트는 수행하지 않았다.
- 실제 영상에서 CTA 화면·오디오 전환과 업로드 패키지 생성까지 확인하려면 플러그인별 기존 프로젝트로 렌더 검증이 필요하다.

## 실제 렌더 후속 보정

- `animal-viral-shorts` 대표 프로젝트로 CTA가 포함된 초안 렌더를 수행하던 중 공통 전달 모듈의 오디오 타임스탬프 필터에 영상용 `setpts`가 사용된 문제를 확인했다.
- 6개 플러그인의 `scripts/youtube_delivery.py`에서 오디오 필터를 `asetpts`로 수정했다.
- 수정 후 Animal Viral Shorts 초안은 17.6초, 720x1280, 30fps, H.264/AAC로 렌더됐고 결론 뒤 1.8초 무음 CTA 샷이 한 번 포함됐다.
- `youtube-upload.json`과 `youtube-upload.md`가 생성됐으며 실제 업로드는 수행하지 않았다.
- 6개 Python 파일의 AST, 6개 Skill 구조, `git diff --check`를 다시 확인했다.
- 6개 로컬 플러그인을 재설치했고 각 설치 캐시의 전달 모듈 SHA-256이 저장소 소스와 일치함을 확인했다.
- 이번 실제 렌더는 Animal Viral Shorts 1종의 대표 검증이며 나머지 5종의 개별 렌더 결과를 대신하지 않는다.
