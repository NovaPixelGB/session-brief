# Session Brief

Free completed-hour spot research for people following BTC, ETH and SOL during London hours. It adds volume and range comparisons against the same UTC hour on the previous seven days. Reader demand remains untested.

**[Read the live brief](https://novapixelgb.github.io/session-brief/)** · **[Subscribe via Atom](https://novapixelgb.github.io/session-brief/feed.xml)** · **[Give feedback](https://github.com/NovaPixelGB/session-brief/issues/new?template=reader-feedback.yml)**

Public launch verified on 8 October 2026. The live page refreshes automatically every six hours at minute 17 UTC through standard GitHub Actions runners. No local computer or model API is needed. A daily Codex follow-up checks failures and reader feedback using the owner's existing allowance; it does not buy any services.

To run locally: `python agent.py` then `python make_feed.py`, using Python 3.11+. No third-party packages. Windows users can use `py -3` instead of `python`.

## Outputs

- `site/index.html`: responsive snapshot, 24-hour sparklines, downloads, freshness indicator and feedback-copy tool.
- `site/latest.md`, `site/latest.json`, `site/source-data.json`: brief, calculated metrics and archived exchange responses.
- `outbox/sample-brief.md` and `outbox/first-users.md`: sample and drafted reader experiment.
- `reports/session-brief-*.md` and `state/raw-*.json`: dated research and source archives.
- `state/activity.jsonl`: append-only execution/failure log.

## Method and limits

Reads [Binance's public market-data host](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md) without keys. [Candle documentation](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#klinecandlestick-data) defines the source fields. Prices and quote volumes are **USDT**, not USD. No account, wallet or trade functions exist.

169 consecutive closed hours supply the current hour plus seven daily same-UTC-hour observations. Hour return: close/open − 1. Range: (high − low)/open. 24h return compares closes 24 hours apart. Relative volume/range divides the current value by the seven-observation median. The 1.50× volume flag is an editorial choice, not predictive evidence. Seven samples, weekends, events and one-exchange coverage limit interpretation.

Incomplete hours are excluded. Stale, gapped or invalid data is rejected. Partial coverage is shown; total failure exits nonzero and retains the previous brief with its original timestamp. Source failures, geographic restrictions and rate limits are respected without bypass. London display uses an IANA timezone database when available (normally on Linux). Windows without it prints an explicit UTC fallback. All calculations use UTC.

## Verification and deployment

`python -m unittest -v` checks calculations, unfinished candles, gaps/staleness, invalid numbers, zero baselines, partial coverage and total failure. `.github/workflows/pages.yml` tests, generates the brief and feed, and publishes `site/` on source pushes, manual runs and a six-hour schedule. It does not commit output back into source. Schedules can be delayed and may be disabled after 60 days of repository inactivity.

This is a free informational research demo. Review [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) before future business hosting. There is no checkout or commercial SaaS. Standard hosted runners in public repositories are [free under GitHub's current policy](https://docs.github.com/en/actions/concepts/billing-and-usage).

Local legacy snapshots are retained for reference, separate from the public source upload. Those old reports mislabeled USDT as USD; use Session Brief for current research.

The data pipeline is deterministic research automation, without ongoing AI calls. Readers can subscribe through the Atom feed and respond through a public GitHub issue form. Publishing and repository topics make the product accessible but do not establish demand. No users or revenue have been established; distribution beyond GitHub needs a relevant authorised channel.
