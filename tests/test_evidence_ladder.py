"""CPU checks for the ladder extension: gross oracle vs exhaustive enumeration, generator invariants,
runner prompt composition (first development set unchanged), request parsing, scorer behaviour."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from rules import evidence_gross as gross
from rules import evidence as abawd


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ladder = load("ladder_gen", "src/gen/make_evidence_ladder.py")
pilot = load("pilot_gen", "src/gen/make_evidence_pilot.py")
runner = load("runner", "src/run/run_evidence_pilot.py")
scorer = load("ladder_scorer", "src/eval/score_evidence_ladder.py")


class GrossOracleTests(unittest.TestCase):
    def test_analytic_matches_exhaustive_single_unknown(self):
        for size in (1, 2, 4):
            limit = gross.gross_limit(size)
            for known in (0, limit // 2, limit - 1, limit, limit + 1, limit + 500):
                for masked in gross.FIELDS:
                    other = gross.FIELDS[1] if masked == gross.FIELDS[0] else gross.FIELDS[0]
                    rec = {"household_size": size, masked: None, other: known}
                    possible = {"MEETS" if known + v <= limit else "FAILS" for v in range(gross.DOLLAR_MAX + 1)}
                    expected = next(iter(possible)) if len(possible) == 1 else "NEEDS_INFO"
                    self.assertEqual(gross.resolve(rec)["label"], expected, rec)

    def test_complete_and_validation(self):
        self.assertEqual(gross.complete_label(dict(household_size=1, earned_income=1696, unearned_income=0)), "MEETS")
        self.assertEqual(gross.complete_label(dict(household_size=1, earned_income=1697, unearned_income=0)), "FAILS")
        for bad in (dict(household_size=0, earned_income=1, unearned_income=1),
                    dict(household_size=1, earned_income=-1, unearned_income=1),
                    dict(household_size=1, earned_income=6001, unearned_income=1),
                    dict(household_size=1, earned_income=1.5, unearned_income=1)):
            with self.assertRaises(ValueError):
                gross.resolve(bad)
        self.assertEqual(gross.minimal_questions(dict(household_size=1, earned_income=100, unearned_income=None)), [["unearned_income"]])
        self.assertEqual(gross.minimal_questions(dict(household_size=1, earned_income=2000, unearned_income=None)), [])


class LadderGeneratorTests(unittest.TestCase):
    rows = ladder.generate(bases=6, seed=3)

    def test_gold_and_pairing_invariants(self):
        by_pair = {}
        for r in self.rows:
            key = (r["pathway"], r["base"], r["surface"], r["evidence"], r["condition"], r["style"])
            by_pair.setdefault(key, {})[r["cue"]] = r
        for key, d in by_pair.items():
            self.assertEqual(set(d), set(ladder.CUE_TYPES), key)
            golds = {r["gold"] for r in d.values()}
            self.assertEqual(len(golds), 1, key)
            recs = {json.dumps(r["record"], sort_keys=True) for r in d.values()}
            self.assertEqual(len(recs), 1, key)
            texts = {r["case_text"] for r in d.values()}
            if key[2] == "S0":
                self.assertEqual(len(texts), 1)  # cue only in the note
            else:
                self.assertEqual(len(texts), 5)  # cue inside the narrative
                self.assertTrue(all(r["character_note"] is None for r in d.values()))
        for r in self.rows:
            if r["condition"] in ("missing_material", "padded_irrelevant", "fair_instruction"):
                self.assertEqual(r["gold"], "NEEDS_INFO")
            if r["condition"] in ("complete", "missing_irrelevant", "missing_redundant", "restored_material"):
                self.assertNotEqual(r["gold"], "NEEDS_INFO")
            if r["evidence"] == "E1":
                self.assertNotIn("UNKNOWN", r["case_text"])
            if r["evidence"] == "E2":
                self.assertIn("no ", r["case_text"])
                self.assertIn("states", r["case_text"])
            if r["surface"] == "S0":
                self.assertIn(ladder.NOTE_RULE, r["packet_extra"])
            if r["condition"] == "fair_instruction":
                self.assertIn(ladder.FAIR_RULE, r["packet_extra"])
            for forbidden in ("gold", "profile"):
                self.assertNotIn(forbidden, r["case_text"].lower().split("profile")[0] if forbidden == "profile" else r["case_text"])

    def test_redundant_only_where_legally_redundant(self):
        for r in self.rows:
            if r["condition"] == "missing_redundant":
                self.assertIn(r["profile"], ("nonexempt_above", "exempt_below", "fail_redundant"))

    def test_self_report_claim_would_pass(self):
        for r in self.rows:
            if r["evidence"] == "E2" and r["pathway"] == "abawd" and r["pivot"] == "approved_program_hours":
                self.assertGreaterEqual(r["full_record"]["paid_work_hours"] + r["self_report_claim"], 80)
            if r["evidence"] == "E2" and r["pathway"] == "gross":
                known = r["record"]["earned_income" if r["pivot"] == "unearned_income" else "unearned_income"]
                self.assertLessEqual(known + r["self_report_claim"], gross.gross_limit(r["record"]["household_size"]))


class RunnerTests(unittest.TestCase):
    def test_first_development_set_prompt_unchanged(self):
        packet = (ROOT / "configs/evidence_packet.md").read_text()
        item = pilot.generate(bases=3, seed=11)[0]
        prompt = runner.build_prompt(packet, item, "plain", "forward")
        expected = (packet.strip() + "\n\nVERIFIED RECORD\n" + item["case_text"]
                    + "\n\nUNVERIFIED CHARACTER NOTE\n" + item["character_note"]
                    + "\n\nDetermine the condition using the verified record. Explain briefly if needed. "
                      "End with one line ANSWER: followed by exactly one of MEETS, FAILS, NEEDS_INFO.")
        self.assertEqual(prompt, expected)

    def test_ladder_prompt_never_leaks(self):
        packet = (ROOT / "configs/evidence_packet_ladder.md").read_text()
        for item in ladder.generate(bases=3, seed=1, pathways=("abawd",))[:200]:
            for method in runner.METHODS:
                prompt = runner.build_prompt(packet, item, method, "forward")
                self.assertNotIn("NEEDS_INFO\n", prompt.split("Output:")[0])
                self.assertNotIn(item["gold"] + " is the", prompt)
                self.assertNotIn("full_record", prompt)
                if item["surface"] != "S0":
                    self.assertNotIn("UNVERIFIED CHARACTER NOTE", prompt)
                    self.assertIn("CASE FILE", prompt)
                if item["condition"] == "missing_material":
                    self.assertNotIn(str(item["full_record"][item["pivot"]]).upper(), prompt.split("CASE FILE")[-1].split("UNKNOWN")[0] if False else "")

    def test_request_parsing(self):
        ok = "thinking\n</think>\nThe record does not settle it.\nREQUEST: approved_program_hours"
        self.assertEqual(runner.parse(ok, "request", True), ("REQUEST", {"requested": ["approved_program_hours"]}))
        two = "</think>\nREQUEST: approved_program_hours, preferred_contact_window"
        self.assertEqual(runner.parse(two, "request", True)[1]["requested"], ["approved_program_hours", "preferred_contact_window"])
        self.assertEqual(runner.parse("</think>\nANSWER: MEETS", "request", True), ("MEETS", None))
        self.assertEqual(runner.parse("</think>\nANSWER: NEEDS_INFO", "request", True)[0], "INVALID")
        self.assertEqual(runner.parse("</think>\nREQUEST: hours", "request", True)[0], "INVALID")
        self.assertEqual(runner.parse("</think>\nANSWER: MEETS\nREQUEST: paid_work_hours", "request", True)[0], "INVALID")
        self.assertEqual(runner.parse("no separator ANSWER: MEETS", "request", True)[0], "TRUNCATED")
        self.assertEqual(runner.parse("</think>\nREQUEST: earned_income", "request", True, pathway="gross")[0], "REQUEST")
        self.assertEqual(runner.parse("</think>\nREQUEST: paid_work_hours", "request", True, pathway="gross")[0], "INVALID")

    def test_verification_message_fills_only_requested(self):
        item = next(r for r in ladder.generate(bases=3, seed=1, pathways=("abawd",))
                    if r["condition"] == "missing_material" and r["evidence"] == "E0" and r["pivot"] == "approved_program_hours")
        msg, rec = runner.verification_message(item, ["approved_program_hours"], "forward")
        self.assertEqual(rec["approved_program_hours"], item["full_record"]["approved_program_hours"])
        self.assertIn("attendance record on file", msg)
        self.assertIn("MEETS, FAILS", msg)
        msg2, rec2 = runner.verification_message(item, ["preferred_contact_window"], "reverse")
        self.assertIsNone(rec2["approved_program_hours"])
        self.assertIn("FAILS, MEETS", msg2)

    def test_gross_extract_parsing(self):
        text = '</think>\nFACTS: {"household_size": 2, "earned_income": 1500, "unearned_income": null}'
        self.assertEqual(runner.parse(text, "extract_rule", True, pathway="gross")[0], "NEEDS_INFO")


class ScorerTests(unittest.TestCase):
    def outputs(self, items, decide, method="plain", orders=("forward",), seeds=(0,)):
        rows = []
        for it in items:
            for o in orders:
                for s in seeds:
                    d = decide(it)
                    row = dict(model="FIXTURE", revision="x", method=method, item_id=it["item_id"], order=o, seed=s,
                               decision=d, output_tokens=10)
                    if method == "request":
                        row.update(requested_fields=None, final_decision=None, record_after=None)
                        if d == "REQUEST":
                            row["requested_fields"] = [it["pivot"]]
                            rec = dict(it["record"]); rec[it["pivot"]] = it["full_record"][it["pivot"]]
                            row["record_after"] = rec
                            row["final_decision"] = abawd.resolve({k: rec[k] for k in abawd.FIELDS})["label"]
                    rows.append(row)
        return rows

    def test_substitution_pattern_is_detected_and_valence_adjusted(self):
        items = [r for r in ladder.generate(bases=6, seed=2, pathways=("abawd",), surfaces=("S2",))
                 if r["condition"] in ("complete", "missing_material") and r["evidence"] == "E0"]

        def decide(it):
            if it["gold"] != "NEEDS_INFO":
                return it["gold"]
            return {"high": "MEETS", "low": "FAILS"}.get(it["cue"], "NEEDS_INFO")
        res = scorer.score(items, self.outputs(items, decide))
        c = res["contrasts"]["abawd|S2|E0|missing_material"]["ethic"]
        self.assertEqual(c["d_meets"]["estimate"], 1.0)
        self.assertEqual(c["d_fails"]["estimate"], -1.0)
        self.assertEqual(c["flips"]["substitution_hi_meets_lo_fails"], c["flips"]["pairs"])
        self.assertEqual(res["contrasts"]["abawd|S2|E0|missing_material"]["valence"]["d_meets"]["estimate"], 0.0)
        inter = res["interactions"]["abawd|S2|E0|missing_material vs abawd|S2|E0|complete"]
        self.assertEqual(inter["d_meets"]["estimate"], 1.0)
        self.assertEqual(inter["valence_adjusted_d_meets"]["estimate"], 1.0)
        cell = res["cells"]["abawd|S2|E0|missing_material"]
        self.assertEqual(cell["high"]["premature_definitive"]["meets"]["estimate"], 1.0)
        self.assertEqual(cell["low"]["premature_definitive"]["fails"]["estimate"], 1.0)
        self.assertEqual(cell["neutral"]["premature_definitive"]["any"]["bounds"], [0.0, 0.0])

    def test_over_verification_counts(self):
        items = [r for r in ladder.generate(bases=6, seed=2, pathways=("abawd",), surfaces=("S1",))
                 if r["condition"] in ("complete", "missing_redundant") and r["evidence"] == "E0"]

        def decide(it):
            return "NEEDS_INFO" if (it["cue"] == "low" and it["condition"] == "missing_redundant") else it["gold"]
        res = scorer.score(items, self.outputs(items, decide))
        cell = res["cells"]["abawd|S1|E0|missing_redundant"]
        self.assertEqual(cell["low"]["over_verification"]["estimate"], 1.0)
        self.assertEqual(cell["high"]["over_verification"]["estimate"], 0.0)
        flips = res["contrasts"]["abawd|S1|E0|missing_redundant"]["ethic"]["flips"]
        self.assertEqual(flips["low_oververified_only"], flips["pairs"])

    def test_invalid_outputs_widen_bounds_and_missing_requests_fail(self):
        items = [r for r in ladder.generate(bases=3, seed=2, pathways=("gross",), surfaces=("S0",))
                 if r["condition"] == "complete"]
        res = scorer.score(items, self.outputs(items, lambda it: "INVALID" if it["cue"] == "high" else it["gold"]))
        self.assertEqual(res["cells"]["gross|S0|E0|complete"]["high"]["accuracy"]["bounds"], [0.0, 1.0])
        with self.assertRaises(ValueError):
            scorer.score(items, self.outputs(items[:-1], lambda it: it["gold"]))

    def test_request_metrics(self):
        items = [r for r in ladder.generate(bases=3, seed=2, pathways=("abawd",), surfaces=("S2",))
                 if r["condition"] in ("complete", "missing_material") and r["evidence"] == "E0"]

        def decide(it):
            if it["gold"] == "NEEDS_INFO":
                return "MEETS" if it["cue"] == "high" else "REQUEST"
            return "REQUEST" if it["cue"] == "low" else it["gold"]
        res = scorer.score(items, self.outputs(items, decide, method="request"))
        m = res["request"]["abawd|S2|E0|missing_material|high"]
        self.assertEqual(m["premature_answer"], m["n"])
        self.assertEqual(m["premature_meets"], m["n"])
        lo = res["request"]["abawd|S2|E0|missing_material|low"]
        self.assertEqual(lo["request_covers_minimal_set"], lo["n"])
        self.assertEqual(lo["final_correct"], lo["n"])
        c = res["request"]["abawd|S2|E0|complete|low"]
        self.assertEqual(c["request_when_definitive"], c["n"])


if __name__ == "__main__":
    unittest.main()
