@AGENTS.md

## This fork (OrcaSlicer-U1)

Not upstream OrcaSlicer: a fork for the Snapmaker U1. Every change that is not upstream's is listed in
`FORK_CHANGES.md` — read it before porting, merging upstream, or touching a listed change.

- **The fork owns the Snapmaker profile bundle.** `resources/profiles/Snapmaker.json` is versioned
  `99.xx.xx.xx` so upstream's vendor profile updates (on for everyone since 2.5.0) never replace it.
  On every upstream merge or sync, diff upstream's `resources/profiles/Snapmaker*` against ours and
  merge their changes in by hand, keeping the fork's deltas listed in `FORK_CHANGES.md`; then bump the
  last component of our version. Never take upstream's version number.
- Port a change to a new upstream base by its intent, not by its code: follow "How to port a change to
  a new upstream base" in `FORK_CHANGES.md` (history and follow-up fixes first, then how upstream
  handles the same problem now, then the change's assumptions and every inheriting profile).
