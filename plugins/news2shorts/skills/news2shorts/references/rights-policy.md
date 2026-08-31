# Visual and audio rights policy

## Allowed asset classes

1. `generated`: created for the project and recorded as synthetic.
2. `licensed`: license and attribution requirements are known and compatible with the intended use.
3. `official`: an official source provides explicit reusable media terms.
4. `owned`: supplied by the user with a recorded assertion of rights.
5. `unreviewed`: a publicly reachable source image retained only for a local editorial draft while permission remains `unknown` or `review_required`.

Public availability is not permission. A NAVER News thumbnail, article image, social post, press photo, embedded video, broadcast clip, or search result must not be used without a separate rights basis.

`unreviewed` never means copyright does not apply. It requires the canonical source page, creator or publisher when known, retrieval time, exact scene relevance, `approved: false`, and `local_review_only: true`. It may be transformed into a whiteboard review scene only after `whiteboard_text_free_reviewed: true`; the derivative inherits the original permission status. It does not count toward the approved real-media ratio and clean-final validation must reject it.

`collect-internet-visual` may fetch a selected public HTTPS image for this local-review path. Require a separate canonical source page, reject private or non-HTTPS hosts and non-image responses, enforce the file-size and pixel limits, preserve the final download URL and SHA-256, and never send browser credentials or remove a watermark. The operator remains responsible for adding permission evidence before publication.

## Web search workflow

1. Search the current news cluster and login-free public community posts for each scene's exact subject, action, and visible result before opening generic stock libraries. Do not retain community comments, usernames, avatars, profile images, private addresses, vehicle plates, or unrelated people.
2. Open the canonical news article or community post before deciding. Treat the page and its image as discovery until subject, date or context, creator or publisher, license or permission text, attribution, privacy, and modification restrictions are reviewed.
3. If the news or community image has a compatible permission basis, collect it as `licensed`, `official`, or `owned`. If it is directly relevant but permission remains unclear and the user will review rights before publication, collect only the selected original as `unreviewed`, `approved: false`, and `local_review_only: true`; prefer that local-review evidence over a generic stock substitute.
4. When no usable current-news or public-community visual survives relevance, privacy, and access review, check official libraries, public-domain collections, and asset-specific commercial-use-compatible licensed sources. Use a generic stock library only after those searches are recorded.
5. Download the selected original or documented derivative into `assets/collected/` and inspect the local file. For footage, also verify the depicted event, capture date or context, and permitted edit or excerpt terms.
6. Record every search decision and asset provenance. Use generation only after the news, public-community, official, and licensed-library paths fail or cannot safely explain the scene.

New Shorts still require at least one rights-cleared, non-synthetic news photo. Version 14 also requires actual photos and real footage to cover at least 60% of visual scenes. It may be licensed media, reusable official media, or user-owned media, but it must depict the reported subject, place, object, person, or event rather than merely suggest the topic. Mark `news_relevance_reviewed: true` only after that match is checked. If the photo minimum or real-media ratio cannot be met safely, generation may fill explanatory scenes for review but final rendering remains blocked.

For every asset used by a project version 3 `quick-reveal`, record `relevance_level` as `direct` or `contextual` and add a concrete `relevance_note` naming what in the image matches the scene claim. `Direct` means the actual reported person, object, event, document, or exact mechanism. Sharing only a city, industry, landscape, or mood is `contextual`. Hook, evidence, turn, impact, and payoff beats require `direct`; a contextual asset is allowed only in a context beat. This relevance review applies to generated explanatory visuals as well as collected media.

Do not use search-engine thumbnails, image proxy URLs, article screenshots, embedded-player captures, or a publisher's visual merely because a download succeeds. Do not remove watermarks or crop out attribution marks to make an asset usable.

Do not treat a public community post as permission. A community-hosted image with unknown rights remains a local-review asset even when the post is public, highly viewed, or widely reposted. Reject images that expose private individuals, minors, home addresses, license plates, usernames, or other unnecessary personal information.

## Korean and international source-event context

New projects use Korean images by default. A Korean collected or generated asset must record `visual_locale: "ko-KR"`, `korean_context_reviewed: true`, and a specific `korean_context_note`. Review the pixels for Korean-language signs, Hangul road or facility markings, Korean road geometry, apartment or storefront architecture, vehicle mix, public-facility design, currency, uniforms, and other location cues. The source being a Korean publisher or community does not prove the image is Korean.

Reject foreign police uniforms, emergency vehicles, road signs, license plates, architecture, storefront language, currency, traffic markings, and obvious foreign stock settings when they are being used as Korean substitutes. Do not crop those cues away to pass the review. When a directly relevant Korean image cannot be found, use a Korean-context official document or a clearly explanatory `korean-editorial-realism` fallback.

An international incident may use actual foreign source-event media only when the user explicitly selected that incident, a direct Korean citizen safety or rights consequence is recorded, and `international_source_visuals.enabled` is true. Each such asset records the configured source-country locale, matching `source_country`, `source_event_context_reviewed: true`, a concrete `source_event_context_note`, and `actual_event_media: true` for photos or video. Use only the exact reported event; unrelated foreign stock and visually similar old disasters remain prohibited. Public footage with unknown permission remains `unreviewed`, `approved: false`, and `local_review_only: true` until a compatible license or permission reference is supplied.

Use official material only when its page states a compatible reuse basis. An official account or press page alone does not imply permission.

## Named politicians and public officials

Extract every fully named politician or public office-holder from the planned narration and visible copy before visual sourcing. For each person who is central to the story, search for a real, rights-cleared photo and use one at least once, preferably at the first meaningful mention. Prefer an image of the reported event; otherwise use a clearly credited current or context-appropriate portrait whose identity has been visually checked.

Do not generate an AI likeness of a named politician or public official, and do not use an unlicensed broadcast frame, social capture, press photo, or official profile merely because it is publicly accessible. The asset-specific page must state a compatible public-domain, Creative Commons, public-sector reuse, or other explicit commercial-use basis. Reject embedded watermarks and do not crop them away.

When no reusable, watermark-free photo survives review, record a `no_usable_asset` search decision and use a relevant official document, chart, map, rights-cleared footage, or clearly explanatory graphic. Never fabricate the person's face to fill the gap.

## Named people and sensitive private persons

Review every central named real person before sourcing, including officials, public figures, accused people, victims, and private persons. Record the exact name, role, first meaningful `scene_ids`, intended `asset_path`, and `visual_status` (`used`, `privacy_excluded`, or `rights_blocked`) in `editorial_grounding.people`. A used named-person asset also records `person_names` and `person_identity_reviewed: true` after visual confirmation.

Use an actual photo only when its asset-specific license or permission supports the intended reuse. Do not treat a family-provided image, missing-person notice, social post, publisher photo, agency profile, or search result as reusable merely because it is public. For victims and other private people, require a documented reuse basis plus an editorially necessary public-interest purpose; otherwise preserve privacy and record why the photo was excluded. Never create or substitute an AI likeness of any named real person.

A rights-cleared real person who is not involved in the reported case may appear only as contextual material. The scene and asset record must say `사건 당사자 아님`, and the composition, headline, and narration must not imply that the pictured person is the named victim, suspect, official, witness, or complainant.

## Thumbnail presenters

An ordinary non-sensitive story may use a separate polished presenter portrait to frame the thumbnail as a visual news explanation. Prefer a user-owned or licensed portrait, or an original synthetic persona that is not based on a real broadcaster, celebrity, public figure, named subject, or supplied person's likeness. Never scrape a face from a news article, broadcaster page, social account, search result, or stock preview.

Record `usage_role: "thumbnail-presenter"`, `presenter_context_reviewed: true`, and `case_party: false`, plus the ordinary provenance, license, synthetic, approval, and visual-quality fields. The thumbnail must visibly identify it as a presenter image and must not imply that the person is the reporter, source, witness, victim, suspect, official, complainant, or article subject. Do not use presenter framing for crime victims, disasters, minors, health emergencies, or other sensitive reporting; use direct evidence instead.

## Named companies, logos, and brand imagery

Review the planned narration and visible copy for specifically named companies. Add only companies that are central parties to `visual_sourcing.company_visuals.companies`; do not treat the news publisher, a source credit, or an incidental comparison as a central company. Record the exact company `name` and the `scene_ids` of its first meaningful mention.

For each recorded company, use at least one real, non-synthetic logo or directly matching company image in one of those scenes. Search in this order: an official brand or media library with explicit compatible reuse terms; a canonical public-domain or commercial-use-compatible licensed logo page; a licensed company photo; a branded product; identifiable headquarters, storefront, vehicle, or facility signage. Choose a logo only when it remains legible at Shorts size and does not overwhelm the factual evidence.

Public availability, a press-room download button, or a company-owned page does not by itself grant commercial reuse permission. Verify the asset-specific permission or license, creator or publisher, attribution, modification limits, and any relevant trademark restriction. Use the mark only for factual editorial identification, do not alter it in a misleading way, and do not imply sponsorship, partnership, approval, or endorsement.

Record `company_names`, `company_visual_type` (`logo`, `official-image`, `licensed-photo`, `branded-product`, or `facility-signage`), and `company_identity_reviewed: true` in the rights record after visually confirming the company match. Do not generate, redraw, approximate, or repair a company logo with AI. If no rights-safe logo or real company image survives review, record `no_usable_asset` with the rejected rights basis and stop before final rendering; a generic building, invented logo, or unrelated industry image does not satisfy the company visual requirement.

## Reaction memes and short reaction clips

Use a meme only as a brief `context` or `rehook` reaction, never as evidence for a factual claim. Prefer a licensed reaction asset, user-owned material, or an original locally authored meme card. Record `usage_role: "reaction-meme"` and `meme_origin: "licensed"`, `"owned"`, or `"original"` in the asset record. Keep reaction memes to about 20% of scenes or fewer.

Do not use film, television, broadcast, celebrity, social-post, community, watermark, or search-result captures without explicit commercial-use permission. Do not crop away attribution or rely on parody or public popularity as the rights basis. Exclude humorous reaction memes from sensitive harm, disasters, crime victims, minors, health emergencies, or other contexts where they would trivialize the subject.

A version 5 project may name a meme as its primary attention device only when the referenced storyboard scene and rights record satisfy those restrictions. Otherwise choose a rights-cleared contrast composite, consequence photo, evidence closeup, or motion proof. Provocative framing never relaxes provenance, relevance, sensitivity, or commercial-use requirements.

## Manifest requirements

Each image or clip used by the storyboard must have:

- project-relative `path`;
- `kind`;
- `source_url` when collected;
- creator or publisher when known;
- `license` or permission basis;
- attribution text when required;
- retrieval or generation time;
- `synthetic` boolean;
- `approved` boolean.
- `permission_status`: `unknown` or `review_required` for `unreviewed` assets.
- `local_review_only: true` for `unreviewed` assets.
- `whiteboard_text_free_reviewed` boolean when the asset may enter whiteboard preparation.
- `media_type`: `photo`, `video`, `document`, `chart`, `illustration`, `pictogram`, `screenshot`, `map`, or `logo` for version 14 projects.
- `relevance_level` and `relevance_note` for every asset in a project version 3 quick-reveal.
- `visual_locale: "ko-KR"`, `korean_context_reviewed: true`, and a concrete `korean_context_note` for Korean-visual-only projects; or the configured source locale, `source_country`, `source_event_context_reviewed`, `source_event_context_note`, and `actual_event_media` for an approved international source-event scope.
- `company_names`, `company_visual_type`, and `company_identity_reviewed: true` when the asset identifies a central named company.
- `usage_role: "thumbnail-presenter"`, `presenter_context_reviewed: true`, and `case_party: false` for a separate presenter portrait.

A real news photo counted toward the project requirement also needs `news_relevance_reviewed: true`. Every non-synthetic collected visual in a project version 3 quick-reveal needs that review, not only the single photo counted toward the global minimum. A generated image needs `visual_quality_reviewed: true` after inspection for distorted anatomy, duplicated objects, broken geometry, pseudo-text, unintended marks, compression artifacts, and unsafe cropping. Do not place text, numbers, captions, or logos inside a generated asset when the renderer can overlay them reliably.

For a collected web asset, also record `source_method: "web_search"`, the canonical `source_url`, and the search query when practical. `rights-manifest.json.searches` should contain:

- `query`;
- related `scene_ids`;
- `searched_at`;
- `outcome`: `collected`, `generated`, or `no_usable_asset`;
- `selected_asset_path` when an asset was collected;
- a short decision note when the result was rejected or generation was chosen.

Generated assets should also record the prompt, generation provider, pixel dimensions, optimization time, and `visual_quality_reviewed` state when available. Normalize generated stills to the project's `generated_image_size`, normally 720x1280, before final validation. Footage records should identify the original clip page and any excerpt or modification conditions. The renderer removing original clip audio does not remove the need to verify visual rights.

New projects should set `visual_sourcing.min_real_media_ratio` to `0.6` and `visual_sourcing.max_generated_scene_ratio` to `0.4`. Treat both as production gates rather than permission to use irrelevant stock media or synthetic visuals: if a draft misses either target, re-run the reusable photo, official document, footage, chart, and map search and record why each remaining non-photo scene is necessary.

## Generated visual style

Use generation only after the reusable-media search is documented. Choose either grounded editorial realism or a flat pictogram system:

- Editorial realism uses ordinary lighting, plausible materials, natural proportions, restrained grading, and documentary camera language. Avoid glowing circuitry, holograms, neon AI brains, friendly robots, glossy 3D icons, and impossible interfaces unless the reported story literally contains them.
- Pictograms use flat shapes, consistent strokes, a limited palette, and no gradients, glow, glass, or 3D depth.

Do not create a realistic reconstruction that could be mistaken for documentary evidence. The renderer does not add an on-frame synthetic badge, so generated visuals must remain clearly explanatory, anonymized, and preferably pictogram- or diagram-based. Keep their synthetic status in the rights, publish, project, and render metadata.

## Synthetic media

If a realistic asset depicts a real person, place, disaster, conflict, arrest, medical event, or other event that did not occur as shown, exclude it. If an explanatory reconstruction is editorially necessary, make it visibly illustrative rather than documentary and record that upload disclosure is required. Do not rely on an on-frame badge as the only disclosure record.

Do not generate a real public figure committing an act, speaking words, or appearing at an event without reliable evidence. Do not clone another person's voice.

## Audio

Use user-owned audio, a documented reusable track, or a platform audio library under its terms. Typecast narration must follow the active Typecast account plan and usage policy; record its provider, model, and voice ID in the render report, but never record the API key. The local system voice is allowed for private draft production. Publication rights for third-party music must be verified separately.
