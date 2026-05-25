# S228 — DB Hygiene Audit

_Generated: 2026-05-25T19:07:28.493938+00:00_

_Pattern: S159 / S213 / S224 audit-before-fix. Read-only._


## Top-line summary

- `legal_record`: **58.0%** malformed in sample (29/50, total 738 in DB)
- `username`: **38.0%** malformed in sample (19/50, total 5,045 in DB)
- **143** orphan targets (no findings)
- **112** targets stale (last_scanned > 30d)
- Phone aggregation drift detected (max delta 26)
- Crypto aggregation drift detected (max delta 18)
- **1** modules emit under multiple categories (>=10% split)


## Block A — Indicator value shape


| indicator_type | total in DB | sampled | malformed | rate % | top reasons |

|---|---:|---:|---:|---:|---|

| `legal_record` | 738 | 50 | 29 | 58.0 | no_alpha=29 |
| `username` | 5,045 | 50 | 19 | 38.0 | username_is_domain=13, username_has_separator=6 |
| `domain` | 4,307 | 50 | 0 | 0.0 |  |
| `email` | 2,887 | 50 | 0 | 0.0 |  |
| `social_url` | 2,729 | 50 | 0 | 0.0 |  |
| `ip` | 964 | 50 | 0 | 0.0 |  |
| `name` | 201 | 50 | 0 | 0.0 |  |
| `media_mention` | 154 | 50 | 0 | 0.0 |  |
| `behavioral_profile` | 127 | 50 | 0 | 0.0 |  |
| `first_name` | 75 | 50 | 0 | 0.0 |  |
| `phone` | 27 | 27 | 0 | 0.0 |  |
| `crypto_wallet` | 19 | 19 | 0 | 0.0 |  |

### Sample malformed rows (top 5 per type)


**`username`**


| value (<=80c) | module | reason | finding_id |

|---|---|---|---|

| `sidonie.stire` | gitlab_profile | username_is_domain | cb9b616f-8bcf-4345-a83b-04028cbaf233 |
| `bruno.diogo` | snapchat_profile | username_is_domain | 0e3d7b91-7c60-42ea-8698-c805cf3d8c31 |
| `avocatv.elkaim` | intelligence | username_is_domain | aa013fb3-dd42-488e-9a29-c9f95e35e337 |
| `Jon Marlow` | dockerhub_profile | username_has_separator | 76e7ecd6-80bc-4686-8e25-0c5dc44f365d |
| `allesandro.nervegna` | intelligence | username_is_domain | 8785ac7e-eb01-47f4-99c7-31a6104b511c |


**`legal_record`**


| value (<=80c) | module | reason | finding_id |

|---|---|---|---|

| `3133` | bodacc_search | no_alpha | eb1d774e-3c36-4145-a840-81017976303a |
| `977` | bodacc_search | no_alpha | 9086022f-a747-48f7-ad75-4afb80300842 |
| `1309` | bodacc_search | no_alpha | 7f0e5a4f-24c4-46b0-90ea-ad3a2b81c344 |
| `1533` | bodacc_search | no_alpha | 93f22aa5-0b37-49a7-ada0-138e9062d564 |
| `99-34278` | courtlistener_search | no_alpha | cf92be57-4056-4232-bf66-33da8267a0cc |



## Block B — Targets hygiene


- Orphan targets (no findings): **143**

- Placeholder-name targets (sample-capped at 50): **0**

- Stale (last_scanned > 30d): **112**

- Status=pending BUT last_scanned set: **0**

- Workspace+email dup groups: **0**


### Orphan samples


| email | display_name | status | created_at |
|---|---|---|---|

| garret.kelly@gmail.com | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| 1337void@gmail.com | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| spacebarisforlosers@gmail.com | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| sll.droid@gmail.com | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| newlibertystandard@gmail.com | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| richard.birgersson@mensa.se | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| alexi.sabunir@gmail.com | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| xerofx@gmx.com | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| all.me.are.born.free@gmail.com | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| theymos@mm.st | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| nphyxx@gmail.com | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| fergalish@yahoo.co.uk | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| lectormatic@gmail.com | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| elnora.crater@gmail.com | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| kind@gmx.at | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| ens2222ayia@gmail.com | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| bitcoin@hush.com | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| bdimych@narod.ru | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| eman.ortego@gmail.com | — | pending | 2026-05-23 23:23:00.795139+00:00 |
| solar@heliacal.net | — | pending | 2026-05-23 23:23:00.795139+00:00 |



## Block C — Profile aggregation drift


- Targets with non-null profile_data: **233**

- Targets with profile_data but missing primary_name: **30**

- Targets with profile_data but empty social_profiles: **3**


### Phone drift (raw findings vs `profile_data->phones`, top 20)


| email | raw | aggregated | delta |
|---|---:|---:|---:|

| gnienlnaha@yahoo.fr | 27 | 1 | 26 |


### Crypto wallets drift (raw vs `profile_data->crypto_wallets`, top 20)


| email | raw | aggregated | delta |
|---|---:|---:|---:|

| gnienlnaha@yahoo.fr | 19 | 1 | 18 |



## Block D — Module/category coherence + BFP substrate


### D1 — Modules with category split >=10% on >=2 categories (1 flagged)


| module | total findings | splits |
|---|---:|---|

| `bodacc_search` | 306 | formal_records=69.3%, public_exposure=30.7% |


### D2 — BFP behavioral_hash_v1 distribution


- Total hashed targets: **155** / **61** distinct hashes


| hash prefix (16c) | count |
|---|---:|

| `f9a5400a00000000` | 37 |
| `14e0de8400000000` | 20 |
| `f9a5400a00000000` | 6 |
| `f9a5400a00000000` | 6 |
| `f9a5400a00000000` | 6 |
| `14e0de8400000000` | 5 |
| `f9a5400a00000000` | 4 |
| `3abb873e00000000` | 3 |
| `f9a5400a00000000` | 3 |
| `c1d6015d00000000` | 3 |
| `14e0de8400000000` | 3 |
| `14e0de8400000000` | 3 |
| `14e0de8400000000` | 2 |
| `86e8fe3800000000` | 2 |
| `3abb873e00000000` | 2 |
| `c291c37100000000` | 2 |
| `f9a5400a00000000` | 2 |
| `f9a5400a00000000` | 2 |
| `9fb8098400000000` | 2 |
| `6d8e1f7700000000` | 1 |

### D3 — Finding cross_verification_count buckets


| bucket | count |
|---|---:|

| 0 | 7,141 |
| 1 | 1,170 |
| 2-4 | 2,329 |
| 5+ | 7,178 |

### D4 — BFP claims integrity


- Total claims: **1,312**

- NULL/empty claim_hash: **0**

- NULL/empty claim_value: **0**


| claim_type | count |
|---|---:|

| `username` | 404 |
| `ip` | 345 |
| `email` | 236 |
| `domain` | 234 |
| `name` | 65 |
| `first_name` | 25 |
| `social_url` | 1 |
| `phone` | 1 |
| `crypto_wallet` | 1 |

### D5 — `data.scraper` vs `module` coherence


- Sample size: **200** (random)

- Mismatches: **0**



## Actionable backlog candidates (ranked by anomaly volume)


- Prune 143 orphan targets (no findings)
- Stabilize category emission on 1 modules
- Cleanup malformed `legal_record` findings (58.0% rate in sample, est. 428 rows)
- Cleanup malformed `username` findings (38.0% rate in sample, est. 1,917 rows)
- Investigate phone aggregation drift on 1 targets
- Investigate crypto aggregation drift on 1 targets
