# Scene rights policy

Record the actual state without upgrading it by inference:

- `owned`: the operator owns the source or asset.
- `licensed`: a recorded licence covers the planned use.
- `permission_confirmed`: the rightsholder gave recorded permission.
- `review_required`: a human must verify the rights.
- `unknown`: no reliable permission conclusion exists.
- `not_permitted`: do not preview or render the asset.

A local file, public URL, attribution line, AI transformation, or successful render does not establish publication rights.

## TikTok and SRT source

Record the SRT file hash, permission status, and permission reference when one exists. Keep the reference blank when none is available.

For a TikTok2Shorts import, preserve the canonical TikTok URL, creator, source-video hash, acquisition record, and exact permission status from the source project. A generated SRT or whiteboard transformation must not upgrade `unknown` or `review_required` rights.

## Scene images

Create one `rights-manifest.json.assets[]` record for each scene image. Preserve:

- project-relative path;
- creator;
- original source page when applicable;
- permission status and reference;
- whether the image is synthetic;
- required display attribution, if any.

Generated images must use `synthetic: true`. Generation does not remove reference-image or character rights concerns.

## Background music

Use only a renderer-generated no-vocal tone bed, a new renderer recording based on a verified public-domain composition, or a recording in `shorts-music-catalog.json`. A catalog recording must have an official source page and download URL, a verified licence, exact required attribution, and a known SHA-256. Fetch it with `music-fetch`; do not accept a same-title file from another source.

Never copy audio from TikTok, a streaming service, or an unverified third-party page. Do not embed a commercial chart song merely because it is available in a platform's Shorts library. Add that kind of track after upload with the platform's official music picker so its platform licence and Content ID handling remain intact.

Record generated audio with its project-relative path, generator, SHA-256, `permission_status: owned`, `synthetic: true`, and `vocals: false`. Record a catalog track as `permission_status: licensed`, `synthetic: false`, with its track ID, licence URL, source page, attribution, and verified SHA-256.

For a public-domain melody remix, separately record the composition title, composer, `permission_status: public_domain`, and an HTTPS score source. `owned` applies only to the plugin-generated recording, not to the composition or the TikTok source. Generated music does not upgrade the TikTok source or scene-image rights.

## Draft and final boundary

- Block `not_permitted` inputs.
- Permit `unknown` and `review_required` only in a local draft. The default Whiteboard workflow keeps a visible label. A news2shorts compatibility draft may hide that label only when `publish_blocked: true`, source provenance, pending rights, and user-owned pre-publication review are retained in project and render metadata.
- Require `owned`, `licensed`, or `permission_confirmed` for a clean final.
- Do not upload. The plugin cannot determine fair use, monetization eligibility, or platform acceptance.
