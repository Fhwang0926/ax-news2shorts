# healing2shorts 플러그인 구현 완료

## 완료 범위

- 음식 조리 영상 위에 생활·감동 기사 또는 익명 사연을 전달하는 저장소 플러그인 `healing2shorts`를 추가했다.
- 스토리 후보와 음식 영상 후보를 각각 최대 3개 제시하고 사용자 선택을 기다리는 Skill 흐름을 정의했다.
- 스토리 후보를 훅·감정선·반전/회수·음식 영상 적합성·근거/안전성의 100점 기준으로 비교하고 최고점 후보 하나를 `BEST`로 표시한다.
- 기사형의 원 출처·독립 출처·claim 연결과 익명 사연형의 기원·동의·비식별화·재구성 표시를 분리했다.
- Typecast Daeun 기본 내레이션, 2줄 이내 큰 자막, 자체 생성 저강도 앰비언트, 720x1280 FFmpeg 렌더를 구현했다.
- 접촉시트, 9:16 크롭 프리뷰, 검토·최종 MP4, 장면 클립, 오디오, SRT, CapCut/Vrew 편집 매니페스트, 업로드 문구 초안을 생성한다.
- `owned`, `licensed`, `permission_confirmed`, `negotiation_pending`, `not_permitted` 권리 상태와 민감 주제 검토 게이트를 구현했다.
- 도우인 자동 다운로드, 로그인·쿠키·CAPTCHA·지역·DRM 우회, 원본 워터마크 제거, 실제 업로드는 포함하지 않았다.
- 잘못 등록된 이전 플러그인과 설치 캐시를 제거하고 `healing2shorts@news2shorts-local`로 교체했다.

## 변경 파일

- `.agents/plugins/marketplace.json`: `healing2shorts` 로컬 마켓플레이스 항목을 마지막에 등록했다.
- `plugins/healing2shorts/.codex-plugin/plugin.json`: 플러그인 manifest와 `힐링쇼츠` UI 정보를 추가했다.
- `plugins/healing2shorts/skills/healing2shorts/SKILL.md`: 후보 선택, 기사·사연 라우팅, 검토 렌더, 권리 승인, 최종 검증 흐름을 정의했다.
- `plugins/healing2shorts/skills/healing2shorts/agents/openai.yaml`: Skill 표시명과 기본 호출 문구를 추가했다.
- `plugins/healing2shorts/skills/healing2shorts/references/`: 후보, 편집·권리, 프로젝트 출력 계약을 추가했다.
- `plugins/healing2shorts/skills/healing2shorts/templates/`: 스토리·영상 후보 JSON 템플릿을 추가했다.
- `plugins/healing2shorts/scripts/healing2shorts.py`: `doctor`, `init`, `preview`, `record-rights`, `validate`, `render`, `upload-package` CLI를 구현했다.
- `plugins/healing2shorts/tests/fixtures/`: 기사형·익명 사연형·영상 후보와 권리 증빙용 합성 fixture를 추가했다.
- `plugins/healing2shorts/README.md`: 범위, 제한, 빠른 시작과 결과 경계를 문서화했다.

## 이름 교체 검증

- 이전 소스 경로와 설치 캐시가 남지 않은 것을 확인했다.
- `healing2shorts@news2shorts-local`의 installed·enabled 상태와 소스·설치 캐시 해시 일치를 확인했다.
- 플러그인 폴더명, manifest 이름, Skill 폴더명·frontmatter, 기본 호출 문구, CLI 파일명, 마켓플레이스 이름·경로가 모두 `healing2shorts`로 일치한다.

## 스토리 BEST 표시 업데이트

- 설치 버전을 `0.1.0+codex.20260824080520`으로 갱신했다.
- 후보 JSON에 `best_candidate_id`, `best_candidate_reason`, 후보별 `story_score`를 추가했다.
- CLI가 다섯 점수 항목의 0~20 범위, 100점 합계, 최고점 후보와 BEST ID 일치를 검사한다.
- BEST는 자동 선택이 아니며 사용자가 다른 후보를 선택해도 프로젝트를 만들 수 있다.
- `story-source.json`에 선택 후보의 점수와 BEST 선택 여부를 보존한다.

## 검증 결과

- Plugin validator: 통과
- Skill quick validator: 통과
- marketplace·manifest·template JSON 검사: 통과
- CLI `--help`, `doctor --json`: 통과
- 기사형과 익명 사연형 `init`, review-ready 검증: 통과
- 접촉시트와 9:16 크롭 프리뷰 생성: 통과
- `negotiation_pending`: 36.021초 검토 MP4와 편집 패키지 생성, 업로드 패키지 `publish_blocked=true` 확인
- `not_permitted`: 검토 준비 검증 단계에서 차단 확인
- `permission_confirmed`와 권리 증빙·검토 승인: publish-ready 검증 통과
- 민감 주제 `medical`과 미완료 검토: publish-ready 단계에서 차단 확인
- 최종 fixture MP4: 37.621초, 720x1280, 30fps, H.264/AAC 확인
- 최종 프레임 시각 확인: 자막 안전 영역과 비검은 종료 화면 확인
- CapCut/Vrew 패키지: 장면 클립 6개, 오디오 6개, SRT, 메타데이터, edit-manifest 생성 확인
- 저장소 원본과 설치 캐시의 manifest, Skill, CLI SHA-256 일치 확인

## 증명 경계

- 합성 fixture의 검토·최종 렌더와 권리 상태 로직은 확인했다.
- 현재 Codex 샌드박스에서는 macOS 키체인 접근이 제한되어 실제 Typecast API 음성 생성은 확인하지 못했다. `doctor`는 설정 명령을 안내했고 로컬 TTS로 자동 대체하지 않는 실패 경로를 확인했다.
- 합성 fixture의 출처와 권리 증빙은 테스트 전용이며 실제 기사 사실이나 도우인 영상 사용 권리를 증명하지 않는다.
- 플러그인 설치·렌더 성공은 게시 권리, 플랫폼 승인, 수익화 적합성을 증명하지 않는다.
- 프론트엔드 빌드는 수행하지 않았다.

## 권리 확인 원본 가져오기·무중문 영상 업데이트

- 설치 버전을 `0.2.0+codex.20260824123751`로 갱신했다.
- `init`에 `--authorized-source-url`과 `--confirm-download-rights`를 추가했다. `owned`, `licensed`, `permission_confirmed` 후보만 제작자·라이선스 제공처가 준 HTTPS 직접 영상 URL에서 최대 512MB까지 자동으로 가져온다.
- 도우인 페이지·CDN, HTTP, 사용자 정보 포함 URL, 로컬·사설 네트워크 주소와 안전하지 않은 리다이렉트는 자동 가져오기에서 차단한다. 쿼리 문자열은 프로젝트 기록에 남기지 않는다.
- 영상 후보에 `visual_text_status`, `text_free_segments`, `visual_text_review_note`를 추가하고 화면 중국어가 없는 후보를 우선하도록 Skill과 후보 계약을 갱신했다.
- `chinese_present` 후보는 서로 다른 중국어 없는 구간 6개 이상이 있어야 프로젝트에 연결할 수 있다. 장면별 `source_text_status=chinese_present`는 검토·최종 검증 모두 실패하고, `unknown`은 검토 경고·게시 준비 오류가 된다.
- 중국어와 워터마크를 삭제·블러·가림 처리하지 않고 해당 구간을 타임라인에서 제외하도록 했다. 저작권과 게시 권리 검증은 기존대로 유지했다.

### 변경 파일

- `plugins/healing2shorts/.codex-plugin/plugin.json`: 버전과 기능 설명을 갱신했다.
- `plugins/healing2shorts/scripts/healing2shorts.py`: 권리 확인 HTTPS 직접 원본 가져오기, 안전한 URL·용량 검사, 원본 문자 상태와 구간 검증을 추가했다.
- `plugins/healing2shorts/skills/healing2shorts/SKILL.md`: 무중문 후보 우선, 권리 확인 자동 가져오기와 구간 제외 흐름을 추가했다.
- `plugins/healing2shorts/skills/healing2shorts/references/`: 후보·권리·출력 계약에 원본 문자 상태와 자동 가져오기 경계를 기록했다.
- `plugins/healing2shorts/skills/healing2shorts/templates/video-candidates.template.json`: 무중문 후보 우선순위를 추가했다.
- `plugins/healing2shorts/skills/healing2shorts/agents/openai.yaml`: 기본 호출 문구에 무중문 후보 우선과 권리 확인 원본 입력을 반영했다.
- `plugins/healing2shorts/tests/fixtures/video-candidates.json`: 원본 문자 상태 fixture를 추가했다.
- `plugins/healing2shorts/tests/test_healing2shorts.py`: 도우인·비HTTPS·사설 주소 차단과 중국어 없는 구간 검사를 추가했다.
- `plugins/healing2shorts/README.md`: 새 입력 방식과 제한을 문서화했다.

### 검증 결과

- Plugin validator와 Skill quick validator 원본·설치본: 통과
- Python 구문 검사, JSON 검사, `git diff --check`: 통과
- 표준 라이브러리 단위 테스트 4개: 통과
- 합성 720x1280 음식 영상의 로컬 `init`과 review-ready 검증: 통과
- `negotiation_pending` 후보의 직접 URL 자동 가져오기: 권리 상태 검사에서 차단 확인
- `chinese_present` 장면 6개의 review-ready 검증: 차단 확인
- 설치본 `healing2shorts@news2shorts-local 0.2.0+codex.20260824123751`: installed, enabled 확인
- 원본과 설치 캐시의 manifest, Skill, CLI SHA-256: 일치

### 확인하지 않은 범위

- 실제 제작자·라이선스 제공처의 권리 확인 HTTPS 원본 URL이 제공되지 않아 외부 다운로드 성공 경로는 실행하지 않았다. URL 정책과 실패 경로만 검증했다.
- Typecast 키는 현재 실행에서 확인되지 않아 실제 음성 렌더를 수행하지 않았다.
- 프론트엔드 빌드는 수행하지 않았다.
