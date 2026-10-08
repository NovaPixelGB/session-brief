"""Session Brief: public spot research. No credentials, packages or trading."""
from __future__ import annotations
import html
import json
import math
import re
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = Path(__file__).resolve().parent
BASE = "https://data-api.binance.vision"
DOCS = "https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#klinecandlestick-data"
HOUR = 3_600_000
DEFAULT_CONFIG = {"symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"], "mode": "research_only",
                  "allow_public_posting": False, "allow_wallet_access": False, "allow_paid_services": False}

def load_config():
    path = ROOT / "config.json"
    config = DEFAULT_CONFIG | (json.loads(path.read_text(encoding="utf-8")) if path.exists() else {})
    assert_safe(config)
    return config

def assert_safe(config):
    if config.get("mode") != "research_only" or any(config.get(k) is not False for k in
            ("allow_public_posting", "allow_wallet_access", "allow_paid_services")):
        raise ValueError("Only research_only mode with all permission flags false is supported.")
    symbols = config.get("symbols")
    if not isinstance(symbols, list) or not 1 <= len(symbols) <= 10:
        raise ValueError("Provide 1–10 symbols.")
    if not all(isinstance(s, str) and re.fullmatch(r"[A-Z0-9]{2,15}USDT", s) for s in symbols):
        raise ValueError("Only uppercase USDT spot symbols are supported.")
    if len(set(symbols)) != len(symbols):
        raise ValueError("Symbols must be unique.")

def get_json(url):
    for attempt in range(3):
        try:
            req = Request(url, headers={"User-Agent": "SessionBrief/1.0"})
            with urlopen(req, timeout=15) as response:
                if not response.url.startswith(BASE + "/api/v3/"):
                    raise ValueError("Unexpected source redirect")
                return json.load(response)
        except HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
            try:
                delay = float(exc.headers.get("Retry-After", 2 ** attempt))
            except ValueError:
                raise RuntimeError("Rate-limited; retry later") from exc
            if not math.isfinite(delay) or delay > 5:
                raise RuntimeError("Rate-limited; retry later") from exc
            time.sleep(max(0, delay))
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

def number(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Non-finite market value")
    return result

def summarise(symbol, raw, cutoff):
    """Require 169 consecutive complete hours; exclude unfinished candles."""
    if not isinstance(raw, list):
        raise ValueError("Unexpected API response")
    candles = []
    for row in raw:
        if not isinstance(row, list) or len(row) < 9:
            raise ValueError("Malformed candle")
        start, close_at = int(row[0]), int(row[6])
        if close_at >= cutoff:
            continue
        o, high, low, c, volume = map(number, (row[1], row[2], row[3], row[4], row[7]))
        if start % HOUR or close_at != start + HOUR - 1:
            raise ValueError("Invalid hourly timestamp")
        if min(o, high, low, c) <= 0 or volume < 0 or not low <= min(o, c) <= max(o, c) <= high:
            raise ValueError("Invalid OHLC/volume")
        candles.append({"start": start, "open": o, "high": high, "low": low, "close": c, "volume": volume})
    candles.sort(key=lambda x: x["start"])
    if len(candles) < 169:
        raise ValueError("Need at least 169 closed hourly candles")
    candles = candles[-169:]
    if any(b["start"] - a["start"] != HOUR for a, b in zip(candles, candles[1:])):
        raise ValueError("Missing or duplicate hourly candles")
    last = candles[-1]
    if last["start"] != cutoff - HOUR:
        raise ValueError("Latest closed hour missing; data is stale")
    prior = [candles[-1 - 24 * day] for day in range(1, 8)]
    baseline = statistics.median(x["volume"] for x in prior)
    range_pct = lambda x: (x["high"] - x["low"]) / x["open"] * 100
    range_baseline = statistics.median(range_pct(x) for x in prior)
    return {"symbol": symbol, "close": last["close"], "change_1h": (last["close"] / last["open"] - 1) * 100,
            "change_24h": (last["close"] / candles[-25]["close"] - 1) * 100,
            "range_1h": range_pct(last), "range_baseline": range_baseline,
            "volume_1h": last["volume"], "volume_baseline": baseline,
            "volume_ratio": last["volume"] / baseline if baseline > 0 else None,
            "range_ratio": range_pct(last) / range_baseline if range_baseline > 0 else None,
            "closes": [x["close"] for x in candles[-24:]], "baseline_days": 7,
            "source_url": BASE + "/api/v3/klines?" + urlencode({"symbol": symbol, "interval": "1h", "limit": 200, "endTime": cutoff - 1})}

def london_label(dt):
    try:
        return dt.astimezone(ZoneInfo("Europe/London")).strftime("%d %b %Y · %H:%M %Z")
    except ZoneInfoNotFoundError:
        return dt.strftime("%d %b %Y · %H:%M UTC (London timezone unavailable)")

def multiplier(value):
    return f"{value:.2f}×" if value is not None else "unavailable"

def findings(rows):
    eligible = [r for r in rows if r["volume_ratio"] is not None]
    if not eligible:
        return ["Volume comparison unavailable: baseline volume is zero."]
    leader = max(eligible, key=lambda r: r["volume_ratio"])
    return [f"{leader['symbol']} has the highest relative hourly volume in this basket: "
            f"{multiplier(leader['volume_ratio'])} the median for the same UTC hour on the previous seven days.",
            f"{sum(r['volume_ratio'] >= 1.5 for r in eligible)} of {len(eligible)} available pairs meet the "
            "1.50× volume flag. The threshold is an editorial filter, not a statistically tested signal."]

def markdown(report):
    lines = ["# Session Brief", "", "Closed-hour spot research for people following major crypto pairs during London hours.", "",
             f"**Hour ending:** {report['london_hour']}  ", f"**Generated:** {report['generated_at']}  ",
             f"**Coverage:** {len(report['assets'])}/{len(report['symbols'])} pairs; Binance spot only; prices in USDT.", "",
             "| Pair | Hour close (USDT) | 1h change | 24h change | 1h range | Volume / usual |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for r in report["assets"]:
        lines.append(f"| {r['symbol']} | {r['close']:,.2f} | {r['change_1h']:+.2f}% | {r['change_24h']:+.2f}% | "
                     f"{r['range_1h']:.2f}% | {multiplier(r['volume_ratio'])} |")
    lines += ["", "## What changed", ""] + ["- " + x for x in findings(report["assets"])]
    if report["errors"]:
        lines += ["", "## Missing coverage", ""] + [f"- {s}: unavailable ({e})." for s, e in report["errors"].items()]
    lines += ["", "## Check the numbers", "",
              "Volume / usual = completed hour quote volume ÷ median quote volume at the same UTC hour on the previous seven days. "
              "Hour range = (high − low) ÷ hour open. 24h change compares completed hourly closes 24 hours apart. "
              "The unfinished candle is excluded. Seven observations are a small descriptive baseline; weekends and events can distort it.", "",
              "London display follows daylight saving where timezone data is available. The comparison is always at the same UTC hour.", "",
              "USDT is the quote asset, not USD. No news attribution, forecasts or trade recommendations are inferred from these figures.", "",
              f"[Binance candle field documentation]({DOCS})", ""]
    lines += [f"- [{r['symbol']} public source]({r['source_url']})" for r in report["assets"]]
    lines += ["", f"Exact responses and retrieval times: `{report['raw_file']}`. "
              "A single exchange cannot describe the whole market. Historical research only.", ""]
    return "\n".join(lines)

def sparkline(closes):
    low, high = min(closes), max(closes)
    points = " ".join(f"{i * 240 / (len(closes)-1):.1f},{38 - 32*(c-low)/(high-low or 1):.1f}" for i, c in enumerate(closes))
    return f'<svg viewBox="0 0 240 44" role="img" aria-label="Last 24 hourly closes, independently scaled"><polyline points="{points}" fill="none" stroke="currentColor" stroke-width="2"/></svg>'

def render_site(report):
    esc = html.escape
    cards, trs, baselines = [], [], []
    for r in report["assets"]:
        direction = "positive" if r["change_1h"] >= 0 else "negative"
        cards.append(f'<article class="card"><div class="pair">{esc(r["symbol"])}</div><h2>{r["close"]:,.2f} <small>USDT</small></h2>'
                     f'<p class="{direction}">{r["change_1h"]:+.2f}% last closed hour</p>'
                     f'{sparkline(r["closes"])}<p class="muted">24 hourly closes · independent scale</p></article>')
        flag = "Elevated volume" if r["volume_ratio"] is not None and r["volume_ratio"] >= 1.5 else "Below flag" if r["volume_ratio"] is not None else "No baseline"
        trs.append(f'<tr><th scope="row">{esc(r["symbol"])}</th><td>{r["change_24h"]:+.2f}%</td><td>{r["range_1h"]:.2f}%</td>'
                   f'<td>{multiplier(r["range_ratio"])}</td><td>{multiplier(r["volume_ratio"])}</td><td>{flag}</td></tr>')
        baselines.append(f'<tr><th scope="row">{esc(r["symbol"])}</th><td>{r["volume_1h"]:,.0f}</td>'
                         f'<td>{r["volume_baseline"]:,.0f}</td><td>{r["range_1h"]:.2f}%</td>'
                         f'<td>{r["range_baseline"]:.2f}%</td></tr>')
    errors = "".join(f"<li>{esc(s)}: unavailable ({esc(e)})</li>" for s, e in report["errors"].items())
    sources = "".join(f'<li><a href="{esc(r["source_url"], quote=True)}">{esc(r["symbol"])} exact request</a></li>' for r in report["assets"])
    template = (ROOT / "site-template.html").read_text(encoding="utf-8")
    fields = {"HOUR": esc(report["london_hour"]), "GENERATED": esc(report["generated_at"]), "CUTOFF": esc(report["hour_end"]),
              "CARDS": "".join(cards), "ROWS": "".join(trs), "FINDINGS": "".join(f"<li>{esc(x)}</li>" for x in findings(report["assets"])),
              "ERRORS": f'<aside class="notice">Partial coverage<ul>{errors}</ul></aside>' if errors else "",
              "COVERAGE": f'{len(report["assets"])}/{len(report["symbols"])}', "SOURCES": sources,
              "BASELINES": "".join(baselines), "SHARE_TEXT": esc("Session Brief — hour ending " + report["london_hour"] + "\n" +
                  "\n".join(findings(report["assets"])) + "\nBinance spot only; historical research. " +
                  f"Coverage: {len(report['assets'])}/{len(report['symbols'])}.\n" +
                  "https://novapixelgb.github.io/session-brief/\nThe link shows the latest published brief, which may change.")}
    for key, value in fields.items():
        template = template.replace("{{" + key + "}}", value)
    return template

def atomic_write(path, content):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)

def log_event(root, event):
    with (root / "state" / "activity.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, allow_nan=False) + "\n")

def generate(root=ROOT):
    config = load_config()
    for folder in ("state", "reports", "outbox", "site"):
        (root / folder).mkdir(exist_ok=True)
    now = datetime.now(UTC)
    cutoff = int(now.timestamp() * 1000) // HOUR * HOUR
    tag = now.strftime("%Y%m%dT%H%M%S%fZ")
    responses, assets, errors = {}, [], {}
    for symbol in config["symbols"]:
        url = BASE + "/api/v3/klines?" + urlencode({"symbol": symbol, "interval": "1h", "limit": 200, "endTime": cutoff - 1})
        try:
            raw = get_json(url)
            responses[symbol] = {"url": url, "retrieved_at": datetime.now(UTC).isoformat(), "candles": raw}
            assets.append(summarise(symbol, raw, cutoff))
        except (ValueError, TypeError, KeyError, IndexError, URLError, TimeoutError, RuntimeError) as exc:
            errors[symbol] = f"{type(exc).__name__}: {exc}"
    atomic_write(root / "state" / f"raw-{tag}.json", json.dumps(responses, indent=2, allow_nan=False))
    if not assets:
        log_event(root, {"at": now.isoformat(), "action": "fetch_failed", "errors": errors})
        raise RuntimeError("No fresh complete data; previous reports preserved. " + str(errors))
    end = datetime.fromtimestamp(cutoff / 1000, UTC)
    report = {"generated_at": now.isoformat(), "hour_end": end.isoformat(), "london_hour": london_label(end),
              "symbols": config["symbols"], "assets": assets, "errors": errors, "raw_file": f"state/raw-{tag}.json"}
    memo = markdown(report)
    page = render_site(report)
    atomic_write(root / "reports" / f"session-brief-{tag}.md", memo)
    atomic_write(root / "outbox" / "sample-brief.md", memo)
    atomic_write(root / "site" / "latest.md", memo)
    atomic_write(root / "site" / "latest.json", json.dumps(report, indent=2, allow_nan=False))
    atomic_write(root / "site" / "source-data.json", json.dumps(responses, indent=2, allow_nan=False))
    atomic_write(root / "site" / "index.html", page)
    log_event(root, {"at": now.isoformat(), "action": "generated_session_brief", "coverage": len(assets), "errors": errors,
                     "report": f"reports/session-brief-{tag}.md", "raw_file": report["raw_file"]})
    print(f"Generated Session Brief: {len(assets)}/{len(config['symbols'])} pairs; hour ending {report['london_hour']}")
    return report

def main():
    try:
        generate()
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
