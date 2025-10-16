# SWE-bench Evaluation Architecture

## Architecture Diagram
```
┌──────────────────────────────┐
│ Task + Patch Inputs          │
│ • Dataset instance metadata  │
│ • Candidate patch JSON       │
└──────────────┬───────────────┘
               │ load_swebench_dataset() / get_predictions_from_file()
               ▼
┌──────────────────────────────┐
│ TestSpec Generation          │
│ • make_test_spec() builds    │
│   repo/env/eval scripts      │
└──────────────┬───────────────┘
               │ dockerfiles + constants describe env
               ▼
┌──────────────────────────────┐
│ Image Orchestration          │
│ • build_env_images() creates │
│   base/env/instance images   │
└──────────────┬───────────────┘
               │ build_container() starts sandbox
               ▼
┌──────────────────────────────┐
│ Container Execution          │
│ • copy_to_container() places │
│   patch, scripts, datasets   │
│ • exec_run_with_timeout()    │
│   runs setup & tests         │
└──────────────┬───────────────┘
               │ get_eval_report() parses logs
               ▼
┌──────────────────────────────┐
│ Grading & Reporting          │
│ • FAIL→PASS & PASS→PASS      │
│   metrics + JSON report      │
└──────────────────────────────┘
```

## Example Tasks
* **Django issue remediation** – launch `python -m swebench.harness.run_evaluation --predictions_path gold --max_workers 1 --instance_ids sympy__sympy-20590 --run_id validate-gold` to replay a known-good patch in a fully containerized environment.【F:README.md†L61-L84】
* **SWE-bench Lite evaluation** – swap in `--dataset_name princeton-nlp/SWE-bench_Lite` and a JSON/JSONL file of candidate patches to grade lightweight tasks locally or on Modal.【F:README.md†L86-L110】

Each task bundles repository metadata, the failing tests (`FAIL_TO_PASS`), and regression suite (`PASS_TO_PASS`) pulled from the dataset so the harness can recreate the original bug and verify the fix.【F:swebench/harness/utils.py†L37-L88】【F:swebench/harness/test_spec/test_spec.py†L64-L126】

## Repository Architecture for Orchestrating Evaluations
* **Entry point (`run_evaluation.py`)** – parses CLI arguments, loads tasks and predictions, spins up worker threads, manages Docker lifecycle, applies patches, and streams per-instance logs before producing a consolidated run report.【F:swebench/harness/run_evaluation.py†L12-L142】
* **Dataset + prediction loading (`utils.py`)** – resolves HuggingFace splits or local JSON/JSONL files, validates instance IDs, and exposes threadpool helpers used throughout the build and execution stages.【F:swebench/harness/utils.py†L37-L129】
* **Test specification (`test_spec.py`)** – converts dataset rows into `TestSpec` objects that capture install/eval scripts, architecture, Docker image keys, and language metadata so builds and runs are deterministic across platforms.【F:swebench/harness/test_spec/test_spec.py†L18-L122】
* **Image build orchestration (`docker_build.py`)** – materializes base, environment, and instance images, writing scripts into build contexts, streaming Docker logs, and de-duplicating builds via hashed image keys.【F:swebench/harness/docker_build.py†L1-L122】【F:swebench/harness/docker_build.py†L150-L206】
* **Runtime Docker utilities (`docker_utils.py`)** – provide low-level helpers for copying artifacts, executing commands with timeouts, cleaning up containers, and removing cached images to keep evaluations isolated.【F:swebench/harness/docker_utils.py†L1-L76】
* **Log parsing & grading (`grading.py` + `log_parsers/`)** – parse framework-specific outputs (pytest, Django, Jest, etc.), compute FAIL→PASS and PASS→PASS metrics, and emit resolved status summaries for each instance.【F:swebench/harness/grading.py†L1-L94】【F:swebench/harness/log_parsers/python.py†L1-L78】【F:swebench/harness/log_parsers/__init__.py†L1-L23】
* **Dockerfile templates (`harness/dockerfiles/`)** – language-aware Dockerfile generators (Python, JavaScript, Java, PHP, Ruby, Rust, Go, C) that plug into `TestSpec` to keep builds consistent across architectures and namespaces.【F:swebench/harness/dockerfiles/__init__.py†L1-L82】
* **Constants & configuration (`harness/constants/`)** – shared enums, path conventions, and repo-specific specs (test commands, install instructions, architecture flags) consumed by every stage of the pipeline.【F:swebench/harness/constants/__init__.py†L1-L86】

Together these modules let `run_evaluation` hydrate the exact historical environment, apply a candidate patch, execute gold-standard tests, and record evaluation artifacts on disk (`logs/`, `evaluation_results/`).【F:swebench/harness/run_evaluation.py†L12-L142】【F:swebench/harness/docker_build.py†L150-L206】

## Reusable Components for New Evaluations
* **Dataset ingestion layer** – `load_swebench_dataset()` already accepts arbitrary JSON/JSONL schemas and HuggingFace dataset names, making it straightforward to plug in new benchmarks containing multi-language tasks so long as instances provide repo identifiers, commits, and test metadata.【F:swebench/harness/utils.py†L69-L129】
* **Extensible Dockerfile templates** – the `get_dockerfile_base/env/instance` helpers map language codes to template strings, with hooks for variants (e.g., JavaScript v2), enabling rapid extension to languages such as Kotlin or C++ by adding new template modules and updating the map.【F:swebench/harness/dockerfiles/__init__.py†L1-L70】
* **Parameterized TestSpec** – language, architecture, namespaces, and script lists are encapsulated inside each `TestSpec`, so other datasets need only supply matching metadata to reuse the same build caching, script generation, and container naming scheme.【F:swebench/harness/test_spec/test_spec.py†L18-L122】
* **Pluggable log parsers** – new test frameworks can be supported by dropping additional parsers into `log_parsers/` and wiring them through the repo-to-parser mapping used during grading, which already covers Python, JavaScript, Java, C, Go, PHP, Ruby, and Rust today.【F:swebench/harness/grading.py†L24-L57】【F:swebench/harness/log_parsers/python.py†L1-L78】【F:swebench/harness/log_parsers/__init__.py†L1-L23】
* **Docker execution + reporting** – container management, patch application, and evaluation reporting are dataset-agnostic; new benchmarks only need to ensure patches conform to the `model_patch` field and that their test commands surface pass/fail status recognizable by the parsers.【F:swebench/harness/run_evaluation.py†L52-L136】【F:swebench/harness/grading.py†L24-L94】

By supplying repository-specific constants (installation commands, test runners) and optional Dockerfile templates for additional ecosystems (e.g., TypeScript, Kotlin), the existing harness can orchestrate end-to-end evaluations for future SWE datasets without re-implementing orchestration logic.【F:swebench/harness/constants/__init__.py†L1-L86】【F:swebench/harness/dockerfiles/__init__.py†L1-L82】
