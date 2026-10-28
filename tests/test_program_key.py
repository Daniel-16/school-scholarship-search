"""The canonical dedup key for a programme or funding award.

The key is also an archive folder name (`documents/applications/<key>/`), so
anything it emits has to be safe as a path, and it has to be a pure function
of the listing: two runs that key the same award differently store it twice,
which defeats the whole point of the state file.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import program_key  # noqa: E402


class MakeKeyTests(unittest.TestCase):
    def test_ordinary_names_slugify(self):
        self.assertEqual(
            program_key.make_key("TU Delft", "MSc Robotics"), "tu-delft_msc-robotics"
        )

    def test_path_breaking_punctuation_never_survives(self):
        # "/" splits the archive path across directories; "," and "(" have no
        # business in a folder name either.
        key = program_key.make_key(
            "University of X", "MSc Data Science (AI/ML), 2027 intake"
        )
        self.assertTrue(program_key.is_canonical(key), key)
        for char in "/,()":
            self.assertNotIn(char, key)

    def test_the_key_is_a_pure_function(self):
        args = ("Bingham University", "M.Sc. Computer Science")
        self.assertEqual(program_key.make_key(*args), program_key.make_key(*args))

    def test_long_names_are_capped_but_stay_distinct(self):
        base = "Development-Related Postgraduate Courses in Engineering and Applied Sciences"
        one = program_key.make_key("DAAD", base + " Track A")
        two = program_key.make_key("DAAD", base + " Track B")
        self.assertNotEqual(one, two)
        for key in (one, two):
            self.assertTrue(program_key.is_canonical(key), key)
            self.assertLessEqual(len(key.split("_")[1]), program_key.AWARD_MAX + 1 + program_key.HASH_LEN)

    def test_truncation_is_stable_across_runs(self):
        long_name = "A" * 200
        self.assertEqual(
            program_key.make_key("Uni", long_name), program_key.make_key("Uni", long_name)
        )

    def test_non_latin_names_fall_back_to_the_listing_id(self):
        # "Прикладная математика" slugifies to nothing. Without the fallback
        # every non-Latin programme from one provider would collide.
        one = program_key.make_key("МГУ", "Прикладная математика", "https://x.ru/p/123456")
        two = program_key.make_key("МГУ", "Информатика", "https://x.ru/p/654321")
        self.assertNotEqual(one, two)
        self.assertTrue(program_key.is_canonical(one), one)

    def test_a_mixed_script_name_is_identified_by_hash_not_by_its_latin_fragment(self):
        # "東京大学 AI" and "京都大学 AI" both fold to "ai".
        one = program_key.make_key("東京大学 AI", "Robotics")
        two = program_key.make_key("京都大学 AI", "Robotics")
        self.assertNotEqual(one, two)

    def test_an_absent_provider_is_named_not_empty(self):
        key = program_key.make_key("", "MSc Robotics")
        self.assertTrue(key.startswith("unknown-provider_"), key)
        self.assertTrue(program_key.is_canonical(key), key)

    def test_a_digits_only_fragment_is_dropped_rather_than_kept(self):
        # The only Latin content left in a non-Latin title is usually the
        # intake year, which is the volatile part. Keeping it as a "readable
        # prefix" is worse than dropping it.
        key = program_key.make_key("МГУ", "Программа 2026", "https://x.ru/p/998877")
        self.assertNotIn("2026", key)

    def test_a_re_listed_award_keeps_one_key_when_only_the_title_year_moved(self):
        # The URL is the identity; the title is not. A funder re-listing the
        # same call for a new intake must not create a second entry when the
        # title is the only thing that changed and it does not slugify.
        url = "https://funder.example/call/998877"
        one = program_key.make_key("Funder", "Программа 2026", url)
        two = program_key.make_key("Funder", "Программа 2027", url)
        self.assertEqual(one, two)


class CanonicalTests(unittest.TestCase):
    def test_canonical_shape(self):
        self.assertTrue(program_key.is_canonical("tu-delft_msc-robotics"))
        for bad in ("", "no-underscore", "a_b_c", "_leading", "UPPER_case", "has/slash_x"):
            self.assertFalse(program_key.is_canonical(bad), bad)

    def test_legacy_three_part_keys_are_recognised_separately(self):
        self.assertTrue(program_key.is_legacy_shape("tu-delft_msc-robotics_netherlands"))
        self.assertFalse(program_key.is_legacy_shape("tu-delft_msc-robotics"))


class AuditTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.tmp = Path(directory.name)

    def write(self, seen):
        path = self.tmp / "seen_programs.json"
        path.write_text(json.dumps({"seen": seen}, ensure_ascii=False), encoding="utf-8")
        return path

    def run_audit(self, path):
        return subprocess.run(
            [sys.executable, str(REPO / "tools" / "program_key.py"), "--audit", str(path)],
            capture_output=True, text=True,
        )

    def entry(self, provider, award, url="https://example.edu/p/1"):
        return {"provider": provider, "award": award, "url": url}

    def test_a_clean_state_file_passes(self):
        path = self.write({"tu-delft_msc-robotics": self.entry("TU Delft", "MSc Robotics")})
        result = self.run_audit(path)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_a_malformed_key_fails(self):
        path = self.write({"tu delft/msc": self.entry("TU Delft", "MSc Robotics")})
        result = self.run_audit(path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("malformed_keys", result.stdout)

    def test_two_keys_for_one_url_fail(self):
        url = "https://example.edu/p/1"
        path = self.write({
            "tu-delft_msc-robotics": self.entry("TU Delft", "MSc Robotics", url),
            "tu-delft_msc-robotics-2027": self.entry("TU Delft", "MSc Robotics 2027", url),
        })
        result = self.run_audit(path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate_urls", result.stdout)

    def test_an_unreadable_state_file_fails_cleanly(self):
        path = self.tmp / "broken.json"
        path.write_text("{not json", encoding="utf-8")
        result = self.run_audit(path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot read", result.stderr)


if __name__ == "__main__":
    unittest.main()
