# Research workflow

## Discovery modes

### Current discovery

Use this mode for a topic or bare request.

- Default lookback: 48 hours.
- Default candidate limit: 10.
- Default editorial focus: fun-first.
- Default YouTube target: at least 3 eligible candidates when public evidence supports them.
- Search broadly enough to compare evidence, then rank no more than ten eligible candidates.
- Prefer public creator or platform pages that expose the actual post, time, and metrics.
- Record every checked platform as `ok`, `blocked`, or `unavailable`; a blocked platform is not evidence of no matching content.

Start with YouTube. If YouTube Data API is configured, use it for metadata leads and verify the selected pages in the browser. If it is unavailable, search the public Shorts surface directly. Do not substitute a generic web result for an inspected Shorts post. Run ranking with `--min-youtube 3`; if fewer than three YouTube candidates pass, preserve the shortfall instead of padding.

## Fun-first editorial filter

Prefer candidates that provide at least two of these qualities:

- recognizable person, company, product, game, or object;
- immediate visual oddity or demonstration;
- one-sentence reversal, correction, payoff, or official response;
- humor, satisfaction, surprise, harmless conflict, or culture gap;
- strong scene changes without requiring a long policy or technical setup.

For an ordinary mixed-topic shortlist, keep breach, vulnerability, geopolitical, regulatory, and other heavy incidents to no more than two candidates. A heavy topic may still qualify when its entertainment value is explicit and responsible; importance alone is not entertainment.

### URL comparison

Use this mode when the user provides one or more URLs.

- Inspect each URL and its visible source trail.
- Disable the recency gate only when the purpose is comparison rather than current discovery.
- Do not infer that the supplied uploader owns the source.

### YouTube API assisted discovery

Use this mode only when the user asks to include Google YouTube API or explicitly chooses a hybrid search. Read [youtube-data-api.md](youtube-data-api.md), collect one page of public metadata per query, and preserve the signal file. The API can support exact metric and publication-time evidence, but every shortlisted candidate still needs visible content inspection, source tracing, Korean Gap checks, and rights review.

Use `collection_method: hybrid_youtube_api_browser` only when the final candidate batch actually combines API metadata with browser or public-web verification. API-only signals are not valid candidate records.

## Evidence collection

For every candidate, capture only facts that can be traced to public pages. Classify a directly usable short clip as `video_signal`; classify a cross-platform incident, official response, community story, or article-led topic as `story_event`.

1. Canonical post URL, platform, title, creator, and timezone-aware publish timestamp.
2. Exact public counts and the API response or page on which they were observed.
3. A literal description of the visible action. Separate observation from interpretation.
4. Why the first seconds create a question and whether the sequence has setup, development, and payoff.
5. Why short Korean narration adds context instead of merely translating the clip.
6. Source-trace clues: watermark or handle, explicit attribution, earliest located post, creator consistency, and repost references.
7. Korean Gap checks using Korean paraphrases, object/action combinations, and close semantic variants. Record the queries and the count of genuinely similar Korean results, not every keyword hit.
8. Rights evidence. A public URL and attribution do not grant reuse permission.
9. Entertainment value. Explain what makes a viewer smile, wonder, feel surprise, anticipate a reveal, or want to share it. Do not equate fear, tragedy, victim impact, or sensational wording with entertainment.

For `story_event`, also record a recognizable subject, concrete event, one-sentence payoff, a stable event-level `story_cluster_id`, and reasons for subject recognition, abnormality or conflict, payoff clarity, twist strength, asset readiness, freshness, comment signal, and evidence strength. The event must be packageable from inspected public evidence even when no single source is a reusable video.

Search pages and aggregator snippets can lead to a candidate, but the candidate needs direct or independently corroborated evidence. When exact metrics or dates are unavailable, exclude the item rather than inventing them.

News, official pages, and communities are discovery sources, not automatic production permission. Use the publisher or visible account as the creator field and keep platform-specific rights and source uncertainty explicit.

## Original-source tracing

Use the following statuses:

- `verified_original`: authorship is directly supported by the creator or a reliable first-party record.
- `probable_original`: multiple clues point to one source, but authorship is not proven.
- `repost_only`: only reposts or compilation pages were found.
- `unknown`: the available evidence cannot support a source conclusion.

Compare timestamps only after accounting for timezones and platform precision. An earlier upload can still be a repost from a deleted or unavailable source. Never remove or crop attribution while investigating.

## Korean Gap review

Generate at least two Korean semantic queries for the observed action. Check whether Korean videos use the same underlying event or mechanism, not merely the same broad category.

Record `similar_results_count` as:

- `0` only after at least two focused queries return no genuinely similar Korean item;
- `1` to `3` for low coverage;
- `4` to `10` for material coverage;
- above `10` for saturation.

The count is a research snapshot, not a permanent market fact. Include capture time and supporting URLs so it can be refreshed.

## Candidate presentation

Present up to ten candidates in score order and then stop. Each candidate needs:

- Candidate ID and canonical URL;
- captured metrics and upload age;
- observed action and story pattern;
- overall score, component scores, and penalties;
- Korean queries, similar-result count, and evidence;
- source status, confidence, likely original URL, and evidence;
- rights status and publication boundary;
- a concise recommendation reason.
- entertainment score and evidence-backed reason;
- YouTube eligible count and shortfall for the batch.

Do not describe the first-ranked item as selected. Ask the user to choose a Candidate ID before any downstream work. After explicit selection, preserve the original shortlist and pass it with the exact Candidate ID to `$shorts-research-packager`; do not reconstruct or silently upgrade the candidate record.
