# S213 — Username Findings Audit

- **Run UTC:** 20260525T000444Z
- **Workspace filter:** `(all)`
- **Total username findings:** 7645
- **Targets touched:** 229
- **Workspaces touched:** 16
- **Validator-fail:** 2940 (38.5%)
- **Low-trust (verified=False AND cross_verified=0):** 3262 (42.7%)

## By module

| module | total | validator_fail | fail_% | top_reason |
|---|---|---|---|---|
| wayback_domain | 124 | 124 | 100.0% | empty_or_too_long |
| rdap_domain | 117 | 117 | 100.0% | empty_or_too_long |
| bandcamp_profile | 18 | 18 | 100.0% | too_many_spaces |
| linkedin_profile | 11 | 11 | 100.0% | too_many_spaces |
| hashnode_profile | 8 | 8 | 100.0% | paren_pattern |
| viewdns_reverse_whois | 2 | 2 | 100.0% | empty_or_too_long |
| breachdirectory | 1 | 1 | 100.0% | empty_or_too_long |
| aboutme_profile | 21 | 20 | 95.2% | too_many_spaces |
| linktree_profile | 38 | 36 | 94.7% | pipe_in_title |
| replit_profile | 75 | 69 | 92.0% | title_pattern |
| telegram_profile | 220 | 189 | 85.9% | too_many_spaces |
| xposedornot_scraper | 76 | 60 | 78.9% | empty_or_too_long |
| tumblr_profile | 24 | 17 | 70.8% | empty_or_too_long |
| nationalize | 101 | 66 | 65.3% | empty_or_too_long |
| genderize | 98 | 63 | 64.3% | empty_or_too_long |
| agify | 95 | 61 | 64.2% | empty_or_too_long |
| runescape_profile | 11 | 7 | 63.6% | empty_or_too_long |
| threads_profile | 280 | 175 | 62.5% | empty_or_too_long |
| twitch_profile | 304 | 187 | 61.5% | empty_or_too_long |
| imgur_profile | 305 | 187 | 61.3% | empty_or_too_long |
| keybase_profile | 292 | 173 | 59.2% | empty_or_too_long |
| dribbble_profile | 22 | 13 | 59.1% | empty_or_too_long |
| strava_profile | 210 | 120 | 57.1% | empty_or_too_long |
| wayback_linkedin_user | 265 | 151 | 57.0% | empty_or_too_long |
| npm_maintainer | 273 | 155 | 56.8% | empty_or_too_long |
| anilist_profile | 272 | 154 | 56.6% | empty_or_too_long |
| kaggle_profile | 272 | 154 | 56.6% | empty_or_too_long |
| pypi_profile | 272 | 154 | 56.6% | empty_or_too_long |
| pinterest_profile | 271 | 153 | 56.5% | empty_or_too_long |
| aboutme_check | 11 | 6 | 54.5% | empty_or_too_long |
| bluesky_profile | 28 | 15 | 53.6% | multi_dot_handle |
| lastfm_profile | 36 | 19 | 52.8% | empty_or_too_long |
| gitlab_profile | 266 | 140 | 52.6% | empty_or_too_long |
| wayback_profile | 18 | 9 | 50.0% | empty_or_too_long |
| disqus_profile | 45 | 21 | 46.7% | empty_or_too_long |
| wayback_github | 9 | 4 | 44.4% | empty_or_too_long |
| wayback_facebook | 12 | 5 | 41.7% | empty_or_too_long |
| wayback_linkedin | 12 | 5 | 41.7% | empty_or_too_long |
| behance_profile | 28 | 11 | 39.3% | empty_or_too_long |
| wayback_twitter | 13 | 5 | 38.5% | empty_or_too_long |
| github_timezone | 44 | 16 | 36.4% | empty_or_too_long |
| github_scraper | 45 | 16 | 35.6% | empty_or_too_long |
| github_gists_user | 31 | 5 | 16.1% | empty_or_too_long |
| wayback_instagram | 7 | 1 | 14.3% | empty_or_too_long |
| mastodon_search | 26 | 3 | 11.5% | empty_or_too_long |
| packagist_profile | 9 | 1 | 11.1% | empty_or_too_long |
| snapchat_profile | 57 | 6 | 10.5% | no_alnum |
| devto_profile | 10 | 1 | 10.0% | too_many_spaces |
| vimeo_profile | 18 | 1 | 5.6% | too_many_spaces |
| huggingface_profile | 21 | 1 | 4.8% | too_many_spaces |
| medium_profile | 47 | 1 | 2.1% | too_many_spaces |
| intelligence | 1875 | 3 | 0.2% | multi_dot_handle |
| roblox_profile | 197 | 0 | 0.0% | — |
| hackernoon_profile | 55 | 0 | 0.0% | — |
| duolingo_profile | 46 | 0 | 0.0% | — |
| reddit_profile | 40 | 0 | 0.0% | — |
| chesscom_profile | 36 | 0 | 0.0% | — |
| github_user_api | 33 | 0 | 0.0% | — |
| stackoverflow_search | 32 | 0 | 0.0% | — |
| dockerhub_profile | 30 | 0 | 0.0% | — |
| kofi_profile | 29 | 0 | 0.0% | — |
| gumroad_profile | 27 | 0 | 0.0% | — |
| paypal_profile | 27 | 0 | 0.0% | — |
| letterboxd_profile | 25 | 0 | 0.0% | — |
| mixcloud_profile | 24 | 0 | 0.0% | — |
| flickr_profile | 23 | 0 | 0.0% | — |
| lichess_profile | 22 | 0 | 0.0% | — |
| ifttt_profile | 19 | 0 | 0.0% | — |
| soundcloud_search | 18 | 0 | 0.0% | — |
| steam_community_profile | 18 | 0 | 0.0% | — |
| steam_profile | 18 | 0 | 0.0% | — |
| calendly_profile | 15 | 0 | 0.0% | — |
| hackernews_profile | 14 | 0 | 0.0% | — |
| myanimelist_profile | 14 | 0 | 0.0% | — |
| pastebin_user | 13 | 0 | 0.0% | — |
| gravatar_scraper | 11 | 0 | 0.0% | — |
| giphy_profile | 10 | 0 | 0.0% | — |
| speedrun_profile | 10 | 0 | 0.0% | — |
| buymeacoffee_profile | 9 | 0 | 0.0% | — |
| codecademy_profile | 9 | 0 | 0.0% | — |
| instructables_profile | 9 | 0 | 0.0% | — |
| codeberg_profile | 7 | 0 | 0.0% | — |
| codewars_profile | 7 | 0 | 0.0% | — |
| wattpad_profile | 7 | 0 | 0.0% | — |
| weebly_profile | 7 | 0 | 0.0% | — |
| reverbnation_profile | 5 | 0 | 0.0% | — |
| rubygems_profile | 5 | 0 | 0.0% | — |
| steemit_profile | 5 | 0 | 0.0% | — |
| wikidot_profile | 5 | 0 | 0.0% | — |
| hack_md_profile | 4 | 0 | 0.0% | — |
| github_deep | 3 | 0 | 0.0% | — |
| gravatar_email_lookup | 2 | 0 | 0.0% | — |
| issuu_profile | 2 | 0 | 0.0% | — |
| opencollective_profile | 2 | 0 | 0.0% | — |
| speakerdeck_profile | 2 | 0 | 0.0% | — |
| blogger_by_gaia_id_profile | 1 | 0 | 0.0% | — |
| gcal_public | 1 | 0 | 0.0% | — |
| istock_profile | 1 | 0 | 0.0% | — |

## By validator reason

| reason | count | example_values (top 3) |
|---|---|---|
| empty_or_too_long | 2446 | ``, `Razberry Razorblade&#39;s collection | Bandcamp`, `Hayden McGovern&#39;s collection | Bandcamp` |
| too_many_spaces | 200 | `Akim Khalilov on about.me`, `Vitina Mary Dsouza on about.me`, `Reves D’or on about.me` |
| title_pattern | 116 | `Sign Up`, `Telegram: Contact @akim`, `Telegram: Contact @stani` |
| fqdn_tld | 77 | `maersk.com`, `threatconnect.com`, `mistral.ai` |
| multi_dot_handle | 57 | `aymen.zerni.nss`, `guillaume.a.perrin`, `dsouza.bsky.social` |
| pipe_in_title | 23 | `Jsjones | Linktree`, `lpopa | Linktree`, `dsouza | Linktree` |
| paren_pattern | 14 | `Subhashis (@slevin)`, `David Souza (@dsouza)`, `Hayden Foote (@hayden)` |
| no_alnum | 6 | ` `, `💙` |
| html_entity | 1 | `PHELIP D&#39;SOUZA` |

## Trust signal cross-tabs

Rows = `validator_pass`, Columns = `cross_verified >= 1`

| validator_pass | cross_verified >= 1 | cross_verified = 0 |
|---|---|---|
| True | 2774 | 1931 |
| False | 120 | 2820 |

## name_scraper_engine focus (Bug 12 candidates)

- Total: **0**
- Validator-fail: **0**

Sample (up to 10):

_(no name_scraper_engine username findings present)_
