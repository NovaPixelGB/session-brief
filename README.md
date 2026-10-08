# Session Brief

Free completed-hour spot research for people following BTC, ETH and SOL during London hours. It adds volume and range comparisons against the same UTC hour on the previous seven days. Reader demand remains untested.

Start with **START_HERE.md**. Double-click **refresh.cmd** on Windows or run `python agent.py` on Python 3.11+. No third-party packages.

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

`python -m unittest -v` checks calculations, unfinished candles, gaps/staleness, invalid numbers, zero baselines, partial coverage and total failure. The manual Actions workflow tests and uploads an artifact, without committing or publishing. A separate deployment example needs deliberate activation.

Review [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) before future business hosting. Uploading this folder alone does not activate a public site or a recurring service; the earlier instruction overstated this.

`legacy_snapshot.py`, `LEGACY_README.md` and old snapshot reports remain for reference. Old reports mislabeled USDT as USD; use Session Brief for current research.

The pipeline is deterministic research automation, without ongoing AI calls. No users, demand or revenue have been established.
