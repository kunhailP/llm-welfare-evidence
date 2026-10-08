# Design D CPU verification

2026-10-08. This file records SOFTWARE CHECKS, not LLM experiment results.

Environment: Python 3.12.14; local NumPy and PyYAML. No GPU, model weights or
paid API was used. The fixed GPU requirements have not been installed or tested
in this local environment.

## Passed

~~~text
python -m unittest discover -s tests -p test_evidence_pilot.py -v
Ran 20 tests
OK
~~~

Coverage includes an independent 98-case complete-record truth table; pivotal
and redundant missingness; unknown versus false; invalid schemas; deterministic
generation; identical legal facts across cue pairs; input hashes; no hidden-gold
leakage into prompts; reasoning/final-channel separation; invalid and truncated
answers; recovery of a known artificial interaction; zero-width-bootstrap
suppression; cancelling mean effects with individual flips; missing, duplicated,
mixed-protocol and wrong-dataset outputs.

The artificial outputs in those tests are explicitly TEST_FIXTURE_NOT_MODEL_OUTPUT.
They establish scorer behaviour, not that any model has the hypothesized effect.

Development generation:

- 24 unique complete numeric legal records.
- 880 items, three logical profiles, two renderings and three cue phrasings.
- Complete: 240 items.
- Missing material: 240 items.
- Missing irrelevant: 240 items.
- Missing redundant: 160 items, passing profiles only.
- Gold MEETS: 480; FAILS: 160; NEEDS_INFO: 240.
- Dataset SHA256: 11aea21c62a5f2431b7e6f5e15a3ad40fb407a2cfa1185274640a0e6b63cd8e9.
- Packet SHA256: 016b20fe9118bee1ca4e0951fe3ac82894d7701e1d7724ddc8092d5aef9a935e.

Dry-run prompt construction produced 22 neutral smoke requests without importing
GPU packages or writing model outputs. Selected-model download planning resolves
the existing pinned Qwen3-8B and Qwen3-14B revisions without downloading weights.

## Not yet checked

- Actual L40 driver, installed CUDA/PyTorch/vLLM compatibility and memory use.
- GPU generation, resume after a real interruption and actual throughput.
- Model competence, cue interaction, mitigation or cross-family replication.
- Human perception of cues, independent templates, population effects.
- Main-study freezing, power/precision, multiplicity and complete manuscript.

The previous Design B/C datasets were not copied into this partial source
snapshot. This check does not claim to rerun their full test/data suite.
