---
name: shorts-price-producer
description: Produce a Korean price-breakdown Short from user-provided menu, product, and quantity evidence with exact Decimal calculations. Use for approved production, not candidate research.
---

# Shorts Price Producer

사용자가 제공한 가격·용량·사용량 근거를 정확히 계산해 가격 카드형 쇼츠를 제작합니다.

## 필수 경계

- 가격 후보를 조사하거나 자동 선택하지 않습니다.
- 회원가, 쿠폰, 첫 구매, 적립금은 기본 계산에서 제외합니다.
- 피할 수 없는 배송비만 합산하고 소매 재료비를 식당의 실제 원가로 표현하지 않습니다.
- 웹 캡처는 권리와 가격 조건이 검토되기 전까지 `review_required`로 유지합니다.

## 실행

`python3 <plugin-root>/scripts/shorts_studio.py price ...`를 사용합니다. `init → assets 승인 → content 승인 → 검토 렌더 → publish 승인 → 최종 검증·렌더 → upload-package` 순서를 지킵니다.

내부 정확 합계와 100원 단위 화면 표시값을 모두 보존합니다. 실제 업로드와 제휴 링크는 만들지 않습니다.
