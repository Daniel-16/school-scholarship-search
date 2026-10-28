"""The specs and the tools must not drift apart.

Every command file is prose a model follows. When a tool's interface changes
and the prose does not, nothing fails: the model runs a command that no longer
exists, or scores against a rubric the tool rejects, and the run looks fine
until someone reads the output carefully. These cases derive the contract from
the tool and compare it against the spec, so a drift on either side fails with
a clean diff.
"""
import json
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
COMMANDS = REPO / ".claude" / "commands"
SKILLS = REPO / ".claude" / "skills"
AGENTS = REPO / ".claude" / "agents"
sys.path.insert(0, str(REPO / "tools"))

import deadline_board  # noqa: E402
import docs_checklist  # noqa: E402
import shortlist_state  # noqa: E402


def read(path):
    return path.read_text(encoding="utf-8")


ALL_SPECS = {p.name: read(p) for p in sorted(COMMANDS.glob("*.md"))}
ALL_SKILLS = {p: read(p) for p in sorted(SKILLS.glob("*/*.md"))}


class ToolReferenceTests(unittest.TestCase):
    """Every tool a spec tells the model to run must exist."""

    SCRIPT = re.compile(r"python3? (tools/[a-z_]+\.py)")

    def test_every_referenced_tool_exists(self):
        for name, text in {**ALL_SPECS, **{str(p): t for p, t in ALL_SKILLS.items()}}.items():
            for script in set(self.SCRIPT.findall(text)):
                with self.subTest(spec=name, script=script):
                    self.assertTrue((REPO / script).is_file(), f"{name} references missing {script}")

    def test_every_referenced_portal_cli_exists(self):
        pattern = re.compile(r"bun run (\.agents/skills/[a-z0-9-]+/cli/src/cli\.ts)")
        for name, text in {**ALL_SPECS, **{str(p): t for p, t in ALL_SKILLS.items()}}.items():
            for cli in set(pattern.findall(text)):
                with self.subTest(spec=name, cli=cli):
                    self.assertTrue((REPO / cli).is_file(), f"{name} references missing {cli}")

    def test_no_spec_references_a_removed_tool(self):
        # The job-search ancestry of this workspace. A spec that still names
        # one of these was not rewritten, it was copied.
        removed = ["tools/posting_guard.py", "tools/job_key.py", "tools/rank_state.py",
                   "salary_lookup.py", "tools/convert_salary_excel.py",
                   "tools/check_upstream_updates.py"]
        for name, text in {**ALL_SPECS, **{str(p): t for p, t in ALL_SKILLS.items()}}.items():
            for tool in removed:
                with self.subTest(spec=name, tool=tool):
                    self.assertNotIn(tool, text)


class RubricConsistencyTests(unittest.TestCase):
    """04-program-evaluation.md and shortlist_state.py are one rubric."""

    EVAL = read(SKILLS / "grad-application-assistant" / "04-program-evaluation.md")

    def test_the_spec_names_every_scored_dimension(self):
        for dimension in shortlist_state.WEIGHTS:
            with self.subTest(dimension=dimension):
                self.assertIn(dimension, self.EVAL)

    def test_the_spec_publishes_the_same_weights(self):
        for dimension, weight in shortlist_state.WEIGHTS.items():
            with self.subTest(dimension=dimension):
                pattern = re.escape(dimension) + r"[^\n]*" + re.escape(f"{weight:.2f}")
                self.assertRegex(
                    self.EVAL, pattern,
                    f"04-program-evaluation.md does not publish {dimension} = {weight:.2f}",
                )

    def test_the_spec_names_every_band(self):
        for _, band in shortlist_state.BANDS:
            with self.subTest(band=band):
                self.assertIn(band, self.EVAL)

    def test_the_scorer_agent_requests_every_dimension(self):
        scorer = read(AGENTS / "listing-scorer.md")
        for dimension in shortlist_state.WEIGHTS:
            with self.subTest(dimension=dimension):
                self.assertIn(dimension, scorer)

    def test_the_scorer_agent_uses_the_tool_status_vocabulary(self):
        scorer = read(AGENTS / "listing-scorer.md")
        for status in shortlist_state.AGENT_STATUSES:
            with self.subTest(status=status):
                self.assertIn(f'"{status}"', scorer)

    def test_all_three_gates_are_specified_wherever_they_are_scored(self):
        gates = ("eligibility", "language_gate", "funding_gate")
        for path in (AGENTS / "listing-scorer.md", COMMANDS / "rank.md",
                     SKILLS / "grad-application-assistant" / "04-program-evaluation.md"):
            for gate in gates:
                with self.subTest(path=path.name, gate=gate):
                    self.assertIn(gate.split("_")[0], read(path).lower())


class LeadTimeConsistencyTests(unittest.TestCase):
    """The lead-time numbers in prose must be the ones in code."""

    def test_the_deadlines_spec_publishes_the_real_offsets(self):
        spec = ALL_SPECS["deadlines.md"]
        for name, days, _ in deadline_board.MILESTONES:
            if name == "submit":
                continue
            with self.subTest(milestone=name):
                self.assertIn(str(days), spec, f"deadlines.md does not publish {name} = {days}")

    def test_the_lead_time_floor_is_published_where_it_is_used(self):
        floor = str(shortlist_state.LEAD_TIME_DAYS)
        for name in ("rank.md", "discover.md"):
            with self.subTest(spec=name):
                self.assertIn(floor, ALL_SPECS[name])


class ChecklistConsistencyTests(unittest.TestCase):
    def test_documents_readme_describes_every_category(self):
        readme = read(REPO / "documents" / "README.md")
        for category in docs_checklist.CATEGORIES:
            with self.subTest(category=category):
                self.assertIn(f"{category}/", readme)

    def test_the_documents_tree_exists_for_every_category(self):
        for category in docs_checklist.CATEGORIES:
            with self.subTest(category=category):
                self.assertTrue((REPO / "documents" / category).is_dir())

    def test_the_sidecar_format_is_documented_where_users_will_look(self):
        for path in (REPO / "documents" / "README.md", REPO / "README.md",
                     COMMANDS / "documents.md"):
            with self.subTest(path=path.name):
                self.assertIn("meta.json", read(path))


class ArchivePathTests(unittest.TestCase):
    """Paths the specs write to must be the paths .gitignore covers."""

    def test_the_application_archive_path_is_consistent(self):
        for name in ("apply.md", "interview.md", "documents.md"):
            with self.subTest(spec=name):
                self.assertIn("documents/applications/", ALL_SPECS[name])

    def test_generated_document_paths_match_the_gitignore_rules(self):
        gitignore = read(REPO / ".gitignore")
        for pattern in ("cv/main_*.*", "statements/sop_*.*", "application_tracker.csv"):
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, gitignore)
        apply_spec = ALL_SPECS["apply.md"]
        self.assertIn("cv/main_<key>.tex", apply_spec)
        self.assertIn("statements/sop_<key>.tex", apply_spec)


class PostgraduateOnlyTests(unittest.TestCase):
    """The one invariant the whole workspace is built on."""

    def test_no_portal_skill_offers_an_undergraduate_level(self):
        for skill in sorted((REPO / ".agents" / "skills").glob("*/SKILL.md")):
            with self.subTest(skill=skill.parent.name):
                text = read(skill).lower()
                self.assertNotRegex(
                    text, r"--level\s+\w*(bachelor|undergraduate)",
                    f"{skill.parent.name} offers an undergraduate level",
                )

    def test_the_level_choices_in_every_cli_are_postgraduate(self):
        for cli in sorted((REPO / ".agents" / "skills").glob("*/cli/src/commands/search.ts")):
            with self.subTest(cli=cli.parts[-4]):
                text = read(cli)
                for match in re.finditer(r'choices:\s*\[([^\]]*)\]', text):
                    values = match.group(1).lower()
                    if "masters" in values or "phd" in values:
                        self.assertNotIn("bachelor", values)
                        self.assertNotIn("undergraduate", values)

    def test_the_invariant_is_stated_where_a_contributor_will_see_it(self):
        for path in (REPO / "CLAUDE.md", REPO / "AGENTS.md", REPO / "README.md"):
            with self.subTest(path=path.name):
                self.assertRegex(read(path).lower(), r"(no undergraduate|undergraduate)")


class SafetyLanguageTests(unittest.TestCase):
    def test_the_workspace_never_claims_to_submit_applications(self):
        for name in ("apply.md",):
            self.assertIn("Never submit", ALL_SPECS[name])

    def test_the_fraud_gate_is_wired_into_every_fetch_path(self):
        for path in (AGENTS / "listing-fetcher.md", AGENTS / "listing-scorer.md",
                     COMMANDS / "apply.md", COMMANDS / "discover.md"):
            with self.subTest(path=path.name):
                self.assertIn("listing_guard.py", read(path))

    def test_untrusted_listing_links_are_never_followed(self):
        for path in (SKILLS / "grad-application-assistant" / "09-web-research.md",
                     REPO / "CLAUDE.md"):
            with self.subTest(path=path.name):
                self.assertIn("inside the listing text", read(path))


class StructureTests(unittest.TestCase):
    def test_every_command_file_declares_its_slash_name(self):
        for name, text in ALL_SPECS.items():
            with self.subTest(spec=name):
                self.assertRegex(text, rf"^# /{re.escape(name[:-3])}\b", f"{name} title mismatch")

    def test_every_skill_reference_file_is_listed_by_its_skill(self):
        skill = read(SKILLS / "grad-application-assistant" / "SKILL.md")
        for path in sorted((SKILLS / "grad-application-assistant").glob("[0-9][0-9]-*.md")):
            with self.subTest(reference=path.name):
                self.assertIn(path.name, skill)

    # The repo-maintenance commands legitimately invoke tooling a human runs by
    # hand after reviewing a diff - installing a new portal's dependencies,
    # re-running the security guards. Those deliberately have no standing
    # grant: a session that could run them unprompted could also widen its own
    # permissions, which is the thing the guards exist to catch.
    MAINTENANCE_SPECS = {"add-portal.md", "add-template.md"}
    MAINTENANCE_TOOLS = {"tools/security_guards.py", "tools/lint_skills.py",
                         "tools/install_portal_clis.py"}

    def test_settings_grants_cover_every_tool_the_workflow_commands_run(self):
        settings = json.loads(read(REPO / ".claude" / "settings.json"))
        allowed = set(settings["permissions"]["allow"])
        pattern = re.compile(r"python3? (tools/[a-z_]+\.py)")
        for name, text in ALL_SPECS.items():
            if name in self.MAINTENANCE_SPECS:
                continue
            for script in set(pattern.findall(text)):
                if script in self.MAINTENANCE_TOOLS:
                    continue
                with self.subTest(spec=name, script=script):
                    self.assertIn(
                        f"Bash(python3 {script}:*)", allowed,
                        f"{name} runs {script} with no matching permission grant",
                    )

    def test_the_maintenance_tools_have_no_standing_grant(self):
        settings = json.loads(read(REPO / ".claude" / "settings.json"))
        allowed = set(settings["permissions"]["allow"])
        for script in self.MAINTENANCE_TOOLS:
            with self.subTest(script=script):
                self.assertNotIn(f"Bash(python3 {script}:*)", allowed)


if __name__ == "__main__":
    unittest.main()
