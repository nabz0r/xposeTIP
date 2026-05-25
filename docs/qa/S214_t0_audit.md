# S214 T0 audit-before-fix: empty_or_too_long source verification

**Question.** How did 2,446 username findings with `validator_reason='empty_or_too_long'`
land in the DB given the S159 writer guard at `scraper_scanner.py:140-145`?

**S159 commit:** `80acd69` — `feat(S159): username taxonomy correction — backend writer
fix + DB backfill + frontend defense` — 2026-05-22 21:19 +0200.

## source_kind distribution

| source_kind | count |
|---|---|
| scraper_engine | 2446 |

100% scraper_engine — no direct emitters in this bucket.

## Top 10 modules by count

| module | count |
|---|---|
| imgur_profile | 185 |
| twitch_profile | 185 |
| keybase_profile | 170 |
| threads_profile | 166 |
| npm_maintainer | 153 |
| anilist_profile | 152 |
| kaggle_profile | 152 |
| pypi_profile | 152 |
| pinterest_profile | 151 |
| wayback_linkedin_user | 149 |

All scraper_engine modules — none are direct-emitter bypass paths.

## created_at range

- oldest: 2026-03-21
- newest: 2026-05-24

The "newest 2026-05-24" reading initially appeared to violate the decision rule.
Subdivision shows it is NOT an empty-string post-guard miss — it is the >40-char
half of the validator's `empty_or_too_long` rule (which catches BOTH empty AND
>40-char in one label).

## Empty vs >40-char era split

| subgroup | pre-S159 | post-S159 |
|---|---|---|
| `LENGTH(value) = 0 OR NULL` | 2440 | **0** |
| `LENGTH(value) > 40`        | 6    | 5 |

- **All 2,440 empty-string rows are pre-S159** — S159 guard works as designed.
- 5 post-S159 >40-char rows are page-title bleeds from `linktree_profile`
  (3 rows) and `bandcamp_profile` (2 rows). Example values:
  - `Slevin Official Music - Listen to songs on YouTube, Spotify | Check for Videos o`
  - `Razberry Razorblade&#39;s collection | Bandcamp`

  These are same class as the deferred-to-S216 `telegram_profile` extraction bug.
  The S159 guard does not block them because the value is non-empty — it would
  require a wider validator-fail-at-write-time guard (separate sprint).

## Decision

Per the literal S214 spec rule: "If newest `created_at` of empty-string rows is
OLDER than the S159 commit → proceed to T1." Newest empty-string row is
**pre-S159** → PROCEED with the cleanup migration.

The 5 post-S159 page-title rows will be swept by this migration (they're in the
same trust bucket) and will re-accumulate slowly until S216 fixes the
linktree/bandcamp extraction config. Acceptable per the spec's explicit
deferral of `telegram_profile`-class extraction fixes to S216.
