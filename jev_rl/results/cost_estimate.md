# Cost estimate for the test pass

Price source: public OpenRouter listing `https://openrouter.ai/api/v1/models/typesafe/jev-1.14/endpoints` (no auth, no project data sent).
Pricing: prompt $0.000000042 per token (= $0.042 per million tokens), completion $0. The decisions endpoint returns no completion tokens in this pricing.

## Call count (computed offline by replaying the reward code with a stub client; test split, 176 items, nine declared runs)

| part | distinct Jev calls (none cached; cache only holds validation) |
|---|---|
| analyze.py, B1 + B2, nine runs | 1677 |
| exploit.py, 176 items x 5 kinds x B1/B2 (additional distinct calls) | 976 |
| total | about 2653 |

Distinct calls are counted by cache key, so identical states shared across runs (B1 choice call per item, gold-equal candidates) are paid for once.

## Cost

Assume a generous 1500 prompt tokens per call (report text plus question set): 2653 x 1500 = about 4.0M tokens = about $0.17. Even at 10x that token count the spend is under $2. Gate: under $5, proceed.

## Revised scope (Cole): single test run, gemma3-1b-lora-n207

Scope was reduced before any run was logged. A first all-nine-runs invocation was started and stopped by hand before it finished; it wrote no test_runs.log entry and no report, but it did populate the cache with some test-split calls (cached responses are reused, so they are not paid for twice).
Reduced estimate: analyze.py on one run is at most 176 B1 choice calls + about 176 road calls + 176 B2 calls = about 530 calls; exploit.py adds about 976 distinct calls minus overlap with the gold candidates. Total about 1500 calls, about 2.3M tokens at 1500 tokens/call, about $0.10. Gate (under $5) passes.

## Actual (after the run)

The cache grew from 439 files (validation) to 2041 files, i.e. about 1600 new distinct calls (this includes calls made by the nine-run invocation that was stopped, which were reused where the same state recurred). At the assumed 1500 tokens per call this is about 2.4M tokens, about $0.10. The true figure was not read from the provider dashboard; it should be treated as an estimate. The exploit run hit repeated connection resets and read timeouts from the API and was relaunched several times; only uncached calls were re-sent, and no results were affected.
