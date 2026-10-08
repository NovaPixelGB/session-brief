# Launch operations

User authorised autonomous publication and automatic refreshes on 8 October 2026. GitHub account: NovaPixelGB. Public repository: https://github.com/NovaPixelGB/session-brief.

Deployment succeeded: https://github.com/NovaPixelGB/session-brief/actions/runs/37843828875. The public page, latest JSON and Atom feed were verified with HTTP 200; coverage is 3/3 pairs with no errors. The scheduled workflow refreshes the page every six hours at minute 17 UTC. It uses only standard public-repository runners and public exchange data. There are no model API calls, payments, exchange orders or wallet access.

Maintain Session Brief (automation ID maintain-session-brief) is ACTIVE, scheduled daily at 09:00 in the user's Europe/London timezone. It uses existing Codex usage allowance, checks health and actual reader feedback, and stays quiet when there is no actionable change. Creation confirms a saved schedule, not that a review has already run.

Readers can subscribe via `feed.xml` in an Atom-capable reader or provide feedback through the repository issue form. These are passive acquisition channels; no existing readers or revenue are assumed.

If the public data request fails, deployment stops and the previous page remains timestamped. Investigate source availability without circumventing restrictions. GitHub may delay schedules or disable them after 60 days of repository inactivity. No empty commits should be generated just to evade inactivity rules.
