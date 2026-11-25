#!/usr/bin/env python3
"""Keep one set of Actions caches for the branch being built (Orca(U1) fork CI).

Every run saves a new ccache entry (`ccache-<leg>-<run id>-<attempt>`), a changed dependency set saves a
new deps cache, and the repository holds only 10 GB, so stale entries push out the ones the next build
wants. After a build this script deletes, on the ref being built, every cache but the newest of its
family, and every cache of other branches except the default branch's (its caches serve any new branch
as a fallback). Pull request, tag and unrecognised caches are left alone.

Needs the `gh` CLI and a token that may write Actions (GH_TOKEN).
"""
import argparse
import json
import os
import re
import subprocess
import sys

# The part of a cache key that stays the same from build to build; the rest is a run or content id.
FAMILIES = [
    re.compile(r"^(ccache-.+)-\d+-\d+$"),
    re.compile(r"^(.+-cache-orcaslicer_deps-build)-[0-9a-f]{64}$"),
    re.compile(r"^(flatpak-builder-[^-]+)-[0-9a-f]{40,}$"),
]


def family_of(key):
    for pattern in FAMILIES:
        match = pattern.match(key)
        if match:
            return match.group(1)
    return None


def plan(caches, ref, default_branch):
    """Returns [(cache, reason)] to delete. `caches` are the API's objects."""
    doomed = []
    newest = {}
    for cache in caches:
        if cache["ref"] == ref:
            family = family_of(cache["key"])
            if family:
                newest.setdefault(family, []).append(cache)
        elif cache["ref"].startswith("refs/heads/") and cache["ref"] != "refs/heads/" + default_branch:
            doomed.append((cache, "another branch"))
    for family, entries in newest.items():
        entries.sort(key=lambda c: c["created_at"], reverse=True)
        doomed.extend((cache, "older than " + entries[0]["key"]) for cache in entries[1:])
    return doomed


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF"))
    parser.add_argument("--dry-run", action="store_true", help="only list what would be deleted")
    args = parser.parse_args()
    if not args.repo or not args.ref:
        sys.exit("--repo and --ref are required outside Actions")

    default_branch = gh("api", f"repos/{args.repo}", "--jq", ".default_branch").strip()
    lines = gh("api", "--paginate", f"repos/{args.repo}/actions/caches?per_page=100", "--jq", ".actions_caches[]")
    caches = [json.loads(line) for line in lines.splitlines() if line.strip()]
    doomed = plan(caches, args.ref, default_branch)

    freed = 0
    for cache, reason in doomed:
        mib = cache["size_in_bytes"] / 2**20
        print(f"{'would delete' if args.dry_run else 'delete'} {cache['key'][:90]} "
              f"({cache['ref']}, {mib:.0f} MiB): {reason}")
        if not args.dry_run:
            gh("api", "-X", "DELETE", f"repos/{args.repo}/actions/caches/{cache['id']}")
        freed += cache["size_in_bytes"]
    total = sum(c["size_in_bytes"] for c in caches)
    print(f"{len(doomed)} of {len(caches)} caches, {freed / 2**30:.2f} of {total / 2**30:.2f} GiB")


if __name__ == "__main__":
    main()
