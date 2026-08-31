# Guided workflow contract

## Project topology

```text
project/
├── workflow.json
├── options/
├── results/
├── revisions/
├── role-project/
└── final/
```

The role-native project stays under `role-project/`. `workflow.json` coordinates approval without converting or flattening the native schema.

## Stage status

```text
pending
options_ready
selected
result_ready
approved
revision_required
invalidated
```

Only the immediately previous `approved` stage unlocks the next stage. Option regeneration, selection changes, or a new result archive the previous workflow snapshot and invalidate all downstream stages. Existing artifacts remain on disk.

## Option registry

Every option group is required and single-select. Each selectable option includes:

- `id`, `label`, `description`
- `best_for`, `tradeoffs`
- `required_inputs`
- `estimated_time`, `external_cost`
- `rights_impact`
- `recommended`
- role-specific metadata

`recommended` is explanatory only. Unavailable entries stay outside selectable groups and include a reason.

## Result and approval

`guided produce` accepts only existing files inside the guided project. It records their relative paths, SHA-256 and size plus role, rights, synthetic state and note. The stage result digest includes the selected option digest and all artifact hashes.

`guided approve` requires the exact current result digest. `revise` returns the stage to `revision_required`. Synthetic image approval requires `--confirm-synthetic-disclosure`.

## Rights and finalization

Clean finalization accepts these source rights:

```text
owned
licensed
permission_confirmed
public_domain
official_press_asset
```

`unknown`, `unreviewed`, `review_required`, `transformative_review` and `not_permitted` remain blocked. User approval confirms fit, not rights. `guided finalize` also requires `--confirm-clean-render`, records codec, dimensions, duration, audio presence and final SHA-256, and never uploads.

## Legacy compatibility

Existing Whiteboard and Senior projects remain unchanged. Route them through:

```text
python3 <plugin-root>/scripts/shorts_suite.py whiteboard ...
python3 <plugin-root>/scripts/shorts_suite.py senior ...
```

Do not create `workflow.json` inside a non-empty legacy project.
