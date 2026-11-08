# Fork Changes

Everything in this repo that is **not** upstream OrcaSlicer/OrcaSlicer 2.5.0 — what to re-check or
re-apply when moving to a newer upstream base. A maintenance checklist, not a user changelog.

`release/v2.5-u1` is the integration branch. It starts at tag `v2.5.0` (`40ecc66f78`, on
`upstream/release/v2.5.0`, not on `upstream/main`). The 2.4 line and its history live on
`release/v2.4-u1`; its `FORK_CHANGES.md` has the background of every change ported from there
(`git show release/v2.4-u1:FORK_CHANGES.md`). Change numbers in brackets, e.g. (2.4 #15), refer to it.

## How this list was built

Each change lives on its own topic branch, branched from `release/v2.5-u1` and merged back with
`--no-ff`. To list only our commits on a branch:

```bash
git log v2.5.0..<branch> --no-merges --format="%h|%an|%s"
```

Commits authored by `r.romantsov` are ours; others are upstream commits taken early (see change 4).
Re-run on every branch below after a rebase and diff against this file.

Rules: never merge `release/v2.4-u1` (or any integration branch) into a topic branch — bring single
commits with `git cherry-pick -x`, or re-apply by hand with `(ported from <hash>)` in the message.

## How to port a change to a new upstream base

Port each change by its intent, not by its code. Copying the code over and patching what breaks
reproduces the old base's assumptions on the new one: the 2.5 port of change 5 re-tied the filament sync
to `filament_id`, the very thing its 2.4 design had moved away from, and the first fix only patched a
symptom. For every change, before writing code:
1. **History.** Read its section here and in the previous base's `FORK_CHANGES.md`, then every commit
   behind it, follow-up fixes included (`git log`, commit messages). Write down the problem it solves,
   what each follow-up corrected and why, and what was decided against.
2. **The new base.** Check how upstream now handles the same problem: changed code and defaults in that
   area (`git log <old tag>..<new tag> -- <files>`), its design docs (`docs/HLSD/`), related upstream PRs,
   merged and open. The change may be upstream already, partly obsolete, or at odds with upstream's
   current design.
3. **Assumptions.** Check that what the change relies on still holds: config indexing, call order,
   defaults, which code path a printer actually takes (e.g. wipe tower type), firmware behaviour
   (U1 firmware dump: `/home/alternativ/Test/config/lava`).
4. **Profiles.** Check a profile delta against every preset that inherits it, not only the one it was
   made for (`tool_change_temprature_wait` in `fdm_U1.json` broke `0.4+0.6`, which has no change G-code).
   Compare with Snapmaker's own Orca fork (`github.com/Snapmaker/OrcaSlicer`, latest tag) for U1
   profile and firmware conventions.
5. **Adapt, then verify.** Re-implement the intent on the new base's terms, with a test that fails
   without the change. Record in this file what changed from the previous base and why.

## Branch map

| Branch | Change |
|---|---|
| `port25/fork-identity` | 1 |
| `port25/flatpak-ci` | 2 |
| `port25/u1-m220` | 3 |
| `port25/sequential-collision` | 4 |
| `port25/snapmaker-filament-sync` | 5 |
| `port25/purge-to-bin` | 6, 7 |
| `port25/u1-profiles` | 8 (and profile fixes of 6) |
| `port25/ci-test-pin` | 2 (test repo pin) |
| `port25/docs` | README, this file, `CLAUDE.md` fork section |

The `fixup!` commits on `port25/u1-m220` and `port25/purge-to-bin` were made after the first merge
(build and test fixes); they were not squashed because the branches were already merged.

## Changes

### 1. Fork identity — own versioning and update checks (2.4 #6)

- `src/libslic3r/AppConfig.cpp` — `VERSION_CHECK_URL` →
  `api.github.com/repos/alternativniy/OrcaSlicer-U1-Sync/releases/latest`. `PROFILE_UPDATE_URL` stays on
  upstream: other vendors' profiles keep coming from upstream. The Snapmaker bundle is kept out of
  reach by its version instead, see change 8.
- `src/slic3r/GUI/GUI_App.cpp` `check_new_version_sf()` — the version regex accepts dot-separated
  identifiers with embedded hyphens (`2.5.0-u1-1.0.0`). New in 2.5: upstream appends an updater query
  (installation id, OS info) and may sign it (`X-Orca-Sig`); both are now sent only when the URL is
  upstream's `check-version.orcaslicer.com`, not to GitHub. A single-release response
  (`releases/latest`) is parsed by upstream's code as is.
- `version.inc` — `SoftFever_VERSION` `2.5.0-u1-1.0.0`: upstream base, then the fork's own semver. The
  fork semver restarts at `1.0.0` on every new upstream base. Bump it only when the current version is
  already tagged (`git tag --list "v*u1*"`).
- Commit: `098ebf96e4` (ported from `85c6e7a3e9`).

### 2. Flatpak CI artifact path (2.4 #5)

`build_all.yml` upload / nightly deploy steps used `/__w/OrcaSlicer/OrcaSlicer/`, which only matches a
checkout named OrcaSlicer; now `${{ github.workspace }}`. It went missing once in a 2.4 merge — grep the
file for `/__w/` after every upstream merge.
- Commit: `6795b28c52` (ported from `f98502faef`).
- `build_orca.yml` CLI tests: `orca-test-repo` is pinned to `4674f68bbc78` (2026-10-26), its state at
  the v2.5.0 base. The test repo follows upstream main; on the 2.4 base its HEAD broke the fork's CI on
  version drift (`2d7fb76e6d`). **Re-pin on every new upstream base.** Commit `441e76c043`.

### 3. Snapmaker U1 speed override restored after the wipe tower purge (2.4 #8)

`WipeTowerWriter2` forces `M220 S100` before purging, but backed up / restored the user's override
(`M220 B` / `M220 R`) only on Marlin flavors. U1 runs klipper and supports both, so the override was
reset to 100 % at the first tool change. Gated on the printer model too (`is_snapmaker_u1()`, same check
as Snapmaker's own Orca fork; U1 firmware handles `M220 B/R` in `gcode_move.py`).
- New in 2.5: the type 1 tower (`WipeTower.cpp`) emits `M220 B/R` too (on 2.4 it was compiled out), on
  Marlin only, so it got the same U1 gate, set on the writer by `set_for_wipe_tower_writer()`.
- `src/libslic3r/GCode/WipeTower2.{hpp,cpp}`, `WipeTower.{hpp,cpp}`; test in
  `tests/fff_print/test_wipe_tower.cpp` for both tower types (checks the whole G-code: `M220 R` follows
  the tower region).
- Commits: `beea7195ac`, `87efc72060` (ported from `ce17f6a78a`), `0e35c07940` (type 1).
- Upstream #12782 (unified wipe tower pipeline) would need this re-applied.

### 4. By-object collision check from upstream main (2.4 #12)

Merged upstream after the 2.5.0 branch was cut, so not in `v2.5.0`. Cherry-picked from `upstream/main`:
- `a7833dd69b` ← `a30ca5e54a` #14987 — print tall objects later when the list order would collide.
- `4e67815be2` ← `8cdc68a6a0` #17217 — keep copies of one object in list order. Test conflict with 2.5's
  own by-layer test (#17232); both tests kept.
- `fb1035c1d9` ← `05a92cd0cf` #15544 — only the part of an object above the rod can collide with it.
- `e7de759993` ← `719fdcf4dd` #17286 — keep rotated copies in list order.

**Drop all four** once the upstream base includes them (2.5.1 / 2.6). Before that, check
`git log 719fdcf4dd..upstream/main -- src/libslic3r/Print.cpp` for further follow-ups.

### 5. Snapmaker filament sync matches user and vendor presets (2.4 #2)

`SnapmakerPrinterAgent` matched a tray by vendor, type and colour, but only among root presets, and the
match reached the GUI only as a `filament_id`, which `PresetBundle::sync_ams_list()` resolves to a root
preset again. User presets saved from a system one never matched.
- The agent considers every visible, compatible preset; finish sub-types (SnapSpeed, Silk, Wood, Matte,
  Marble, HF) count as the base type plus a preset-name hint. The match is decided by vendor, type and
  colour, never by `filament_id`; the agent remembers it per slot (`m_refined_filament_matches`).
- `IPrinterAgent::get_refined_filament_preset(slot_index)` (default: none) exposes it.
  `Sidebar::build_filament_ams_list()` stores it in the tray config as `filament_settings_id`, and
  `PresetBundle::sync_ams_list()` takes that preset over its `filament_id` lookup whenever it is
  compatible — also for a tray without a `filament_id`, which otherwise counts as empty. The 2.5 rule
  that keeps a slot's current user preset sharing the synced preset's `filament_id` (#16986) skips the
  presets an agent named (`agent_picks`), and holds as upstream's for everything else. The tray's `filament_id`
  (the match's own, else the type's generic one) only tags the tray, e.g. for change detection.
- On 2.4 the substitution happened in Plater after the sync; 2.5's sync (mapping, appended colours,
  mixed filaments) breaks the slot ↔ preset index assumption that needed, so it moved into the
  resolution itself.
- Files: `SnapmakerPrinterAgent.{hpp,cpp}`, `IPrinterAgent.hpp`, `Plater.cpp`, `PresetBundle.cpp`; test
  "Syncing the AMS takes the preset an agent named for the tray" in
  `tests/libslic3r/test_preset_bundle_loading.cpp`.
- Upstream bug fixed on the way: user presets loaded from the cloud inherited the parent's
  `filament_id` only when the cloud sent `"null"`, not when it sent an empty value. `Preset.cpp` now
  inherits on empty too (`4faaaa8faa`). The sync does not depend on it. Candidate for an upstream PR.
- Commits: `7126c51171` (ported from `c8cf1ab792`, `2628f52da5`), `4faaaa8faa`, `cc14d67a17`,
  `6d679a5180`. Checked on a real U1 (2026-11-09).
- **Fork-only, not for an upstream PR in this form.** Upstream's design (`docs/HLSD/filament_id.md`): the
  agent hands a `filament_id` to the shared matcher, which resolves it to a root preset; agents are meant
  to converge on that. SoftFever removed a per-preset (`setting_id`) path in `20388f846d`, and 2.5's
  Snapmaker agent matches root presets only on purpose. Upstream's answer for user presets: #16986 (keep
  the slot's user preset for the same filament, in 2.5) and open #16496 (detached user preset with its
  own id). Upstreamable pieces: the empty cloud `filament_id` fix on its own; the sub-type name hint is
  what open #15278 does — support that one instead of a duplicate.
- Conflict watch: upstream #12232, #15145 (+ #15179/#15180/#15183/#15185), #15278, #14760, #15196 touch
  the same code. Reconcile against whichever merges first.

### 6. `tool_change_temprature_wait` — optional M109 after a tool change (2.4 #14)

`OozePrevention::post_toolchange()` always emitted `M109 S<temp> T<n>`. Printer option (Multimaterial →
Advanced), default `true` = unchanged; `false` → `M104`. The key name keeps Snapmaker Orca's typo on
purpose, so their profiles and 3MFs load it — don't fix the spelling.
- `PrintConfig.{hpp,cpp}`, `GCode.cpp`, `Preset.cpp`, `Print.cpp`, `Tab.cpp`; profile: `"0"` in the
  `Snapmaker U1 (0.2/0.4/0.6/0.8 nozzle).json` printers, whose change G-code waits itself (`M109` before
  `T`, or the purge template at the bin) — as in Snapmaker's own profiles. **Not in `fdm_U1.json`**:
  `0.4+0.6` inherits from it, has no change G-code and needs the `M109` after the tool change (ooze
  prevention, standby −150 °C); with the key inherited it started the next tool cold (fixed in `09aaf46eda`;
  the same bug was on 2.4-u1).
- Commit: `f9a6c000ba` (cherry-pick of `b643a03e00`).

### 7. Purge to bin — tool changer purge into the purge bin instead of a prime tower (2.4 #15)

After each tool change, `GCode::purge_to_bin()` runs the printer's `purge_bin_gcode` template to purge
the new tool into the purge bin and wipe it. The slicer decides how much and how fast, the template does
the moves. Design, U1 template history and decisions: 2.4 `FORK_CHANGES.md` #15.
- Settings: process `purge_to_bin` (off), `purge_bin_speed_ratio`; filament `filament_purge_bin_volume`,
  `_first_volume`, `_dwell`; printer extruder `purge_bin_depart_retract` / `purge_bin_restart_extra`
  with filament overrides (Setting Overrides page); printer `purge_bin_gcode` (empty = off).
- Order in `set_extruder()`: … `post_toolchange()` → pressure advance → **purge to bin** →
  `m_last_pos_defined = false` → `synchronize_toolchange_position()` (picks up the XY the template left).
  `defer_temp_wait` is only set for the prime tower, which purge to bin excludes (asserted).
- 2.5 specifics: variant / override arrays (`retraction_length`, `purge_bin_*` retraction,
  `filament_max_volumetric_speed`) are read through `get_filament_config_index()`, plain filament arrays
  (`filament_purge_bin_*` volumes, dwell) by filament id. `purge_bin_depart_retract` /
  `purge_bin_restart_extra` are in `printer_options_with_variant_1` and `filament_options_with_variant`,
  like the tool change retraction. `Print::validate()` warnings use 2.5's multi-warning `warn()`.
- New in 2.5: after a pause (`CustomGCode::PausePrint`), a colour change, or custom G-code with a pause
  command (`PAUSE`, `M600`, `M601`, `M0`, `M1`, `M25`), every tool purges the first purge volume once more;
  the active tool counts as used. Idea from upstream #16934, not its code.
- U1 profiles (fork-local delta, re-check on every upstream profile sync): `fdm_U1.json` template,
  depart 6 / restart −0.3 (8 variant values); Snapmaker `fdm_filament_tpu.json` and
  `Snapmaker TPU 95A @U1 base.json` depart 2 / extra 0 via the filament override; the change G-code of
  `Snapmaker U1 (0.2/0.4/0.6/0.8 nozzle).json` skips its own `M109` and `SM_PRINT_PREEXTRUDE_FILAMENT` when
  purge to bin is active (`0.4+0.6` has no change G-code of its own). `Snapmaker.json` `02.04.00.21`.
- ru translations hand-inserted (`# AI Translated`), no full gettext resync.
- Tests: `tests/fff_print/test_purge_to_bin.cpp`, 8 cases. Pitfalls: build the config with
  `multifilament_config()` **and** give each filament its own config slot
  (`filament_extruder_variant` × 2, `filament_self_index` `1,2`), else every per-filament override reads
  column 0; set `single_extruder_multi_material` 0; keep the prime tower inside the 200×200 test bed;
  compare only the tool change commands (slicing is not byte-stable run to run).
- Commits: `f3f941c11a`, `72a1bb3f36`, fixups `5bdea2f486` … `e42c99c109` (ported from `a317c07f5c`,
  `db2964be9d`, `383e133af7`, `643240acb0`, `0c72de004f`, `16b574c919`, `def5db478a`, `652dfa683a`).
- Not yet printed with the 2.5 build.

**Before an upstream PR** (after the 2.5 branch has been printed with): re-check #16934 first; the PR
description compares the two approaches (ours: per-filament mm³ volumes, depart retraction with filament
overrides, writer state set in code, fan / E mode / feedrate restore, pause handling, printed on U1;
theirs: idle-time step sizing). Strip the ru `.po` entries. Ship change 6 with it or as its own PR.
Decided against, don't re-research: a 2.5 plugin (no seam inside G-code generation), a tool-change plugin
seam in 2.5.0, on-printer purge timing (needs Snapmaker/u1-klipper changes that don't get merged).

### 8. The fork owns the Snapmaker profile bundle

2.5.0 turned vendor profile updates on for everyone (upstream #17289, no setting; only stealth mode or a
`dev` version keep them off). An upstream Snapmaker bundle with a higher version would be offered as a
configuration update and, if accepted, replace the fork's U1 profiles (purge to bin template, change
G-code, tool change wait).
- `Snapmaker.json` `version` is `99.00.00.01`: the app folds a four-part version into
  `major.minor.(patch*100+build)` and compares that, so major 99 is out of upstream's reach; the rest
  counts the fork's profile releases. Bump the last component on every fork profile change.
- **On every upstream merge or sync: diff upstream's `resources/profiles/Snapmaker*` against ours and merge
  their changes in by hand**, keeping the fork's deltas (changes 6, 7, this section). Last synced with
  upstream `02.04.00.20` (v2.5.0). The same rule is in `CLAUDE.md`.
- Fork deltas in the U1 profiles besides 6 and 7 (`09aaf46eda`):
  - change G-code, print by object: the lift is absolute (`G90`, default `max_print_height`), as in
    Snapmaker's 20261003 change G-code; upstream's 20260607 sends the absolute height as a relative move.
  - `0.4+0.6`: `extruder_clearance_height_to_rod` 27.5 / `extruder_clearance_radius` 72.5 like the other U1
    printers (upstream #15544 measured the rod); it inherited 36 / 65.
- Not done: `0.4+0.6` is a different profile line on `fdm_U1` (own `PRINT_START`, no change G-code, no Z lift
  on tool change, generic retraction). Aligning it with the official U1 profiles is a profile design
  decision, left open.
- Commits: `09aaf46eda`, `4e99dcbc82`.
- **Alternatives to the version lock** (discussed 2026-11-09, parked; the lock stays for now). Orca can't
  layer one vendor bundle on another (a machine preset only inherits within its own vendor; the only
  cross-vendor base is `OrcaFilamentLibrary` for filaments), so any hybrid needs work:
  - *Upstream the deltas* (preferred long term): the U1 profile fixes (by-object `G90`, `0.4+0.6`, where
    `tool_change_temprature_wait` lives) as their own PR, purge to bin with its U1 template as another.
    With no deltas left, drop the 99 version and take upstream's updates like everyone else.
  - *Overlay in code*: a small fork file of the keys we set, applied over the loaded Snapmaker presets
    wherever they came from (resources or an OTA bundle). Key-level deltas are easy; the change G-code
    is one string, so it can only be replaced whole — keep the hash of the upstream value it was based
    on and skip it with a log warning when upstream's changes. About a day of work, one more fork delta.
  - *Own update server*: `PROFILE_UPDATE_URL` to a small proxy (Snapmaker → a fork release asset, other
    vendors → upstream), plus a CI job that re-applies our deltas to upstream's bundle. Needs
    infrastructure; conflicts still need a human. Too much for this fork.

## Deferred — may come back

- **Nozzle picker + Mixed Nozzle Sizes** (2.4 #13, upstream PR #14400, still open). Not ported: the 2.5
  sidebar UI changed a lot and the picker needs real adaptation. Material when it comes back: PR head
  (`gh pr view 14400 --repo OrcaSlicer/OrcaSlicer --json headRefOid,updatedAt`; was `0bd92b7628`), our
  follow-ups on `release/v2.4-u1` — `a552887dce` (locale-independent diameters, needed for comma-decimal
  UIs), `7d008a8400` (collapsible section, checkmark, fixed grid), `316d6925ff` (ru strings). Until then
  U1 users switch nozzle size via the `Snapmaker U1 (x nozzle)` printer profiles.
- **U1 filename before slicing** (2.4 follow-up `893d8d4951`). Not needed on 2.5: upstream #15950 added
  the post-slice half (`PrintStatistics::initial_no_support_tool`), and Export / Send are only offered
  after slicing, which includes the G-code export, so `Print::finished()` holds and the real value is
  used. Checked in the code, not run. If a placeholder parser error ever shows before slicing, port the
  `Print::output_filename()` part.

## Taken upstream or dropped in 2.5 (verified, don't re-port)

- No sparse layers toolchange fix (2.4 #1) — our PR #15441, in 2.5.0 (`39408fa1f2`). The final purge
  stays mid-air (`m_final_purge.print_z`), as intended.
- No sparse layers collision detection (2.4 #1) — superseded by upstream #15485
  (`compacted_wipe_tower_clearance_valid()`); our PR #15442 closed.
- Toolchange retraction in the GUI (2.4 #3) — upstream #15039 (`6312caaf13`). PR #13509 obsolete.
- TPU filament tuning across vendors (2.4 #4) — dropped (user decision): #15039 sets
  `retract_length_toolchange` 2 for toolchanger printers, the TPU override was a no-op on U1.
- U1 bed temps 100 °C (2.4 #9) — #15483 in 2.5.0. U1 filename filament (2.4 #10) — #15349 in 2.5.0.
- Snapmaker `filament_vendor` on type bases (2.4 #11) — PR #15482 closed, fixed in `WebGuideDialog.cpp`.
- CI backports (NSIS retry #15768, Win ARM64 CMake 4.3 #16052, Flatpak deps cache #15501) — in 2.5.0.
  The `orca-test-repo` pin (`2d7fb76e6d`) was for the 2.4.2 base; if CLI CI fails on version drift,
  pin to the test-repo commit matching 2.5.0.

## Verification state of the integrated branch

State on 2026-11-09 (`release/v2.5-u1` with all of the above), Release build:
- full `ctest`: only `cli_malformed_input` fails (also fails on plain `v2.5.0`). Under `-j8` the
  MoonrakerPrinterAgent `Stopping the status stream sends the printer a close frame` test has failed at
  random before (passes on its own, untouched by us).
- `scripts/run_clang_tidy.sh -b v2.5.0` clean.
- `scripts/check_profile.sh -v Snapmaker --validator build/src/Release/OrcaSlicer_profile_validator`:
  `profile_tool`, `version_bump`, `legacy_compat` and `validate_slice` (92 slices) pass. The other
  validator checks fail only on other vendors' presets that `-v` leaves unloaded (no Snapmaker errors).
  Rebuild the validator target first and pass `--validator`: the script otherwise picks the first one it
  finds, possibly a stale build. By-object change G-code checked by slicing with a temporary
  `printing_by_object_gcode` on the U1 0.4 printer.
- Real U1: filament sync works. Not yet: a print with purge to bin on the 2.5 build, the
  `orca-test-repo` CLI suite at the pinned commit.

## Upstream PR watchlist (state on 2026-11-08)

Re-check before touching the same code (`gh pr view <n> --repo OrcaSlicer/OrcaSlicer --json state,mergedAt`).
- Taken early from `upstream/main`: #14987, #15544, #17217, #17286 (change 4).
- Deferred: #14400 (nozzle picker).
- Competing with change 7, don't take: #16934 (purge bucket sized by idle time), open.
- Same code as change 5, don't take yet: #12232, #15145 (+ stacked PRs), #15278 (sub-type in name, same
  idea as ours), #14760, #15196, #16300 (Snapmaker sync fixes), #16985 (lane_data ids for Snapmaker),
  #16822 (multi-colour spools), #16477 (`filament_subtype` setting), #16496 (own id for detached user
  presets — upstream's way for user presets).
- #12782 unified wipe tower pipeline — would need change 3 re-applied.
- #13286 abandoned, #13509 obsolete.
