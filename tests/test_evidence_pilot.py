"""Meaningful CPU checks: independent truth tables, pairing and failure handling."""
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from rules.evidence import complete_label, minimal_questions, resolve


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = load_module("evidence_generator", "src/gen/make_evidence_pilot.py")
scorer = load_module("evidence_scorer", "src/eval/score_evidence_pilot.py")
runner = load_module("evidence_runner", "src/run/run_evidence_pilot.py")


def record(paid=40, program=32, medical=False):
    return dict(paid_work_hours=paid, approved_program_hours=program,
                medical_exemption=medical)


def mock_outputs(items, decision=None):
    return [dict(model="TEST_FIXTURE_NOT_MODEL_OUTPUT", revision="fixture",
                 method="plain", item_id=item["item_id"], order="forward", seed=0,
                 decision=decision(item) if decision else item["gold"]) for item in items]


class OracleTests(unittest.TestCase):
    def test_complete_records_against_independent_boolean_rule(self):
        for paid in [0, 20, 40, 79, 80, 130, 160]:
            for program in [0, 1, 39, 40, 79, 80, 160]:
                for medical in [False, True]:
                    expected = "MEETS" if medical or paid + program >= 80 else "FAILS"
                    self.assertEqual(complete_label(record(paid, program, medical)), expected)

    def test_partial_record_truth_table(self):
        examples = [
            (record(program=39), "FAILS"),
            (record(program=40), "MEETS"),
            (record(program=None), "NEEDS_INFO"),
            (record(program=None, medical=True), "MEETS"),
            (record(program=32, medical=None), "NEEDS_INFO"),
            (record(program=40, medical=None), "MEETS"),
            (record(paid=None, program=80), "MEETS"),
            (record(paid=None, program=0), "NEEDS_INFO"),
        ]
        for case, expected in examples:
            self.assertEqual(resolve(case)["label"], expected)

    def test_missing_is_not_false_and_nuisance_is_irrelevant(self):
        case = record(medical=None)
        self.assertEqual(resolve(case)["label"], "NEEDS_INFO")
        case["preferred_contact_window"] = None
        self.assertEqual(resolve(case)["label"], "NEEDS_INFO")
        self.assertEqual(resolve(record(medical=False))["label"], "FAILS")

    def test_minimal_questions(self):
        self.assertEqual(minimal_questions(record(program=None)), [["approved_program_hours"]])
        self.assertEqual(minimal_questions(record(program=None, medical=True)), [])
        self.assertEqual(minimal_questions(record(program=40, medical=None)), [])
        self.assertEqual(minimal_questions(record(program=None, medical=None)),
                         [["approved_program_hours", "medical_exemption"]])

    def test_bad_types_and_missing_keys_are_rejected(self):
        for case in [dict(approved_program_hours=0), record(paid=True), record(program=-1),
                     record(program=161), record(medical="false")]:
            with self.assertRaises(ValueError):
                resolve(case)


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = gen.generate(6)

    def test_reproducibility_and_unique_ids(self):
        self.assertEqual(self.items, gen.generate(6))
        self.assertEqual(len(self.items), len({r["item_id"] for r in self.items}))
        self.assertEqual(len({r["base"] for r in self.items}), 6)
        self.assertEqual(len({json.dumps({f: r["full_record"][f] for f in ("paid_work_hours", "approved_program_hours", "medical_exemption")}, sort_keys=True)
                              for r in self.items}), 6)

    def test_counterfactual_pairs_preserve_all_verified_facts(self):
        grouped = {}
        for row in self.items:
            key = row["base"], row["condition"], row["style"]
            grouped.setdefault(key, []).append(row)
        for rows in grouped.values():
            self.assertEqual({r["cue"] for r in rows}, set(gen.CUES))
            self.assertEqual(len({json.dumps(r["record"], sort_keys=True) for r in rows}), 1)
            self.assertEqual(len({r["gold"] for r in rows}), 1)

    def test_materiality_and_redundancy_are_proven(self):
        for row in self.items:
            expected = "NEEDS_INFO" if row["condition"] == "missing_material" else complete_label(row["full_record"])
            self.assertEqual(row["gold"], expected)
            if row["condition"] == "missing_redundant":
                self.assertNotEqual(row["profile"], "nonexempt_below")
                self.assertEqual(row["gold"], "MEETS")

    def test_manifest_detects_packet_or_dataset_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dev.jsonl"
            gen.write_dataset(path, 3)
            runner.validate_manifest(path, ROOT / "configs/evidence_packet.md")
            path.write_text(path.read_text() + "\n")
            with self.assertRaises(ValueError):
                runner.validate_manifest(path, ROOT / "configs/evidence_packet.md")

    def test_prompts_do_not_leak_hidden_completion_or_gold(self):
        row = copy.deepcopy(next(r for r in self.items if r["condition"] == "missing_material"))
        for method in runner.METHODS:
            before = runner.build_prompt("PACKET", row, method, "forward")
            changed = copy.deepcopy(row)
            changed["gold"] = "SECRET_CHANGED"
            changed["full_record"] = {"secret": "HIDDEN_COMPLETION"}
            changed["minimal_questions"] = [["SECRET_QUESTION"]]
            self.assertEqual(before, runner.build_prompt("PACKET", changed, method, "forward"))


class ParserTests(unittest.TestCase):
    def test_reasoning_is_not_scored_as_final_answer(self):
        text = "ANSWER: FAILS\n</think>\nANSWER: NEEDS_INFO"
        self.assertEqual(runner.parse(text, "plain", True)[0], "NEEDS_INFO")
        self.assertEqual(runner.parse("ANSWER: MEETS", "plain", True)[0], "TRUNCATED")

    def test_conflicting_and_length_limited_answers_are_invalid(self):
        self.assertEqual(runner.parse("ANSWER: MEETS\nANSWER: FAILS", "plain")[0], "INVALID")
        self.assertEqual(runner.parse("ANSWER: MEETS", "plain", finish_reason="length")[0], "TRUNCATED")

    def test_extraction_preserves_unknown_and_checks_schema(self):
        text = 'FACTS: {"paid_work_hours":40,"approved_program_hours":null,"medical_exemption":false}'
        self.assertEqual(runner.parse(text, "extract_rule")[0], "NEEDS_INFO")
        self.assertEqual(runner.parse(text.replace("false", '"false"'), "extract_rule")[0], "INVALID")
        self.assertEqual(runner.parse(text.replace("null", "-1"), "extract_rule")[0], "INVALID")


class ScorerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = gen.generate(6)

    def test_known_material_interaction_is_recovered(self):
        def decision(item):
            if item["condition"] == "missing_material":
                return "MEETS" if item["cue"] == "high" else "NEEDS_INFO"
            return item["gold"]
        report = scorer.score(self.items, mock_outputs(self.items, decision), draws=50)
        effects = report["effects"]["plain"]
        self.assertEqual(effects["interaction_missing_material_vs_complete"]["estimate"], 1.)
        self.assertEqual(effects["valence_adjusted_interaction_missing_material"]["estimate"], 1.)
        self.assertEqual(effects["interaction_missing_irrelevant_vs_complete"]["estimate"], 0.)

    def test_zero_bootstrap_does_not_claim_equivalence(self):
        report = scorer.score(self.items, mock_outputs(self.items), draws=50)
        effect = report["effects"]["plain"]["interaction_missing_material_vs_complete"]
        self.assertEqual(effect["estimate"], 0.)
        self.assertIsNone(effect["ci95"])
        self.assertIn("Degenerate", effect["ci_reason"])
        self.assertGreater(report["paired_flip_rates"]["plain"]["complete"]["zero_event_one_sided95_upper"], 0.)

    def test_invalid_outputs_create_bounds_not_false_decisions(self):
        outputs = mock_outputs(self.items)
        for row in outputs:
            if row["item_id"].endswith("_high"):
                row["decision"] = "INVALID"
        report = scorer.score(self.items, outputs, draws=50)
        self.assertIsNone(report["effects"]["plain"]["cue_gap_missing_material"]["estimate"])
        self.assertEqual(report["effects"]["plain"]["cue_gap_missing_material"]["identification_bounds"], [0., 1.])
        self.assertGreater(report["rates"]["plain"]["complete"]["accuracy"]["invalid"], 0)

    def test_missing_duplicate_mixed_and_unknown_outputs_are_rejected(self):
        outputs = mock_outputs(self.items)
        for invalid in [outputs[:-1], outputs+[outputs[0]],
                        [dict(outputs[0], model="OTHER")]+outputs[1:],
                        [dict(outputs[0], item_id="NO_SUCH_ITEM")]+outputs[1:]]:
            with self.assertRaises(ValueError):
                scorer.score(self.items, invalid, draws=10)
        report = scorer.score(self.items, outputs[:-1], allow_partial=True, draws=10)
        self.assertEqual(report["missing_requests"], 1)

    def test_dataset_hash_mismatch_is_rejected(self):
        outputs = [dict(r, data_sha256="wrong") for r in mock_outputs(self.items)]
        with self.assertRaises(ValueError):
            scorer.score(self.items, outputs, draws=10)

    def test_mixed_protocols_are_rejected(self):
        outputs = [dict(r, protocol_sha256="protocol_one") for r in mock_outputs(self.items)]
        outputs[0]["protocol_sha256"] = "protocol_two"
        with self.assertRaises(ValueError):
            scorer.score(self.items, outputs, draws=10)

    def test_mean_zero_can_hide_individual_flips(self):
        def decision(item):
            if item["condition"] == "missing_material" and item["cue"] in ("high", "low"):
                high_meets = int(item["base"][3:]) % 2 == 0
                return "MEETS" if (item["cue"] == "high") == high_meets else "NEEDS_INFO"
            return item["gold"]
        report = scorer.score(self.items, mock_outputs(self.items, decision), draws=50)
        self.assertEqual(report["effects"]["plain"]["cue_gap_missing_material"]["estimate"], 0.)
        self.assertEqual(report["paired_flip_rates"]["plain"]["missing_material"]["fraction"], 1.)


if __name__ == "__main__":
    unittest.main()
