# PS-043 – Metro Fare and Smart Card Engine with Zone Fares, Peak Pricing and Penalties — Sample Data Pack

Prepared by 10 SECONDS for Team T117.

## Files

| File | What it holds | Row count |
|---|---|---|
| `lines.csv` | 3 metro lines | 3 data rows |
| `stations.csv` | 45 stations with zone (1 = city centre) and interchange flag | 45 data rows |
| `fare_matrix.csv` | Zone fare by number of zones crossed | 5 data rows |
| `holidays.csv` | Listed holidays (entirely off-peak, 10% off) | 3 data rows |
| `cards.csv` | 30 smart cards (STANDARD, STUDENT, SENIOR, TOURIST_PASS) with opening balance and auto-reload settings | 30 data rows |
| `commands.txt` | 400 tap events over 4 days (12 mismatches, 6 overstays) plus top-ups, a block, surrenders and print requests | 443 command lines (excluding comments) |

Row numbers quoted below are 1-based data-row numbers (the header is row 0). Line numbers for `commands.txt` are physical line numbers including comment lines.

## Column reference

Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals with 2 places (no commas, no symbol); percentages as plain numbers (12.5 means 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix. An empty cell means "not applicable" and only appears in columns whose notes say so.

### `lines.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| line_id | string | LN-xxx | — | — |
| line_name | string | — | — | — |

### `stations.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| station_id | string | STN-nn | — | primary key |
| station_name | string | — | — | — |
| line_id | string | — | lines.csv | primary line |
| zone | int | — | 1-5 | 1 = city centre |
| interchange | bool | — | — | — |
| interchange_line_id | string | — | lines.csv | second line served at an interchange |

### `fare_matrix.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| zones_crossed | int | — | 0-4 | /zone_out - zone_in/ |
| fare | decimal | Rs | — | token fare before card discounts; + Rs 5 if the journey touches zone 1 |

### `holidays.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| holiday_date | date | — | — | — |
| holiday_name | string | — | — | — |

### `cards.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| card_id | string | MC-nnnnnnnn | — | primary key |
| card_type | enum | — | STANDARD, STUDENT, SENIOR, TOURIST_PASS | — |
| balance | decimal | Rs | — | opening balance at 2026-10-01 00:00 |
| auto_reload | bool | — | — | — |
| linked_account | string | — | — | auto-reload source; empty when auto_reload is false |
| issued_date | date | — | — | — |
| pass_days | int | — | 1, 3 | TOURIST_PASS only |
| status | enum | — | ACTIVE | — |

## Command file format

`commands.txt` holds one command per line in the form `COMMAND_NAME|arg1|arg2|...`. Commands must be processed strictly in file order. Lines starting with `#` are comments and blank lines are ignored. An empty argument (two adjacent `|`) means "not supplied". Every command used in this pack:

| Command | Arguments (in order) | Meaning |
|---|---|---|
| `TAP_IN` | `card_id|ts|station_id` | Gate entry (refuse with LOW_BALANCE below the minimum balance) |
| `TAP_OUT` | `card_id|ts|station_id` | Gate exit: compute fare or penalty, apply caps, auto-reload |
| `TOPUP` | `card_id|ts|amount` | Manual top-up |
| `BLOCK` | `card_id|ts` | Card reported lost; journeys after this are rejected |
| `SURRENDER` | `card_id|ts` | Card returned for refund |
| `PRINT_HISTORY` | `card_id` | Print the card's journey history |
| `PRINT_REVENUE` | `date` | Print revenue by station for the date |

## Planted scenarios

Every edge case in the brief, mapped to the exact record where it occurs, followed by extra traps.

- **EC-01 Tap-in at exactly 10:00 on a weekday**
  - Tap-in at 10:00:00 Thursday (peak window 08:00–10:00 has ended?) vs the same trip tapped in at 09:59:59 — commands.txt line 42 (`TAP_IN|MC-42949707|2026-10-01 10:00:00|STN-11`); commands.txt line 46 (`TAP_OUT|MC-42949707|2026-10-01 10:31:00|STN-26`); commands.txt line 41 (`TAP_IN|MC-91062504|2026-10-01 09:59:59|STN-11`); commands.txt line 45 (`TAP_OUT|MC-91062504|2026-10-01 10:30:00|STN-26`)
- **EC-02 STUDENT card at 07:59 vs 08:00**
  - Two STUDENT cards on the same trip: 07:59:00 tap-in (off-peak, 50% off) vs 08:00:00 (peak, full fare + 20%) — commands.txt line 10 (`TAP_IN|MC-20755918|2026-10-01 07:59:00|STN-18`); commands.txt line 21 (`TAP_OUT|MC-20755918|2026-10-01 08:40:00|STN-24`); commands.txt line 11 (`TAP_IN|MC-60553219|2026-10-01 08:00:00|STN-18`); commands.txt line 24 (`TAP_OUT|MC-60553219|2026-10-01 08:41:00|STN-24`)
- **EC-03 Journey of 90 minutes 00 seconds for a 2-zone trip**
  - Journey 2026-10-03 11:15:00 -> 2026-10-03 12:45:00 = exactly 90 min 00 s between zone 2 and zone 2 (<= 2 zones crossed) -> not an overstay — commands.txt line 272 (`TAP_IN|MC-92142603|2026-10-03 11:15:00|STN-05`); commands.txt line 282 (`TAP_OUT|MC-92142603|2026-10-03 12:45:00|STN-10`)
- **EC-04 Same-station exit at exactly 15 minutes**
  - Exit at the entry station after exactly 15 min 00 s (free 'changed mind'?) and another after 15 min 01 s (minimum fare + Rs 10) — commands.txt line 218 (`TAP_IN|MC-84539312|2026-10-02 18:10:00|STN-09`); commands.txt line 221 (`TAP_OUT|MC-84539312|2026-10-02 18:25:00|STN-09`); commands.txt line 264 (`TAP_IN|MC-78749124|2026-10-03 09:40:00|STN-19`); commands.txt line 267 (`TAP_OUT|MC-78749124|2026-10-03 09:55:01|STN-19`)
- **EC-05 Daily cap reached mid-journey (fare would push past Rs 150)**
  - STANDARD card on Thursday: Majestic (zone 1) <-> Bommasandra (zone 5) at 08:05 (peak), 12:30 (off-peak) and 17:10 (peak) -> the third fare would push the day past Rs 150 -> only the remainder is charged; the 20:30 trip is Rs 0 but still logged — commands.txt line 15 (`TAP_IN|MC-20281406|2026-10-01 08:05:00|STN-07`); commands.txt line 31 (`TAP_OUT|MC-20281406|2026-10-01 09:05:00|STN-45`); commands.txt line 56 (`TAP_IN|MC-20281406|2026-10-01 12:30:00|STN-45`); commands.txt line 64 (`TAP_OUT|MC-20281406|2026-10-01 13:30:00|STN-07`); commands.txt line 94 (`TAP_IN|MC-20281406|2026-10-01 17:10:00|STN-07`); commands.txt line 108 (`TAP_OUT|MC-20281406|2026-10-01 18:10:00|STN-45`); commands.txt line 130 (`TAP_IN|MC-20281406|2026-10-01 20:30:00|STN-45`); commands.txt line 132 (`TAP_OUT|MC-20281406|2026-10-01 20:50:00|STN-44`)
- **EC-06 Auto-reload triggered twice, then a third low-balance tap-out**
  - STUDENT card with auto-reload, opening balance 101.00, riding Majestic <-> Bommasandra back-to-back on Thursday from 06:00: the first tap-out takes it below Rs 100 (reload 1), and after 13 more trips it drops below Rs 100 again (reload 2, the daily maximum). NOTE: with Rs 500 reloads and the brief's fares a third same-day low-balance tap-out cannot be reached; the card's Friday trip tests that the counter resets per day — cards.csv row 20 (MC-59220720); commands.txt line 3 (`TAP_IN|MC-59220720|2026-10-01 06:00:00|STN-07`); commands.txt line 4 (`TAP_OUT|MC-59220720|2026-10-01 06:56:00|STN-45`); commands.txt line 119 (`TAP_IN|MC-59220720|2026-10-01 19:00:00|STN-45`); commands.txt line 127 (`TAP_OUT|MC-59220720|2026-10-01 19:56:00|STN-07`); commands.txt line 162 (`TAP_IN|MC-59220720|2026-10-02 09:00:00|STN-07`); commands.txt line 170 (`TAP_OUT|MC-59220720|2026-10-02 09:56:00|STN-45`)
- **EC-07 TOURIST_PASS first tapped at 23:50**
  - 1-day TOURIST_PASS first tapped at 23:50 on 2026-10-02 -> valid to 23:59 that day; the tap-out at 00:18 is after midnight and the next morning's trip is outside validity — cards.csv row 28 (MC-20315228); commands.txt line 241 (`TAP_IN|MC-20315228|2026-10-02 23:50:00|STN-07`); commands.txt line 243 (`TAP_OUT|MC-20315228|2026-10-03 00:18:00|STN-28`); commands.txt line 262 (`TAP_IN|MC-20315228|2026-10-03 09:30:00|STN-28`); commands.txt line 270 (`TAP_OUT|MC-20315228|2026-10-03 10:00:00|STN-09`)
- **EC-08 Card blocked between tap-in and tap-out**
  - Card tapped in 16:05, reported lost (BLOCK) at 16:20, tap-out 16:52 -> journey after the block time is rejected; SURRENDER later refunds the balance as at the block time minus Rs 50 deposit — commands.txt line 296 (`TAP_IN|MC-83817111|2026-10-03 16:05:00|STN-13`); commands.txt line 299 (`TAP_OUT|MC-83817111|2026-10-03 16:52:00|STN-28`); commands.txt line 298 (`BLOCK|MC-83817111|2026-10-03 16:20:00`); commands.txt line 302 (`SURRENDER|MC-83817111|2026-10-03 17:30:00`)
- **Extra traps (not in the brief, but realistic):**
  - STANDARD card with 55.00: passes the Rs 50 gate check at 08:40, the peak zone-5 -> zone-1 trip costs more than 55 and takes it negative; the two evening tap-ins are refused (LOW_BALANCE) until the TOPUP — cards.csv row 17 (MC-23526517); commands.txt line 22 (`TAP_IN|MC-23526517|2026-10-01 08:40:00|STN-39`); commands.txt line 34 (`TAP_OUT|MC-23526517|2026-10-01 09:22:00|STN-07`); commands.txt line 107 (`TAP_IN|MC-23526517|2026-10-01 18:05:00|STN-07`); commands.txt line 109 (`TAP_IN|MC-23526517|2026-10-01 18:12:00|STN-07`); commands.txt line 114 (`TOPUP|MC-23526517|2026-10-01 18:30:00|200.00`)
  - SENIOR card from a zone-1 station: 30% off applies to the zone fare, never to the Rs 5 zone-1 supplement — commands.txt line 50 (`TAP_IN|MC-47742025|2026-10-01 11:00:00|STN-08`); commands.txt line 52 (`TAP_OUT|MC-47742025|2026-10-01 11:40:00|STN-45`)
  - TAP_OUT with no matching TAP_IN (6 cards) -> Rs 55 maximum-fare penalty — commands.txt line 90 (`TAP_OUT|MC-22490601|2026-10-01 16:36:00|STN-32`); commands.txt line 174 (`TAP_OUT|MC-20762202|2026-10-02 11:09:00|STN-40`); commands.txt line 300 (`TAP_OUT|MC-74403905|2026-10-03 17:13:00|STN-38`)
  - TAP_IN while a previous TAP_IN is still open (6 cards) -> old journey closed at maximum fare, new journey starts — commands.txt line 208 (`TAP_IN|MC-19508913|2026-10-02 17:25:00|STN-03`); commands.txt line 265 (`TAP_IN|MC-22210414|2026-10-03 09:41:00|STN-35`); commands.txt line 380 (`TAP_IN|MC-65013815|2026-10-04 16:45:00|STN-44`)
  - 6 overstays: journeys longer than 90 min (<= 2 zones) or 120 min (> 2 zones) -> Rs 50 penalty — commands.txt line 297 (`TAP_IN|MC-47396008|2026-10-03 16:18:00|STN-30`); commands.txt line 311 (`TAP_OUT|MC-47396008|2026-10-03 18:22:00|STN-32`); commands.txt line 393 (`TAP_IN|MC-18002709|2026-10-04 18:30:00|STN-12`); commands.txt line 409 (`TAP_OUT|MC-18002709|2026-10-04 20:33:00|STN-21`); commands.txt line 117 (`TAP_IN|MC-40631110|2026-10-01 18:50:00|STN-08`); commands.txt line 134 (`TAP_OUT|MC-40631110|2026-10-01 21:12:00|STN-34`)

## What is NOT in this pack

Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-nn). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation

Produce these CSV files (header row, same conventions as above, rows sorted as stated). Where the brief is silent on a format detail the choice below is binding for evaluation.

### `journeys.csv`

One row per TAP_IN / TAP_OUT outcome, in command order.

Columns, in order: `card_id`, `ts`, `event`, `station_id`, `entry_station_id`, `zones_crossed`, `fare_before_cap`, `fare_charged`, `penalty`, `auto_reload_amount`, `balance_after`, `result`, `rule_ids`

### `card_history.csv`

One row per completed or penalised journey per PRINT_HISTORY.

Columns, in order: `card_id`, `journey_no`, `tap_in_ts`, `tap_in_station`, `tap_out_ts`, `tap_out_station`, `fare`, `penalty`, `balance_after`

### `station_revenue.csv`

One row per station per PRINT_REVENUE (revenue booked at the exit station; penalties included).

Columns, in order: `date`, `station_id`, `journeys`, `fare_revenue`, `penalty_revenue`, `total`

Binding choices: `result` is OK, REFUSED_LOW_BALANCE, REJECTED_BLOCKED, PENALTY or PASS; peak uplift rounded to the rupee; balances to the paisa; journey ids in card_history.csv are 1-based per card in tap order.
