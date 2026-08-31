---
name: shorts-suite
description: "Route every new Shorts Suite production through Guided Shorts, which requires user option selection and result approval at source, script, image, voice, and render stages. Also route legacy projects to their existing Whiteboard, Senior, Animal, Healing, Romance, Discovery, Packaging, or Global Reframe role without converting schemas. Use for broad Shorts Suite requests or when the correct role is unclear."
---

# Shorts Suite

For every new production project, use `$guided-shorts-producer`. It lists all currently selectable options with explanations, produces only the user's selection, and stops for result approval at each of the five stages.

Use the smallest direct role only for an existing legacy project or an explicitly requested compatibility operation. Read only that role's skill before acting.

- Current overseas source research and Korean Gap comparison: use `$shorts-discovery`.
- Selected Candidate ID deep research and renderer-neutral evidence, asset, script, and scene packaging: use `$shorts-research-packager`.
- TikTok or YouTube animal source research and local production: use `$animal-shorts-producer`.
- Anonymized or fictionalized healing dialogue over authorized food footage: use `$healing-shorts-producer`.
- Approved Korean two-person romance drama production: use `$romance-shorts-producer`.
- A Korean Shorts signal reframed into an independently sourced English production draft: use `$global-shorts-producer`.
- Existing Whiteboard animation projects: use `$whiteboard-shorts`.
- Existing Senior storytoon projects: use `$senior-shorts-producer`.

Do not route news production or native CapCut issue cloning here. Those remain in `news2shorts` and `cc-helper`.

## Shared boundaries

- Never auto-select a source or story when the selected role requires explicit user choice.
- For a new project, do not bypass Guided Shorts by invoking a direct role first.
- `$shorts-research-packager` may follow `$shorts-discovery` only after the user explicitly selects one Candidate ID; preserve the original shortlist as the handoff input.
- Keep source availability, factual proof, reuse rights, render proof, and publication approval separate.
- Preserve each role's existing project schema and approval names. Do not translate one role's rights vocabulary into another role's final permission.
- Existing legacy project folders may be read by compatibility checks, but new projects use the `shorts-suite` role identifiers and output roots.
- Do not run another role merely because its output could be useful later. Stop at the selected role's approval boundary.

The common command router is `python3 <plugin-root>/scripts/shorts_suite.py <role> ...`. Guided projects use the `guided` role; legacy Whiteboard and Senior projects use the `whiteboard` and `senior` roles.
