---
name: senior-shorts-producer
description: Resume, validate, or render an existing legacy Senior Shorts storytoon project inside Shorts Suite while preserving its native story, image, voice, subtitle, approval, and render contracts. Use when the user supplies an existing Senior project or explicitly requests the compatibility role. For every new 시니어 쇼츠 production use guided-shorts-producer instead. Do not copy source stories, auto-approve stages, upload, or access private accounts.
---

# 시니어 쇼츠 제작

이 스킬은 기존 Senior 프로젝트 호환 역할입니다. 신규 프로젝트라면 중단하고 `$guided-shorts-producer`를 사용합니다. 직접 `init`부터 시작하지 않습니다.

이 스킬은 Phase 1 창작 사연툰 전용입니다. 사용자가 제공한 주제는 사실 보도나 실화로 포장하지 않고 `fictionalized` 창작 사연으로 구성합니다. 건강, 금융, 연금, 복지, 세금, 정부 정책처럼 현재 사실 검증이 필요한 정보형 요청은 이 스킬로 제작하지 말고 출처 조사 범위와 별도 지원 여부를 사용자에게 알립니다.

## 시작 원칙

- 주제가 있으면 콘텐츠 유형은 `fictional_storytoon`, 타깃은 `55-75`, 길이는 55초를 기본값으로 사용합니다. 결과를 크게 바꾸는 정보가 없으면 반복 질문하지 않습니다.
- 주제가 없으면 YouTube 공개 메타데이터를 소재 신호로 수집하고 서로 다른 창작 후보를 정확히 3개 제시한 뒤 사용자 선택을 기다립니다. 자동 선택하지 않습니다.
- 공개 영상 제목·조회수·길이·게시 시각은 수요 신호일 뿐입니다. 영상, 썸네일, 댓글, 대사, 사건 순서, 반전과 결말을 가져오지 않습니다.
- 로컬 상태는 현재 실행 중인 프로세스를 기준으로 확인합니다. ComfyUI가 실행 중이지 않으면 임의로 시작하지 않습니다.
- 처음부터 LTX-Video, LoRA, IP-Adapter, BGM/SFX 자동화, 배치 생산을 추가하지 않습니다.
- `story.json`은 5개 훅과 정확히 8개 장면을 가진 구조화 JSON으로 작성합니다. 자유 형식 원고만 만들지 않습니다.
- 대본 승인 전 이미지 생성, 캐릭터 승인과 합성 고지 승인 전 TTS, 검토본 승인 전 최종 렌더를 진행하지 않습니다.
- 실제 YouTube, TikTok, Instagram 업로드를 수행하지 않습니다.

## 필수 참고 자료

소재가 없으면 [discovery-contract.md](references/discovery-contract.md)를 읽습니다. 프로젝트를 만들기 전에 [story-contract.md](references/story-contract.md)를 읽습니다. 이미지·음성·렌더 단계 전에 [output-contract.md](references/output-contract.md)를 읽습니다.

## 소재 발굴 흐름

1. 현재 API 키 상태를 확인합니다. API 키 값은 대화에 요청하거나 출력하지 않습니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior doctor --check-youtube --json

2. 키가 실제로 없을 때만 사용자가 자신의 터미널에서 숨김 입력 설정을 한 번 실행하도록 안내합니다. Codex 샌드박스에서 키체인 조회가 제한된 경우에는 미설정으로 단정하지 않습니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior configure-youtube

3. YouTube 공개 영상 메타데이터에서 최근 소재 신호를 수집합니다. 기본값은 90일, 검색어 3개, 검색어당 10개이며 추가 페이지를 자동 호출하지 않습니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior discover

4. `youtube-signals.json`을 읽어 반복되는 고민과 갈등 유형을 묶습니다. 영상 하나를 사연 하나로 변환하지 않습니다. `templates/story-candidates.template.json` 형식으로 서로 다른 창작 후보를 정확히 3개 작성합니다.

5. 세 후보의 제목, 한 줄 이야기, 시니어 고민, 갈등, 반전 방향, 8컷 적합성, 차별화, 신호 ID, 민감도, 점수를 보여주고 멈춥니다. 사용자가 ID를 선택한 뒤에만 기록합니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior select \
         --candidates <story-candidates.json> \
         --candidate-id <selected-id>

6. 선택 기록으로 프로젝트를 초기화한 뒤 아래 제작 흐름을 계속합니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior init \
         --selection <selection.json> \
         --target-age 55-75 \
         --duration 55 \
         --project-dir <project-dir>

## 제작 흐름

1. 플러그인 환경을 확인합니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior doctor

2. 사용자가 주제를 직접 제공했다면 프로젝트를 초기화합니다. 소재 발굴을 거쳤다면 위의 `--selection` 경로를 사용합니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior init \
         --topic "<topic>" \
         --target-age 55-75 \
         --duration 55 \
         --project-dir <project-dir>

3. 생성된 `story.json`을 작성합니다.
   - 훅 후보를 정확히 5개 만들고 `curiosity`, `emotion`, `conflict`, `clarity`, `spoiler_control`을 각각 0~20점으로 평가합니다.
   - 합계가 가장 높은 훅을 `selected_hook_id`로 선택합니다. 동점이면 호기심, 갈등, 명료성 순으로 비교합니다.
   - 장면 역할은 `hook`, `character_intro`, `incident`, `conflict`, `escalation`, `pre_reveal`, `reveal`, `afterglow` 순서를 유지합니다.
   - 등장인물의 연령, 얼굴, 머리, 의상, 성격을 고정하고 각 장면 `characters`와 `visual_prompt`에 필요한 인물만 연결합니다.
   - 자막은 1~2줄, 한 줄 16자 이하로 작성하고 장면당 핵심어를 최대 2개 지정합니다.
   - Phase 1의 `video_mode`는 `static` 또는 `ken_burns`만 사용합니다. `ltx_video`를 넣지 않습니다.

4. 정적 계약을 검사합니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior validate --project-dir <project-dir>

5. 선택된 훅, 8장면 요약, 등장인물, 창작 사연 표시 방식을 사용자에게 보여주고 대본 승인을 기다립니다. 승인 후 기록합니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior approve --project-dir <project-dir> --script

6. 캐릭터 정의와 스타일 프리셋이 결합된 이미지 프롬프트를 만듭니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior image-prompts --project-dir <project-dir>

7. 실행 중인 ComfyUI와 API workflow가 확인되면 첫 장면만 생성합니다. 사용자가 다른 이미지 생성 수단을 승인했다면 같은 결과 경로 `images/scene01.png`를 사용합니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior comfyui \
         --project-dir <project-dir> \
         --workflow <api-workflow.json> \
         --prompt-node <node-id> \
         --output-node <node-id> \
         --scene 1

8. 첫 이미지의 얼굴, 연령, 머리, 의상, 한국 배경, 자막용 여백을 보여주고 캐릭터 승인을 기다립니다. 승인 후 나머지 장면을 생성합니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior approve --project-dir <project-dir> --character
       python3 -B <plugin-root>/scripts/shorts_suite.py senior comfyui <same-options> --all

9. 최종 설명에 `AI로 제작한 창작 사연입니다.`와 동등한 합성·창작 고지를 넣는 방식을 사용자에게 확인하고 승인 상태를 기록합니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior approve --project-dir <project-dir> --synthetic-disclosure

10. 장면별 음성을 생성하거나 사용자가 승인한 장면별 음성을 가져옵니다. macOS TTS는 로컬 검토 기본 경로이며 Typecast, OpenAI, ElevenLabs를 임의 호출하지 않습니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior voice --project-dir <project-dir> --provider macos

    장면별 파일을 받았으면 `scene01`부터 `scene08`까지 같은 이름을 사용합니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior voice \
         --project-dir <project-dir> \
         --provider files \
         --source-dir <audio-dir>

11. 실제 음성 길이에 맞춘 JSON/ASS 자막을 만들고 렌더 준비 상태를 검사합니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior subtitle --project-dir <project-dir>
       python3 -B <plugin-root>/scripts/shorts_suite.py senior validate --project-dir <project-dir> --render-ready

12. 검토본을 렌더합니다. 기존 출력은 `--overwrite` 없이 덮어쓰지 않습니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior render --project-dir <project-dir> --draft

13. 대표 프레임과 전체 재생을 확인합니다. 9:16, 얼굴·의상 일관성, 손·텍스트 오류, 자막 2줄, 음성 누락, 화면 끝 검정 프레임, 장면 리듬을 검토합니다. 검토 승인 후에만 최종본을 만듭니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior approve --project-dir <project-dir> --draft-review
       python3 -B <plugin-root>/scripts/shorts_suite.py senior validate --project-dir <project-dir> --publish-ready
       python3 -B <plugin-root>/scripts/shorts_suite.py senior render --project-dir <project-dir> --final
       python3 -B <plugin-root>/scripts/shorts_suite.py senior validate --project-dir <project-dir> --final

## 결과 경계

- `final/review.mp4`는 로컬 검토본이며 게시 승인을 뜻하지 않습니다.
- `final/final.mp4`는 사용자 승인과 로컬 미디어 검사를 통과한 파일입니다. 플랫폼 업로드, 저작권 판정, 수익화 적합성을 증명하지 않습니다.
- 지속 가능한 수정 위치는 `story.json`입니다. 대본이나 자막을 바꾼 뒤 음성·자막·렌더를 다시 수행합니다.
- 상태는 `project.json`과 `status` 명령으로 확인합니다.

       python3 -B <plugin-root>/scripts/shorts_suite.py senior status --project-dir <project-dir>
