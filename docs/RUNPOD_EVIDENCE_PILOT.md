# Design D on one L40 48GB

Status: development instructions, CPU checks completed; no GPU run completed.
Requires an SSH connection to the user's Pod. GPU environment compatibility,
actual memory use, parsing and throughput must be checked on that Pod.

## Apply this change

The accompanying evidence-pilot.patch was built against main commit
881576e3337845e00ad127b7b4052fe51ac5b244. It changes existing research docs and adds
new files without editing the archived experiments or legacy results.

From a normal checkout of that repository:

~~~bash
git status --short
git apply --check /path/to/evidence-pilot.patch
git apply /path/to/evidence-pilot.patch
~~~

Do not discard existing uncommitted work. The check should succeed before applying.
The patch does not create a commit; the PI can inspect and author their own commit.
The downloadable bundle is an overlay, not a full clone or the original datasets.

## Environment

Use the repo's Python 3.12 GPU environment and configs/requirements.lock.txt.
Inspect the Pod's driver, GPU and installed packages before reinstalling anything.
The provider's available-CUDA label is not proof that a particular Python wheel
is compatible. Do not alter the fixed package versions during an experiment.

The following assumes Python 3.12 is installed on the Pod:

~~~bash
python3.12 -m venv /workspace/venv_evidence
/workspace/venv_evidence/bin/pip install -r configs/requirements.lock.txt
/workspace/venv_evidence/bin/python -m unittest discover -s tests -p test_evidence_pilot.py -v
~~~

These new CPU tests do not require third-party data or a GPU. They do not replace
the legacy rule tests or external policy validation.

Use /workspace for the model cache and outputs. A Pod volume is not a durable
backup after Pod termination; export results before deleting it. Keep runtime
logs and large model files out of git. Stop compute while revising the design;
the user-provided deployment quote includes continuing storage fees when stopped.

## Generate and inspect before downloading models

~~~bash
/workspace/venv_evidence/bin/python src/gen/make_evidence_pilot.py --bases 24 --seed 11
/workspace/venv_evidence/bin/python src/run/run_evidence_pilot.py --model qwen3-8b --cue neutral --base-limit 3 --orders forward --dry-run --out results/evidence_pilot/unused.jsonl
~~~

The generator creates 880 items from 24 unique numeric base records, only three
logical profiles, two renderings and three cue phrasings. Its manifest records
dataset, packet and source hashes. It is explicitly DEVELOPMENT data.

Read every legal profile, each cue pair and examples of every missingness arm.
The neutral smoke command has 22 requests. The dry run writes no model output.

## Download only the first model

~~~bash
/workspace/venv_evidence/bin/python src/run/download_evidence_models.py --model qwen3-8b --cache-dir /workspace/hf/hub
~~~

The historical all-model download script is not necessary for this pilot.
The first model's weights do not require quantization on L40 48GB.

## Neutral smoke and competence

~~~bash
/workspace/venv_evidence/bin/python src/run/run_evidence_pilot.py --model qwen3-8b --cue neutral --base-limit 3 --orders forward --out results/evidence_pilot/qwen3-8b_smoke.jsonl
/workspace/venv_evidence/bin/python src/eval/score_evidence_pilot.py --data data/evidence_pilot/dev.jsonl --results results/evidence_pilot/qwen3-8b_smoke.jsonl --allow-partial --out results/evidence_pilot/qwen3-8b_smoke_score.json
~~~

Inspect all 22 raw outputs. The smoke score deliberately reports missing
requests relative to a full study and cannot estimate the moral-cue interaction.
Before broad runs, verify the model interprets the packet and labels correctly.
Then use all 24 bases with only the neutral cue:

~~~bash
/workspace/venv_evidence/bin/python src/run/run_evidence_pilot.py --model qwen3-8b --cue neutral --orders forward,reverse --out results/evidence_pilot/qwen3-8b_neutral.jsonl
~~~

This competence run has 352 requests. Report valid-response rates and balanced
accuracy by condition; a competent neutral baseline is necessary for a useful
interference analysis.

## Paired development experiment

~~~bash
/workspace/venv_evidence/bin/python src/run/run_evidence_pilot.py --model qwen3-8b --seeds 0,1 --out results/evidence_pilot/qwen3-8b_plain.jsonl
/workspace/venv_evidence/bin/python src/eval/score_evidence_pilot.py --data data/evidence_pilot/dev.jsonl --results results/evidence_pilot/qwen3-8b_plain.jsonl --out results/evidence_pilot/qwen3-8b_plain_score.json
~~~

This is 3,520 requests: 880 items x two answer orders x two seeds. It is not
3,520 independent cases. Run in batches of 32 with at most eight active sequences.
Defaults allow 4,096 new tokens and an 8,192-token total context. Do not lower
the reasoning budget after seeing which outputs support the hypothesis.
Measure actual throughput on smoke output before budgeting a longer run.

The runner fsyncs output after each batch. Resume exactly the same command with
--resume; mismatched hashes/settings or duplicate requests are rejected.
Output order is recorded for every request. Raw model text is retained.

## Subsequent models and methods

Only after reviewing the first results:

~~~bash
/workspace/venv_evidence/bin/python src/run/download_evidence_models.py --model qwen3-14b --cache-dir /workspace/hf/hub
/workspace/venv_evidence/bin/python src/run/run_evidence_pilot.py --model qwen3-14b --cue neutral --base-limit 3 --orders forward --out results/evidence_pilot/qwen3-14b_smoke.jsonl
~~~

Qwen3-14B BF16 is the same-family scale check, not cross-family replication.
The existing gpt-oss-20b adapter is a second-family candidate, but its MXFP4
kernel support and final-channel parsing must be validated on this specific
Pod before running it. The new runner has no validated Ministral adapter.
Do not interpret quantized 32B versus BF16 14B as a pure scale effect.

For an exploratory format/extraction diagnostic, keep the same model, dataset,
seeds and budgets and use --method fact_table or --method extract_rule.
Extraction is a fixed JSON-schema task: use --orders forward to avoid paying for
identical extraction prompts under a nominal answer-order change. Score each
method separately; join outputs only when provenance is compatible.

No confirmatory claim is licensed by these development commands. Design D's
main-study freeze and independent data/model/rule-pathway checks remain pending.
