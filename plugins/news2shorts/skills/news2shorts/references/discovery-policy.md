# Current Issue Discovery Policy

Use this policy only when finding current news candidates. It ranks editorial review priority; it does not predict views, measure national opinion, or replace source verification.

## Discovery lanes

Run all of these lanes for a source-less request:

- broad current news: politics, economy, society, and technology;
- politics and accountability: government policy, National Assembly activity, elections, public officials, favoritism, conflicts of interest, false reporting, concealment, omission, and failed oversight;
- household cost and assets: taxes, prices, fees, pensions, housing, deposits, loans, and interest rates;
- safety and health: accidents, fires, recalls, crime, medical access, food, and workplace safety;
- education and labor: schools, students, teachers, hiring, wages, unemployment, and retirement;
- rights and information: privacy, hacking, leaks, refunds, compensation, discrimination, and consumer harm;
- public services: transport, electricity, communications, administrative delays, closures, cancellations, and outages.

Use a primary six-hour window for velocity, a 24-30 hour discovery window for candidates, and an older window only when the issue is still gaining independent coverage. Do not let one topic consume the shortlist merely because the same release was syndicated many times.

## NewsPic discovery surface

For every source-less request, inspect the public NewsPic news category at `https://m.newspic.kr/main?category=CA01`. Also inspect `https://m.newspic.kr/liveKeyword` when it exposes usable current headlines. Keep only the headline, displayed publisher, displayed publication time, NewsPic URL, and observation time needed for the active review.

NewsPic is an aggregator and discovery lead, not an independent fact source, popularity measurement, public-opinion signal, or media-reuse licence. Resolve the original publisher page from a usable outbound link or an exact headline-and-publisher search, then apply the normal original, official, and independent-source checks. Do not count the NewsPic domain toward source diversity or six-hour velocity. Multiple NewsPic entries from the same publisher remain one underlying source.

If a NewsPic article page is inaccessible, returns a cache miss, or does not expose the original publisher page, continue with the displayed headline and publisher only long enough to search for the original. Reject the lead when the canonical article and required corroboration cannot be verified. Report `NewsPic 확인`, `NewsPic 미확인`, and how many shortlisted candidates originated from that pool; never silently substitute another aggregator.

## Previously covered topic gate

Apply project history before the citizen-impact and hotness gates. Read the current workspace's `projects/**/project.json` and sibling `sources.json` files for prior news2shorts work. Treat every recognized project as already covered when it has reached initialization, research, revision, draft render, or final render; pending approval does not make the topic new.

Exclude a candidate when either condition is met:

1. its canonical source URL matches a prior project's source URL or a URL recorded in that project's `sources.json`;
2. its headline and corroborating article titles match the prior title, topic, hook stake, issue focus, viewer stake, payoff, or corroborating titles as the same news cluster.

A different publisher, rewritten headline, later reaction article, or routine incremental update is still the same covered story. Keep the exclusion transparent by recording the prior project path, status, title, topic, and match reason, but do not place it in the selectable shortlist. Report the number excluded. Apply the same manual history check when NAVER API is unavailable. Revisit a covered cluster only when the user explicitly supplies that topic or URL and asks for a follow-up, correction, or rerender.

## Citizen-impact gate

Apply this gate before scoring or recommending a cluster. A candidate qualifies only when the reviewed sources support all three answers:

1. who is directly affected, such as a family, consumer, resident, worker, patient, driver, tenant, student, or service user;
2. what concrete cost, safety or protection failure, lost right or access, or public-service disruption reaches that group;
3. one plain sourced sentence answering `누가 무엇을 얼마나 잃거나 위험해지는가?`.

The automated `discover` command uses titles and summaries to reject clusters that lack a direct consequence path and records its reasons in `citizen_impact_gate`. Treat that as a conservative first pass, then verify the one-sentence consequence against the original reporting. Exclude organization-internal bonuses, executive or shareholder disputes, party conflict, procedural announcements, and abstract gaps when no consequence outside the institution is established. A high velocity, political, accountability, trend, or community score never overrides this gate. Continue searching and replace rejected items until ten qualified clusters are ready; never weaken this gate to fill the count.

## Hotness evidence

After the citizen-impact gate passes, the automated `discover` result exposes a 100-point review-priority score:

| Component | Maximum |
|---|---:|
| Freshness | 15 |
| Independent-news velocity in six hours | 20 |
| Source diversity | 15 |
| Citizen sensitivity | 20 |
| Political relevance | 5 |
| Verified accountability terms | 10 |
| Cross-community lead signal | 5 |
| Query coverage | 5 |
| Verification readiness | 5 |

NAVER search trend may add up to 10 points before the total is capped at 100. NewsPic placement or ranking never adds points. Treat every component as a transparent comparison aid, not a performance claim. Prefer candidates with a concrete public consequence and a question that can be answered in 12-35 seconds. Deprioritize a procedural announcement with no identified citizen effect, duplicated press-release coverage, a topic that needs more than ten seconds of setup, or a claim whose payoff remains unknown.

Politics receives discovery coverage, not automatic editorial endorsement. A political candidate should reach the shortlist when it has current independent reporting plus a concrete effect on citizens, public money, safety, rights, fairness, or institutional trust. Party conflict alone is not enough.

## Public community signals

Community pages are lead discovery only. Use public pages that require no login, subscription, CAPTCHA, form submission, or access-control bypass. When possible, check at least two communities with different audience profiles so one coordinated or partisan space cannot define the result.

Keep only this minimal metadata for the active review:

```json
{
  "signals": [
    {
      "title": "public post title",
      "community": "community name",
      "url": "https://public.example/post"
    }
  ]
}
```

Pass that temporary file to `discover --community-signals <path>` only when NAVER API discovery is available. The command accepts at most 50 signals, discards extra fields, and matches titles to an existing news cluster. One community yields no score. Two distinct communities yield a small signal and three or more reach the five-point cap.

Never preserve or quote post bodies, comments, usernames, profile details, private identifiers, victim information, rumors, or allegations. Never convert community visibility, ranking, comment volume, or provocative language into `시민들이 분노했다`, `국민적 논란`, or a factual claim. Verify the underlying event through the original or official source and the required independent news sources.

## Ten-candidate shortlist

Present exactly ten qualified candidates in one numbered list and keep user selection mandatory. A discovery run is complete only when ten unused clusters pass the history, citizen-impact, source, and recency gates. If the first pass is short, continue through unused lanes, broader original-publisher queries, and the remaining 24-30 hour window. If external access still prevents completion, report `후보 조사 미완료: N/10` rather than returning a smaller final list.

Keep the set meaningfully different across:

1. politics or public-accountability impact;
2. household cost, safety, rights, or service impact;
3. a verified reversal or unexpected consequence.

Do not fill a lane with a weak candidate. Replace it with a qualified cluster from another lane. For each item show why it is timely, six-hour independent-news spread, citizen-sensitivity categories, the exact contradiction or public consequence, community coverage status, verification state, first-hook potential, and visual-evidence feasibility. Keep sensitive political, crime, disaster, health, finance, war, election, and minor-related topics behind guided review before final rendering.
