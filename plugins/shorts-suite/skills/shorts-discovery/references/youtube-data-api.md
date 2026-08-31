# YouTube Data API discovery option

Use YouTube Data API v3 only for public metadata leads. It does not replace browser inspection, original-source tracing, Korean Gap review, or rights evidence.

## Credential handling

- Read `YOUTUBE_API_KEY` first. On macOS, use the `shorts-suite.youtube-data-api-key` Keychain item second.
- Never accept or print the key in a command argument, URL query, project JSON, log, report, or conversation.
- Ask the user to run the hidden-input setup command in their own terminal when no key is available:

```text
python3 -B <plugin-root>/scripts/discover.py configure-youtube
```

- Check configuration without revealing the key:

```text
python3 -B <plugin-root>/scripts/discover.py doctor --check-youtube --json
```

If a Codex sandbox reports `keychain_check_limited: true`, do not conclude that the key is missing. Ask the user to run the same doctor command in their own terminal.

## Collect metadata signals

Use focused queries and one page per query. The default window remains 48 hours.

```text
python3 -B <plugin-root>/scripts/discover.py youtube-signals \
  --query "unexpected company response" \
  --query "strange internet incident" \
  --hours 48 \
  --region-code US \
  --relevance-language en \
  --per-query 10 \
  --max-signals 30
```

The command calls `search.list` for IDs and snippets, then batches IDs through `videos.list` for public statistics, duration, and status. It does not request extra pages automatically. Quota is recorded as method call counts because Google now manages `search.list` in a granular quota bucket; consult the current Google Cloud quota page for actual remaining limits.

## Output boundary

`youtube-api-signals.json` records:

- title, channel, publication time, and duration;
- views, likes, comments, and capture time;
- matched queries and API call counts;
- `browser_verification_required: true`;
- `rights.status: unknown` and `reuse_allowed: false`.

Do not download videos, thumbnails, captions, audio, or comments. Do not turn a signal directly into a candidate. Inspect the content, confirm the visible action and likely source, perform Korean Gap checks, then create the normal candidate batch using `collection_method: hybrid_youtube_api_browser`.

## Security and access boundary

- Public metadata reads use an API key. Private account data, ownership filters, upload, modification, and deletion require OAuth and are outside this skill.
- Keep TLS certificate verification enabled. The CLI may select an existing system CA bundle when Python's default CA file is unavailable; it never disables verification.
- API metadata and public URLs do not grant reuse permission or publication readiness.
