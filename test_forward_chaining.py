import unittest

from forward_chaining import ForwardChaining
from main import load_knowledge_base


class TestForwardChaining(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.knowledge_base = load_knowledge_base()
        cls.engine = ForwardChaining(cls.knowledge_base["rules"])

    def test_text_conflict_rule_chaining(self):
        facts = {
            "merge_conflict_message",
            "unmerged_paths",
            "conflict_markers_present",
            "status_UU",
        }
        result = self.engine.run(facts)
        self.assertIn("merge_conflict_confirmed", result["working_memory"])
        self.assertIn("textual_content_conflict", result["working_memory"])
        self.assertIn("both_modified_conflict", result["working_memory"])
        self.assertEqual(
            [rule["id"] for rule in result["fired_rules"]],
            ["R1", "R2", "R3"],
        )

    def test_deleted_by_current_branch(self):
        facts = {"merge_conflict_message", "unmerged_paths", "status_DU"}
        result = self.engine.run(facts)
        self.assertIn("deleted_by_current_branch_conflict", result["working_memory"])
        self.assertIn("R4", [rule["id"] for rule in result["fired_rules"]])

    def test_deleted_by_incoming_branch(self):
        facts = {"merge_conflict_message", "unmerged_paths", "status_UD"}
        result = self.engine.run(facts)
        self.assertIn("deleted_by_incoming_branch_conflict", result["working_memory"])
        self.assertIn("R5", [rule["id"] for rule in result["fired_rules"]])

    def test_abort_recommendation(self):
        facts = {"merge_in_progress", "user_wants_abort"}
        result = self.engine.run(facts)
        self.assertIn("abort_merge_recommended", result["working_memory"])
        self.assertIn("R6", [rule["id"] for rule in result["fired_rules"]])

    def test_continue_recommendation(self):
        facts = {
            "merge_in_progress",
            "all_conflicts_resolved",
            "resolved_files_staged",
        }
        result = self.engine.run(facts)
        self.assertIn("continue_merge_recommended", result["working_memory"])
        self.assertIn("R7", [rule["id"] for rule in result["fired_rules"]])

    def test_no_matching_rule(self):
        result = self.engine.run(set())
        self.assertEqual(result["fired_rules"], [])
        self.assertEqual(result["working_memory"], set())


if __name__ == "__main__":
    unittest.main(verbosity=2)
