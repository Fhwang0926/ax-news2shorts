# Research workflow

## Discovery modes

### Current discovery

Use this mode for a topic or bare request.

- Default lookback: 48 hours.
- Default candidate limit: 10.
- Search broadly enough to compare evidence, then rank no more than ten eligible candidates.
- Prefer public creator or platform pages that expose the actual post, time, and metrics.
- Record every checked platform as `ok`, `blocked`, or `unavailable`; a blocked platform is not evidence of no matching content.

### URL comparison

Use this mode when the user provides one or more URLs.

- Inspect each URL and its visible source trail.
- Disable the recency gate only when the purpose is comparison rather than current discovery.
- Do not infer that the supplied uploader owns the source.

## Evidence collection

For every candidate, capture only facts that can be traced to public pages:

1. Canonical post URL, platform, title, creator, and timezone-aware publish timestamp.
2. Exact visible counts and the page or screen on which they were observed.
3. A literal description of the visible action. Separate observation from interpretation.
4. Why the first seconds create a question and whether the sequence has setup, development, and payoff.
5. Why short Korean narration adds context instead of merely translating the clip.
6. Source-trace clues: watermark or handle, explicit attribution, earliest located post, creator consistency, and repost references.
7. Korean Gap checks using Korean paraphrases, object/action combinations, and close semantic variants. Record the queries and the count of genuinely similar Korean results, not every keyword hit.
8. Rights evidence. A public URL and attribution do not grant reuse permission.

Search pages and aggregator snippets can lead to a candidate, but the candidate needs direct or independently corroborated evidence. When exact metrics or dates are unavailable, exclude the item rather than inventing them.

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

Do not describe the first-ranked item as selected. Ask the user to choose a Candidate ID before any downstream work.
