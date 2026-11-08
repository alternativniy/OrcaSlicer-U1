# Fork Changes — port plan 2.4 → 2.5.0

This branch, `release/v2.5-u1`, is the fork's integration branch for upstream **2.5.0**. It starts at
tag `v2.5.0` (`40ecc66f78`, on `upstream/release/v2.5.0`, **not** on `upstream/main`).

This file is the port plan: which fork changes from `release/v2.4-u1` still have to be carried over,
which are already in upstream 2.5.0, and which are dropped. The full description of every change
(the why, the design, the test history) is in `FORK_CHANGES.md` on `release/v2.4-u1`:

```bash
git show release/v2.4-u1:FORK_CHANGES.md
```

Change numbers (#1 … #15) below are the same as in that file. When a port item is done, mark it done
here (commit hashes on `release/v2.5-u1`). When the whole port is done, turn this file back into a
regular fork-changes list (see "Final step").

Everything below was checked on 2026-11-08 against tag `v2.5.0`: `git grep` on the tag, PR states via
`gh pr view`, and a trial `git cherry-pick --no-commit` of every fork commit onto `v2.5.0` in a
throwaway worktree. The conflict lists below come from that trial.

## Rules for the agents doing the port

- **Never merge `release/v2.4-u1` (or `feature/purge-to-bin`) into this branch** or into a port branch.
  Bring over single commits with `git cherry-pick -x <hash>` (keeps authorship and the source hash),
  and re-apply by hand where a commit doesn't cherry-pick. When a commit is re-applied by hand, add
  `(ported from <hash>)` to the commit message.
- One topic branch per port item, branched from `release/v2.5-u1`, named `port25/<topic>` (names
  are given per item below). Merge it back into `release/v2.5-u1` with `--no-ff` when it builds and
  its tests pass. Items marked independent can run in parallel.
- Upstream commits (author not `r.romantsov`) are taken from `upstream/main` or the PR head, not from
  our old cherry-picks on `release/v2.4-u1`, so the code matches what upstream actually merged.
- Build Release (`cmake --build build --config Release --target all --`) and run the affected test
  suites (`ctest --test-dir ./tests/fff_print -C Release`, `ctest --test-dir ./tests/libslic3r -C Release`).
  Report pre-existing failures as such, checked against plain `v2.5.0`.
- Follow `AGENTS.md`: include what you use (`scripts/run_clang_tidy.sh` on changed lines), translatable
  string rules, `SetSizerAndFit`.
- **Profiles:** every change under `resources/profiles/<Vendor>/` bumps `version` in
  `resources/profiles/<Vendor>.json`. Upstream `Snapmaker.json` is at `02.04.00.20` in 2.5.0. The
  first port that touches Snapmaker profiles bumps it to `02.04.00.21`; later ones go up from whatever
  `release/v2.5-u1` has at that moment. **Never** take the number from a 2.4 commit (`.08` … `.14`).
  After profile changes, sync the local package: `rsync -a resources/ build/package/resources/`.
- `localization/i18n/ru/OrcaSlicer_ru.po`: the 2.4 branch hand-inserted msgids for the fork's new strings.
  Keep doing that (no `--full` gettext resync, it drags in unrelated upstream string drift), new source
  files go into `localization/i18n/list.txt`. Check with
  `msgfmt --check-format --check-header -o /tmp/ru.mo localization/i18n/ru/OrcaSlicer_ru.po`.
- No pushes, no PRs, no GitHub comments — the user does that.
- Don't bump the fork version per item; it is done once, in P1.

## Summary

| # | Change | Verdict | Port item |
|---|---|---|---|
| 1 | No sparse layers toolchange fix | **Drop** — in 2.5.0 (our PR #15441) | — |
| 1 | No sparse layers collision detection | **Drop** — superseded by upstream #15485 (in 2.5.0) | — |
| 1 | Final purge relocation | **Drop** — was reverted on purpose, 2.5.0 keeps mid-air | — |
| 2 | Snapmaker filament profile sync | **Port, by hand** | P5 |
| 3 | Toolchange retraction in the GUI | **Drop** — in 2.5.0 via upstream #15039 | — |
| 4 | TPU filament tuning, 46 vendor files | **Drop** — user decision 2026-11-08, see "Dropped" | — |
| 5 | Flatpak CI artifact path | **Port** | P2 |
| 6 | Fork identity: update URL, version regex, version | **Port** | P1 |
| 7 | README "About this fork" | **Port, rewrite** | P10 |
| 8 | U1 M220 B/R after wipe tower purge | **Port** | P3 |
| 9 | U1 bed temps cap 100 °C | **Drop** — in 2.5.0 (#15483) | — |
| 10 | U1 filename respects filament selection | **Drop** — #15349 in 2.5.0; pre-slice follow-up believed covered, see "Deferred" | — |
| 11 | Snapmaker `filament_vendor` on type bases | **Drop** — PR #15482 closed, fixed upstream in code | — |
| 12 | By-object collision: geometry order + rod-only height | **Port from upstream/main** (#14987, #15544, #17217 — merged to main after the 2.5.0 branch) | P4 |
| 13 | Nozzle picker + Mixed Nozzle Sizes (#14400) | **Deferred** — sidebar UI changed in 2.5, needs adaptation | — |
| 14 | `tool_change_temprature_wait` | **Port** | P8 |
| 15 | Purge to bin | **Port, by hand** (depends on P8) | P8 |
| — | CI backports (NSIS retry, Win ARM64 CMake 4.3, Flatpak deps cache) | **Drop** — all three upstream commits are in 2.5.0 | — |
| — | CI: pin `orca-test-repo` to 2.4.2-era commit (`2d7fb76e6d`) | **Drop** — pin was for the 2.4.2 base | — |
| — | `FORK_CHANGES.md` docs commits, Snapmaker.json bump commits, version bumps | **Drop** — rewritten here / redone in P1 | — |

## Dropped — evidence

Keep this section so nobody re-ports these.

- **#1 fix** (`839fb636e6`, `53a2314d12` + reverts `b6ec7366b9`, `f792045bd6`): upstream merged our
  PR #15441 as `39408fa1f2`, in `v2.5.0`. `restore_layer_z_before_toolchange` /
  `deretraction_from_wipe_tower_generator` are in `GCode.cpp`, `WipeTower.cpp`, `WipeTower2.cpp`; the
  `defer_compacted_descend` guard is there (`GCode.cpp:1169`). `finalize()` still targets
  `m_final_purge.print_z` (`GCode.cpp:2173`), i.e. the mid-air final purge we wanted. Nothing to do.
- **#1 detection** (`0be65a114b`, `5b32911159`): superseded by upstream #15485
  (`Print::compacted_wipe_tower_clearance_valid()` / `validate_compacted_wipe_tower_clearance()`,
  `Print.cpp:1431`/`1499`). Our PR #15442 was closed. The known gap (tower freezes when toolchanges stop,
  detector silent) still exists upstream; not ours to fix here.
- **#3** (`73bf782e84`): upstream #15039 (`6312caaf13`, in 2.5.0) added
  `filament_retract_length_toolchange` / `filament_retract_restart_extra_toolchange` to the filament
  override keys, the Setting Overrides page, `Preset.cpp`, and gave `retract_length_toolchange` a real
  label/tooltip. Upstream PR #13509, the source of our version, is still open but obsolete for us.
- **#9** (cap bed temps): upstream `5496883493` (#15483), in 2.5.0. All four bases are at 100 °C.
- **#10 profile part**: upstream `f31e610b72` (#15349), in 2.5.0; `fdm_process_U1_common.json` uses
  `filament_type[initial_no_support_extruder]`.
- **#11** (`filament_vendor` on type bases): PR #15482 was closed by SoftFever — the bug was in
  `WebGuideDialog.cpp`, fixed there in code; Snapmaker type bases don't need the key. Do **not**
  re-add it. Only verify (part of P10 smoke test): Add/Remove Filaments for Snapmaker U1 shows the
  ABS/ASA/PETG/PLA presets.
- **CI backports** `6ab094a94a` (upstream `29858ba925`, #15768), `6d412f20ce` (`8bf7b73141`, #16052),
  `e2f339d39c` (`e6501bb1ce`, #15501): all three upstream commits are ancestors of `v2.5.0`.
- **`2d7fb76e6d`** (pin `orca-test-repo` to `0dfd8df4`): the pin matched the 2.4.2 base. 2.5.0 is what
  the current test repo is calibrated against. If the CLI/golden-slice CI job fails on version drift
  later, pin to the test-repo commit matching 2.5.0, don't reuse `0dfd8df4`.
- **#4 TPU tuning** (`770f6d442e`, 46 vendor TPU files): dropped (user decision 2026-11-08). Upstream
  #15039 exposes the setting and sets `retract_length_toolchange` 2 at the printer level for
  toolchanger profiles (`fdm_U1.json` included), so the TPU override of 2 is a no-op on U1. Dropped with
  it: the Snapmaker TPU `filament_retraction_length` 0.5 → 1.5 and the 20/20 retraction speeds on other
  vendors. Not affected: the purge-to-bin TPU overrides (`filament_purge_bin_*`) are part of P8.
- **Snapmaker U1 printer/process profiles** in general track upstream (official U1 support). Only the
  fork-local deltas listed in P8 are ours.

## Port items

Recommended order: **P1 → P2 → P3 → P4 → P5 → P8 → P10.** P2–P5 are independent of each other and
can run in parallel after P1. P8 comes after P1 (version). P6, P7, P9 are not part of the port (see
"Deferred" and "Dropped"); the numbers are kept so references stay stable.

### P1. Fork identity and version (#6) — branch `port25/fork-identity`

Source: `85c6e7a3e9` (+ version bumps `80773db9fa`, `b579a39dbe`). Trial cherry-pick: conflict in
`version.inc` only.

- `src/libslic3r/AppConfig.cpp:61` — `VERSION_CHECK_URL` →
  `https://api.github.com/repos/alternativniy/OrcaSlicer-U1-Sync/releases/latest`. Leave
  `PROFILE_UPDATE_URL` (line 62) on upstream.
- `src/slic3r/GUI/GUI_App.cpp` — `check_new_version_sf()` (`:6605`), the regex at `:6655` — same
  replacement as in `85c6e7a3e9` (dot-separated identifiers with embedded hyphens), keep the
  `Orca(U1):` comment.
- **New in 2.5.0, check:** `check_new_version_sf()` now appends an updater query string
  (`build_updater_query()`: installation id, version, OS, arch, OS info) to `version_check_url` and
  can attach an `X-Orca-Sig` header (`maybe_attach_updater_signature()`, only when
  `ORCA_UPDATER_SIG_KEY` is set at build time — fork CI doesn't set it). With our URL this sends the
  query to `api.github.com`. GitHub ignores unknown query params, so it works, but it leaks the
  installation id to GitHub for nothing. Skip the query string (and the signature) when the URL is
  not upstream's `check-version.orcaslicer.com` — small guarded change, comment it as `Orca(U1)`.
  Also check how the response is parsed now: `releases/latest` returns one object, while the code
  iterates releases (`consider_release`) — make sure a single-object response still works (it did in
  2.4); if not, switch the URL to `.../releases` (array) and verify prerelease handling.
- `version.inc` — `SoftFever_VERSION` → **`2.5.0-u1-1.0.0`** (user decision 2026-11-08: the fork's own
  semver restarts at 1.0.0 on every new upstream base). Compares higher than every `2.4.2-u1-*` tag.
  Don't touch `SLIC3R_VERSION`.
- Test: build, run, Help → Check for updates (needs a published fork release to compare against; at
  minimum confirm no crash and the log shows the GitHub URL).

### P2. Flatpak CI artifact path (#5) — branch `port25/flatpak-ci`

Source: `f98502faef`. Trial cherry-pick conflicts in `.github/workflows/build_all.yml` (context moved).
In `v2.5.0` the hardcoded path is still there: `build_all.yml:467` (`upload-artifact` `path:`) and
`:472` (`asset_path:`). Replace `/__w/OrcaSlicer/OrcaSlicer/` with `${{ github.workspace }}/` in both.
Grep the whole file for `/__w/` afterwards. Nothing else from the old commit.

### P3. U1 speed override restored after wipe tower purge (#8) — branch `port25/u1-m220`

Source: `ce17f6a78a`. Conflict in `src/libslic3r/GCode/WipeTower2.cpp` (context). 2.5.0 still gates
`speed_override_backup()` / `speed_override_restore()` (`WipeTower2.cpp:677-692`) on Marlin flavors
only. Re-apply: `m_printer_model` threaded through the `WipeTower2` and `WipeTowerWriter2`
constructors, `is_snapmaker_u1()` (`icontains "Snapmaker"` && `"U1"`), and the two `M220` lines
gated on it alongside the Marlin check. Check where `WipeTower2` is constructed in 2.5.0 (`Print.cpp`
/ `GCode.cpp`) — upstream #15485 changed wipe tower code, the constructor call site may have moved.
Don't touch `WipeTower.cpp` (Type1). Test: slice a U1 2-colour print with a prime tower (Type2), the
G-code has `M220 B` before and `M220 R` after each tower purge; a Marlin printer is unchanged.

### P4. By-object collision check (#12) — branch `port25/sequential-collision`

Do **not** cherry-pick our old `635608bc61` / `7464edcd13`. Upstream merged the PRs into `main` after
the 2.5.0 branch was cut (not in `v2.5.0`):
1. `a30ca5e54a` — By object: print tall objects later when the list order would collide (#14987).
   Trial: applies cleanly on `v2.5.0` (`Print.cpp`, `Print.hpp`, `tests/fff_print/test_print.cpp`).
2. `05a92cd0cf` — only the part of an object above the rod can collide with it (#15544). Trial:
   conflict in `Print.cpp` after (1). Upstream main had other `Print.cpp` commits between the two,
   among them `8cdc68a6a0` (#17217, see 3) — resolve by hand keeping upstream's final shape.
3. `8cdc68a6a0` — Sequential print: keep copies of one object in their list order (#17217), a
   follow-up fix to the same function, also not in 2.5.0. Take it (after 1, before or with 2 — try
   `a30ca5e54a`, `8cdc68a6a0`, `05a92cd0cf` in that order first).
Run `ctest --test-dir ./tests/fff_print -C Release` (the PRs bring their own test cases).
When upstream ships 2.5.1/2.6 with these, they become redundant — note that in the final list.

### P5. Snapmaker filament profile sync (#2) — branch `port25/snapmaker-filament-sync`

Source: `c8cf1ab792`, `2628f52da5` (ours, no upstream PR). Trial conflicts: `IPrinterAgent.hpp`, then
`SnapmakerPrinterAgent.cpp`. Upstream refactored the printer agent infrastructure in between
(#15710 `a5413efc37`, plus include clean-ups #16071/#16220), so re-apply by hand.
- 2.5.0 still has the problem: `find_closest_color_preset_by_vendor_and_type()`
  (`SnapmakerPrinterAgent.cpp:29`) only considers root presets (`get_preset_base(p) == &p`), and
  the match survives `PresetBundle::sync_ams_list()` only as `filament_id`.
- Re-add `IPrinterAgent::get_refined_filament_preset(int slot_index)` (default empty),
  `SnapmakerPrinterAgent::m_refined_filament_matches`, the user-preset / original-manufacturer
  matching from both commits, and the `Plater.cpp` hook that substitutes the refined preset after the
  generic resolution. Find the current `sync_ams_list` call site in `Plater.cpp` / wherever #15710
  moved it.
- Conflict watch: PRs #12232, #15145, #15278, #14760 (all open) touch the same code. Not merged as of
  2026-11-08; re-check before starting.
- Test: needs a real U1 (user). Agent: build + confirm other agents (Moonraker, Qidi, Creality) are
  untouched (default implementation returns `""`).

### P8. `tool_change_temprature_wait` (#14) + Purge to bin (#15) — branch `port25/purge-to-bin`

The detailed research for this item is in the 2.4 file, section **"#15 → Port to 2.5.0 — TODO"**
(`git show release/v2.4-u1:FORK_CHANGES.md`). Read it in full; key points repeated here.

Commits, in order:
1. `b643a03e00` — `tool_change_temprature_wait` (#14). Use this one, not its `-x` copy `8f3f137c17`.
   Trial conflicts: `Snapmaker U1 (0.4 nozzle).json`, `Preset.cpp`, `Tab.cpp`. **Keep the
   `temprature` spelling** (Snapmaker Orca compatibility). `OozePrevention::post_toolchange()`
   (`GCode.cpp:516`) is unchanged in 2.5.0. Profile: `"tool_change_temprature_wait": "0"` in
   `fdm_U1.json`; check whether 2.5.0's `Snapmaker U1 (0.4 nozzle).json` still carries the key as a
   stray duplicate, remove it if so.
2. Purge to bin, from `feature/purge-to-bin`: `a317c07f5c`, `db2964be9d`, `383e133af7`, `643240acb0`,
   `0c72de004f`, `16b574c919`, `def5db478a`, `652dfa683a`. Skip `cdad6f09a2` (Snapmaker.json bump)
   and `8f3f137c17` (duplicate of 1). Trial conflicts for `a317c07f5c`: `GCode.cpp`, `GCode.hpp`,
   `GCodeProcessor.hpp`, `Preset.cpp`, `Print.cpp`, `Tab.cpp`, `tests/fff_print/CMakeLists.txt` —
   expect to re-apply `GCode.cpp` by hand. Squashing the 8 into fewer commits is fine.

2.5.0 specifics (verified against the tag):
- `GCode::set_extruder()` (`GCode.cpp:~10990`) has `bool defer_temp_wait` and a toolchange position
  sync. Insert `purge_to_bin()` **after** `set_filament_pressure_advance(...)` and **before**
  `m_last_pos_defined = false` / `synchronize_toolchange_position(...)`. `defer_temp_wait` is only set
  for the wipe tower and purge to bin requires the tower off; add an assert or a test for that.
- All filament-indexed reads in `purge_to_bin()` go through `get_filament_config_index()`
  (`filament_purge_bin_volume`, `_first_volume`, `_dwell`, `retraction_length`,
  `purge_bin_depart_retract`, `purge_bin_restart_extra`, `filament_max_volumetric_speed`). The
  first-use set `m_purge_bin_used_filaments` stays keyed by filament id.
- Upstream 2.5.0 has no `purge_to_bin`, `tool_change_temprature_wait` or `toolchange_prime` key — no
  name clash. `; EXTERNAL_PURGE` and `;_FORCE_RESUME_FAN_SPEED` still exist.
- The old merge conflict next to #3's override keys is gone (#3 is upstream now, P-list "Dropped");
  add the `filament_purge_bin_*` override keys next to upstream's toolchange keys in
  `filament_extruder_override_keys`, `Preset.cpp`, `Tab.cpp` (`:4530`, `:4648`).
- **New behaviour to add** (agreed with the user): after a pause / colour change
  (`CustomGCode::PausePrint` / `ColorChange`, around `GCode.cpp:5714`; also custom G-code containing
  `PAUSE`, `M600`, `M0`, `M1`, `M25`), the next purge of every tool uses
  `filament_purge_bin_first_volume`: clear `m_purge_bin_used_filaments`, re-insert the active tool.
  Add a test case. Idea credited to upstream PR #16934 (not their code).
- Tests: `tests/fff_print/test_purge_to_bin.cpp` (7 cases + the pause case). `Print::m_isBBLPrinter`
  is initialized in 2.5.0 (old pitfall gone); test configs still default to
  `single_extruder_multi_material` — set it explicitly; compare only the tool-change commands.
- Profiles (fork-local delta): `fdm_U1.json` (`purge_bin_gcode` template, `purge_bin_depart_retract`
  6, `purge_bin_restart_extra` −0.3, `tool_change_temprature_wait` 0), Snapmaker
  `fdm_filament_tpu.json` + `Snapmaker TPU 95A @U1 base.json` (depart 2 / extra 0 overrides),
  `Snapmaker U1 (0.4 nozzle).json` change G-code (no `M109` before `T` and no
  `SM_PRINT_PREEXTRUDE_FILAMENT` when purge to bin is active). Upstream rewrote U1 profiles between
  2.4 and 2.5 (`fdm_U1.json` now inherits `fdm_toolchanger`, `retract_length_toolchange` 2) — re-apply
  the deltas on top of upstream's current files, don't overwrite them with 2.4 versions.
  `Snapmaker.json` → next after current (`02.04.00.21` if P8 is the first Snapmaker profile change).
- ru translations: carry the hand-inserted msgids from the purge-to-bin commits.
- Before starting, re-check PR #16934 (`gh pr view 16934 --repo OrcaSlicer/OrcaSlicer --json
  state,mergedAt`). Open as of 2026-11-08. If merged, stop and ask the user.
- Verification the user does: print on U1 (PETG black/white, then PLA+PETG).

### P10. README, docs, final list — branch `port25/docs`

- README: re-write the "About this fork" section (source `0bb8923e1a`, `5bdf7aca8a`; trial conflict
  in `README.md`) for what the fork carries on 2.5: no sparse layers fix is upstream now (mention as
  contributed upstream), list purge to bin, `tool_change_temprature_wait`, U1 M220,
  Snapmaker filament sync, independent update channel.
- Smoke test of the integrated branch: full Release build, full `ctest`, start the app, U1 profile
  loads, Add/Remove Filaments shows Snapmaker U1 presets (#11 check), slice a 2-colour U1 plate with
  and without prime tower.

## Deferred — not ported now, may come back later

### P7. Nozzle picker + Mixed Nozzle Sizes (#13) — deferred (user decision 2026-11-08)

Not ported to 2.5 for now: the sidebar UI changed a lot in 2.5, the picker needs real adaptation, not
a cherry-pick. If it comes back, the material is:
- Upstream PR #14400 (open, `CONFLICTING`, head `0bd92b7628`, author ni4223, last update 2026-09-26).
  Check for a newer head first (`gh pr view 14400 --repo OrcaSlicer/OrcaSlicer --json headRefOid,updatedAt`).
- Our follow-ups on `release/v2.4-u1`: `a552887dce` (locale-independent diameter parse/format — needed
  for comma-decimal UIs like Russian), `7d008a8400` (collapsible section, checkmark instead of Apply,
  fixed grid), `316d6925ff` (ru strings + `list.txt`).
- Trial cherry-pick of `0bd92b7628` on `v2.5.0` conflicts in `ConfigManipulation.cpp/.hpp`,
  `Plater.cpp`, `tests/libslic3r/CMakeLists.txt`.
- Until then 2.5 users switch U1 nozzle size by picking the `Snapmaker U1 (x nozzle)` printer profile.

### P6. U1 filename before slicing (#10 follow-up `893d8d4951`) — believed covered, not ported

Upstream 2.5.0 has `PrintStatistics::initial_no_support_tool` (set in `GCode.cpp:4941`, exported as
`initial_no_support_extruder` in `PrintStatistics::config()`, `Print.cpp:5844`), i.e. the post-slice
half of our fix. Our commit also had a pre-slice part in `Print::output_filename()` (the
`placeholders()` value is a string, and the U1 `filename_format` uses it as an array index). Expected
to be fine on 2.5; not ported. If the suggested file name before slicing (Export G-code / Send to
printer on a U1 profile) shows a placeholder parser error, port only the `output_filename()` part of
`893d8d4951`.

## Final step

When P1–P5, P8, P10 are merged: rewrite this file into the regular fork-changes format (as on
`release/v2.4-u1`): "How this list was built" (with `git merge-base v2.5.0 <branch>` instead of
`origin/main`), branch map for the `port25/*` branches, one section per live change with commits on
this branch, "Not fork changes", and the watchlist below. Keep the "Dropped — evidence" section as
"Taken upstream / dropped in 2.5".

## Upstream PR watchlist (state on 2026-11-08)

Re-check before every port item that touches the same code
(`gh pr view <n> --repo OrcaSlicer/OrcaSlicer --json state,mergedAt,headRefOid`).

- **Merged to `upstream/main`, not in 2.5.0, taken in P4:** #14987 (`a30ca5e54a`), #15544
  (`05a92cd0cf`), #17217 (`8cdc68a6a0`). Drop our copies once a newer upstream base includes them.
- **Open, deferred:** #14400 (nozzle picker, P7 — see "Deferred").
- **Open, obsolete for us:** #13509 (toolchange retraction GUI — covered by merged #15039).
- **Competing with #15, do not take:** #16934 (purge bucket sized by idle time). Open, see P8.
- **Same code as #2 (P5), do not take yet:** #12232, #15145 (+ stacked #15179, #15180, #15183, #15185),
  #15278, #14760, #15196. All open. Reconcile P5 against whichever merges first.
- **#13286** — abandoned (superseded by #15145), ignore.
- **#12782** — unified WipeTower pipeline. Open. If it lands, P3 (`WipeTower2.cpp` M220) has to be
  re-applied on the new pipeline.
