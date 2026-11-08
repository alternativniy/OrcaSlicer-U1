@AGENTS.md

## This fork (OrcaSlicer-U1-Sync)

Not upstream OrcaSlicer: a fork for the Snapmaker U1. Every change that is not upstream's is listed in
`FORK_CHANGES.md` — read it before porting, merging upstream, or touching a listed change.

- **The fork owns the Snapmaker profile bundle.** `resources/profiles/Snapmaker.json` is versioned
  `99.xx.xx.xx` so upstream's vendor profile updates (on for everyone since 2.5.0) never replace it.
  On every upstream merge or sync, diff upstream's `resources/profiles/Snapmaker*` against ours and
  merge their changes in by hand, keeping the fork's deltas listed in `FORK_CHANGES.md`; then bump the
  last component of our version. Never take upstream's version number.
- Port a change by its intent, not by its code: read its history in `FORK_CHANGES.md` and the commits
  first, and check how the new upstream base handles the same problem.
