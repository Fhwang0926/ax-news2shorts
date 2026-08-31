---
name: careerfill-review
description: Review a CareerFill draft for text and visual source coverage, screenshot-DOM consistency, claim verification, limits, repeated examples, sensitive fields, and tab identity. Do not write to the browser or submit.
---

# CareerFill Review

Audit one stored application preview and explain every blocker.

Read [the application contract](../../references/application-contract.md), [the vault contract](../../references/vault-contract.md), [the Notion contract](../../references/notion-contract.md), and [the security boundary](../../references/security.md).

## Workflow

1. Require the exact CareerFill application session ID.
2. Call `get_application_session` and confirm company, role, URL, page fingerprint, field count, visual observation count, and no-write flags.
3. Call `review_application_draft`.
4. For every narrative answer, inspect the exact Claim statements and local or Notion SourceSpan locations. Reject unverified, missing, stale, or unrelated Claims.
5. Recalculate character or UTF-8 byte lengths using the field unit. Flag missing required fields and unsafe near-limit answers.
6. Check visual observations against DOM facts. Flag unresolved visual blockers, low-confidence visual-only conclusions, and screenshot/DOM conflicts affecting required state, limits, progress, errors, or upload status.
7. Flag Claim reuse across answers, unsupported statements, mixed company/role references, and manual sensitive or legal fields.
8. For Notion evidence, confirm the registered source URL, block ID, and snapshot hash. A live page that changed after capture requires a refreshed snapshot and renewed Claim review.
9. Report Evidence only as candidates with sensitivity and verification state. A Notion block, visual observation, or rendered page never proves attachment suitability by itself. Do not attach files.
10. Return `passed` only when the review tool has no issues and the human-readable review finds no additional blocker. Even then, state that Notion writing, browser writing, attachment, and submission remain disabled.

Call `review_claim` only when the user explicitly asks to update the status of an exact Claim after seeing its statement and source.
