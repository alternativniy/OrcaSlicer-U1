import unittest

from ci_prune_caches import family_of, plan

H64 = "a" * 64
H40 = "b" * 40


def cache(key, ref="refs/heads/rel", created="2026-11-25T10:00:00Z"):
    return {"id": hash((key, ref, created)), "key": key, "ref": ref, "created_at": created, "size_in_bytes": 1}


class PruneCaches(unittest.TestCase):
    def test_families(self):
        self.assertEqual(family_of("ccache-Linux-amd64-123-1"), "ccache-Linux-amd64")
        self.assertEqual(family_of("ccache-Windows-x64-clang-45571901034-2"), "ccache-Windows-x64-clang")
        self.assertEqual(family_of(f"macos-15-arm64-cache-orcaslicer_deps-build-{H64}"), "macos-15-arm64-cache-orcaslicer_deps-build")
        self.assertEqual(family_of(f"flatpak-builder-x86_64-{H40}"), "flatpak-builder-x86_64")
        self.assertIsNone(family_of("get-cmake-sha256-verified-v1-" + H64))
        self.assertIsNone(family_of("nsis-3.13"))

    def test_keeps_newest_of_each_family_only(self):
        caches = [
            cache("ccache-Linux-amd64-1-1", created="2026-11-24T10:00:00Z"),
            cache("ccache-Linux-amd64-2-1", created="2026-11-25T10:00:00Z"),
            cache("ccache-Linux-amd64-2-2", created="2026-11-25T11:00:00Z"),
            cache("ccache-macOS-arm64-1-1"),
            cache(f"linux-clang-cache-orcaslicer_deps-build-{H64}"),
            cache("nsis-3.13"),
        ]
        doomed = [c["key"] for c, _ in plan(caches, "refs/heads/rel", "main")]
        self.assertEqual(sorted(doomed), ["ccache-Linux-amd64-1-1", "ccache-Linux-amd64-2-1"])

    def test_other_branches_go_but_default_pull_requests_and_tags_stay(self):
        caches = [
            cache("ccache-Linux-amd64-1-1", ref="refs/heads/old"),
            cache("nsis-3.13", ref="refs/heads/old"),
            cache("ccache-Linux-amd64-2-1", ref="refs/heads/main"),
            cache("ccache-Linux-amd64-3-1", ref="refs/pull/7/merge"),
            cache("ccache-Linux-amd64-4-1", ref="refs/tags/v1"),
            cache("ccache-Linux-amd64-5-1"),
        ]
        doomed = [c["key"] for c, _ in plan(caches, "refs/heads/rel", "main")]
        self.assertEqual(sorted(doomed), ["ccache-Linux-amd64-1-1", "nsis-3.13"])


if __name__ == "__main__":
    unittest.main()
