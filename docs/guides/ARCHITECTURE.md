# SWE-bench Architecture

This document provides a comprehensive overview of the SWE-bench evaluation orchestration system, designed to evaluate language models on real-world software engineering tasks across multiple programming languages.

## Table of Contents
- [Architecture Diagram](#architecture-diagram)
- [Example Tasks](#example-tasks)
- [Repository Architecture for Orchestrating Evaluations](#repository-architecture-for-orchestrating-evaluations)
- [Reusable Components for New Evaluations](#reusable-components-for-new-evaluations)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SWE-bench Evaluation System                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              INPUT LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Dataset (HuggingFace/Local)              Predictions (JSON/JSONL)          │
│  ├─ instance_id                           ├─ instance_id                    │
│  ├─ repo                                  ├─ model_name_or_path             │
│  ├─ problem_statement                     └─ model_patch                    │
│  ├─ base_commit                                                              │
│  ├─ test_patch                                                               │
│  ├─ FAIL_TO_PASS (tests)                                                     │
│  └─ PASS_TO_PASS (tests)                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATION LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  run_evaluation.py (Main Entry Point)                                       │
│  ├─ Loads dataset & predictions                                             │
│  ├─ Creates TestSpec for each instance                                      │
│  ├─ Manages parallel execution (ThreadPoolExecutor)                         │
│  └─ Generates final report                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TEST SPECIFICATION LAYER                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  test_spec/test_spec.py (TestSpec Dataclass)                               │
│  ├─ Instance metadata (repo, version, instance_id)                          │
│  ├─ Test requirements (FAIL_TO_PASS, PASS_TO_PASS)                          │
│  ├─ Docker configuration                                                     │
│  └─ Script generation:                                                       │
│      ├─ repo_script_list  (clone & checkout repo)                           │
│      ├─ env_script_list   (install dependencies)                            │
│      └─ eval_script_list  (apply test patch & run tests)                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       LANGUAGE-SPECIFIC LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Modular Components (by language)                                           │
│                                                                               │
│  constants/          dockerfiles/        log_parsers/                        │
│  ├─ python.py        ├─ python.py       ├─ python.py                        │
│  ├─ javascript.py    ├─ javascript.py   ├─ javascript.py                    │
│  ├─ java.py          ├─ java.py         ├─ java.py                          │
│  ├─ c.py             ├─ c.py            ├─ c.py                             │
│  ├─ go.py            ├─ go.py           ├─ go.py                            │
│  ├─ rust.py          ├─ rust.py         ├─ rust.py                          │
│  ├─ ruby.py          ├─ ruby.py         ├─ ruby.py                          │
│  └─ php.py           └─ php.py          └─ php.py                           │
│                                                                               │
│  Each language provides:                                                     │
│  ├─ Repository configurations (versions, test commands)                     │
│  ├─ Dockerfile templates (environment setup)                                │
│  └─ Log parsers (test output → pass/fail status)                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONTAINERIZATION LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Docker Image Hierarchy (Layered Caching)                                   │
│                                                                               │
│  ┌────────────────────────────────────────┐                                 │
│  │      Base Image (sweb.base.*)          │  Language runtime + tools       │
│  │      ├─ Ubuntu 22.04                   │  (Shared across repos)          │
│  │      ├─ Python/Node.js/etc.            │                                 │
│  │      └─ Common build tools             │                                 │
│  └────────────────────────────────────────┘                                 │
│                    │                                                          │
│                    ▼                                                          │
│  ┌────────────────────────────────────────┐                                 │
│  │   Environment Image (sweb.env.*)       │  Repository dependencies        │
│  │      ├─ Repo-specific packages         │  (Shared across versions)       │
│  │      └─ Test frameworks                │                                 │
│  └────────────────────────────────────────┘                                 │
│                    │                                                          │
│                    ▼                                                          │
│  ┌────────────────────────────────────────┐                                 │
│  │   Instance Image (sweb.eval.*)         │  Task-specific setup            │
│  │      ├─ Cloned repository              │  (Per instance)                 │
│  │      ├─ Checked out to base_commit     │                                 │
│  │      └─ Ready for patching             │                                 │
│  └────────────────────────────────────────┘                                 │
│                                                                               │
│  Built by: docker_build.py                                                  │
│  ├─ build_base_images()    (if not cached)                                  │
│  ├─ build_env_images()     (if not cached)                                  │
│  └─ build_instance_image() (per instance)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EXECUTION LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  docker_utils.py (Container Operations)                                     │
│                                                                               │
│  For each instance:                                                          │
│  1. Create container from instance image                                     │
│  2. Start container                                                          │
│  3. Copy model patch to container → /tmp/patch.diff                          │
│  4. Apply patch: git apply /tmp/patch.diff                                   │
│  5. Copy test patch & apply it                                               │
│  6. Execute test command with timeout                                        │
│  7. Capture test output → test_output.txt                                    │
│  8. Cleanup container                                                        │
│                                                                               │
│  Key functions:                                                              │
│  ├─ copy_to_container()     (file transfer)                                 │
│  ├─ exec_run_with_timeout() (command execution)                             │
│  └─ cleanup_container()     (cleanup)                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GRADING LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  grading.py (Test Result Analysis)                                          │
│                                                                               │
│  1. Parse test output using language-specific log parser                    │
│     └─ Extracts test names and their status (PASSED/FAILED/ERROR)           │
│                                                                               │
│  2. Compare against gold results:                                            │
│     ┌─────────────────────────────────────────────────────────┐             │
│     │ Test Category      │ Gold Status │ Eval Status │ Result │             │
│     ├────────────────────┼─────────────┼─────────────┼────────┤             │
│     │ FAIL_TO_PASS (F2P) │    FAIL     │    PASS     │   ✓    │             │
│     │ FAIL_TO_PASS (F2P) │    FAIL     │    FAIL     │   ✗    │             │
│     │ PASS_TO_PASS (P2P) │    PASS     │    PASS     │   ✓    │             │
│     │ PASS_TO_PASS (P2P) │    PASS     │    FAIL     │   ✗    │             │
│     └─────────────────────────────────────────────────────────┘             │
│                                                                               │
│  3. Compute resolution status:                                               │
│     ├─ FULL:    All F2P pass + All P2P pass                                 │
│     ├─ PARTIAL: Some F2P pass + All P2P pass                                │
│     └─ NO:      Otherwise                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OUTPUT LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Generated Artifacts:                                                        │
│                                                                               │
│  logs/                                                                       │
│  ├─ build_images/                                                            │
│  │  ├─ base/                (base image build logs)                         │
│  │  ├─ env/                 (environment image build logs)                  │
│  │  └─ instances/           (instance image build logs)                     │
│  │                                                                            │
│  └─ run_evaluation/                                                          │
│     └─ {run_id}/                                                             │
│        └─ {model_name}/                                                      │
│           └─ {instance_id}/                                                  │
│              ├─ run_instance.log    (execution log)                          │
│              ├─ test_output.txt     (raw test output)                        │
│              ├─ patch.diff          (applied patch)                          │
│              └─ report.json         (grading results)                        │
│                                                                               │
│  evaluation_results/                                                         │
│  └─ {run_id}.json  (aggregated results: resolved/total, resolution rate)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Task Structure and Format

Each task instance in SWE-bench represents a real-world software engineering issue derived from GitHub pull requests. The dataset follows a standardized format to enable consistent evaluation across different programming languages and repositories.

### Core Task Fields

**Required Fields** (used for evaluation):
- `instance_id`: Unique identifier in format `owner__repo-pull_number` (e.g., `django__django-10301`)
- `repo`: Repository in format `owner/repo` (e.g., `django/django`)
- `base_commit`: Git commit SHA where the issue exists and evaluation begins
- `version`: Repository version key (maps to dependency specifications in constants)
- `test_patch`: Git diff containing test(s) that expose the bug (apply to `base_commit`)
- `FAIL_TO_PASS`: List of test names that should pass after applying a correct solution
- `PASS_TO_PASS`: List of test names that should remain passing (regression tests)

**Optional Fields** (provide context, not used during evaluation):
- `problem_statement`: Human-readable description of the issue
- `patch`: Reference/gold solution as git diff (used for validation/analysis, not evaluation)
- `hints_text`: Additional context from issue comments (retrieved but currently unused)
- `created_at`: Timestamp when the original PR was created (ISO 8601 format)
- `environment_setup_commit`: Alternative commit for environment setup (Python-specific, defaults to `base_commit`)

The evaluation harness uses only the required fields to determine if a model's solution correctly fixes the issue without breaking existing functionality.

---

## Example Tasks

### Python Task Example: Django Issue #29500

**Task Description:**
```json
{
  "instance_id": "django__django-10301",
  "repo": "django/django",
  "problem_statement": "Migrations should not depend on django.contrib.auth models...",
  "base_commit": "3fe5d0128b7a231c195eff7c5bf3dbd7fd0e8222",
  "version": "3.0",
  "test_patch": "diff --git a/tests/auth_tests/test_migrations.py ...\n+    def test_remove_permission_after_delete(self):\n+        # Test implementation\n",
  "FAIL_TO_PASS": ["test_remove_permission_after_delete"],
  "PASS_TO_PASS": ["test_create_permission", "test_update_permission", ...],
  "patch": "diff --git a/django/contrib/auth/models.py ...\n--- a/django/contrib/auth/models.py\n+++ b/django/contrib/auth/models.py\n@@ -123,6 +123,7 @@...",
  "hints_text": "The issue is related to migration dependencies...",
  "created_at": "2019-04-23T14:30:00Z",
  "environment_setup_commit": "3fe5d0128b7a231c195eff7c5bf3dbd7fd0e8222"
}
```

**Model Prediction:**
```json
{
  "instance_id": "django__django-10301",
  "model_name_or_path": "gpt-4",
  "model_patch": "diff --git a/django/contrib/auth/models.py ...\n--- a/django/contrib/auth/models.py\n+++ b/django/contrib/auth/models.py\n@@ -123,6 +123,7 @@..."
}
```

**Evaluation Flow:**
1. **Setup**: Create Docker container with Python 3.9, Django 3.0 dependencies
2. **Repository**: Clone `django/django`, checkout to `base_commit`
3. **Patch**: Apply `model_patch` to the repository
4. **Test**: Apply `test_patch`, run Django test suite
5. **Grade**: Verify `test_remove_permission_after_delete` now passes, all other tests still pass

### JavaScript Task Example: Chart.js Issue #11234

**Task Description:**
```json
{
  "instance_id": "chartjs__Chart.js-11234",
  "repo": "chartjs/Chart.js",
  "problem_statement": "Fix bar chart rendering with negative values...",
  "base_commit": "5b8a0f5c3d9e1f2a7b8c9d0e1f2a3b4c5d6e7f8a",
  "version": "4.2",
  "test_patch": "diff --git a/test/specs/scale.linear.tests.js ...\n+  it('should handle negative values', function() {\n+    // Test implementation\n+  });\n",
  "FAIL_TO_PASS": ["test/specs/scale.linear.tests.js::negative values"],
  "PASS_TO_PASS": ["test/specs/scale.linear.tests.js::positive values", ...],
  "patch": "diff --git a/src/scales/scale.linear.js ...\n--- a/src/scales/scale.linear.js\n+++ b/src/scales/scale.linear.js\n@@ -45,7 +45,10 @@...",
  "hints_text": "The scale calculation needs to account for negative bounds",
  "created_at": "2023-08-15T09:45:22Z"
}
```

**Evaluation Flow:**
1. **Setup**: Create Docker container with Node.js 21, pnpm, xvfb (for browser tests)
2. **Repository**: Clone `chartjs/Chart.js`, checkout to `base_commit`
3. **Build**: Run `pnpm install && pnpm run build`
4. **Patch**: Apply model's patch
5. **Test**: Run karma tests with xvfb for headless browser testing
6. **Grade**: Parse karma output, verify failing test now passes

### Multi-Language Support Example

SWE-bench currently supports 8 programming languages:

| Language   | Example Repository           | Test Framework        | Log Parser        |
|------------|------------------------------|-----------------------|-------------------|
| Python     | django/django                | pytest, unittest      | pytest output     |
| JavaScript | chartjs/Chart.js             | jest, karma, mocha    | TAP, jest JSON    |
| Java       | spring-projects/spring-boot  | JUnit                 | JUnit XML         |
| C          | curl/curl                    | CTest, custom         | TAP format        |
| Go         | kubernetes/kubernetes        | go test               | go test output    |
| Rust       | rust-lang/rust               | cargo test            | cargo test output |
| Ruby       | rails/rails                  | minitest, RSpec       | RSpec formatter   |
| PHP        | laravel/framework            | PHPUnit               | PHPUnit TAP       |

---

## Repository Architecture for Orchestrating Evaluations

Under the hood, the evaluation runs the following steps:
1. `run_evaluation.py` starts and loads dataset from HuggingFace.
2. `test_spec.py` creates TestSpec for each instance.
3. `docker_build.py` creates container environment. Files in `dockerfiles/` generate Dockerfiles for different languages and configurations. 
4. `docker_utils.py` applies patch & runs tests.
5. `grading.py` analyzes test results.
6. Files in `log_parsers/` extract test results from test framework output (language-specific).

### Core Components

#### 1. Main Orchestrator: `run_evaluation.py`

**Purpose**: Entry point and coordinator for the entire evaluation pipeline.

**Key Responsibilities**:
- Parse command-line arguments (dataset, predictions, workers, timeout)
- Load dataset from HuggingFace or local files
- Load model predictions from JSON/JSONL
- Create `TestSpec` objects for each instance
- Build Docker images (base → env → instance)
- Execute evaluations in parallel using `ThreadPoolExecutor`
- Aggregate results and generate final report

**Key Functions**:
```python
def main(dataset_name, split, instance_ids, predictions_path, 
         max_workers, cache_level, run_id, timeout, ...):
    # Load data
    predictions = get_predictions_from_file(predictions_path)
    dataset = get_dataset_from_preds(dataset_name, split, instance_ids, predictions)
    
    # Build environment images (cached)
    build_env_images(client, dataset, force_rebuild, max_workers)
    
    # Run instances in parallel
    run_instances(predictions, dataset, cache_level, clean, 
                  force_rebuild, max_workers, run_id, timeout)
    
    # Generate report
    return make_run_report(predictions, dataset, run_id)

def run_instance(test_spec, pred, rm_image, force_rebuild, client, run_id, timeout):
    # 1. Build container from instance image
    container = build_container(test_spec, client, run_id)
    container.start()
    
    # 2. Apply model patch
    patch_file.write_text(pred['model_patch'])
    copy_to_container(container, patch_file, DOCKER_PATCH)
    container.exec_run(f"git apply {DOCKER_PATCH}")
    
    # 3. Run evaluation script (apply test patch + run tests)
    test_output, timed_out = exec_run_with_timeout(container, "/bin/bash /eval.sh", timeout)
    
    # 4. Grade results
    report = get_eval_report(test_spec, pred, test_output_path)
    
    return {"completed": True, "resolved": report['resolved']}
```

#### 2. Test Specification: `test_spec/test_spec.py`

**Purpose**: Encapsulates all information needed to evaluate a single task instance.

**Key Data Structure**:
```python
@dataclass
class TestSpec:
    instance_id: str           # Unique identifier (e.g., "django__django-10301")
    repo: str                  # Repository (e.g., "django/django")
    version: str               # Version for dependency installation (e.g., "3.0")
    
    # Test requirements
    FAIL_TO_PASS: list[str]    # Tests that should change from FAIL to PASS
    PASS_TO_PASS: list[str]    # Tests that should remain PASS
    
    # Docker configuration
    arch: str                  # Architecture (x86_64, arm64)
    language: str              # Language (py, js, java, etc.)
    docker_specs: dict         # Language-specific Docker settings
    
    # Setup scripts
    repo_script_list: list[str]   # Clone & checkout repository
    env_script_list: list[str]    # Install dependencies
    eval_script_list: list[str]   # Apply test patch & run tests
    
    # Image names (for caching)
    @property
    def base_image_key(self) -> str:
        return f"sweb.base.{self.language}.{self.arch}:{self.base_image_tag}"
    
    @property
    def env_image_key(self) -> str:
        # Hash of env_script_list for cache invalidation
        hash_value = hashlib.sha256(str(self.env_script_list).encode()).hexdigest()
        return f"sweb.env.{self.language}.{self.arch}.{hash_value[:22]}:{self.env_image_tag}"
    
    @property
    def instance_image_key(self) -> str:
        return f"sweb.eval.{self.arch}.{self.instance_id.lower()}:{self.instance_image_tag}"
```

**Script Generation** (`test_spec/create_scripts.py`):
```python
def make_repo_script_list(specs, repo, repo_directory, base_commit, env_name):
    """Generate commands to clone and checkout repository"""
    # Language-agnostic operations:
    # - Clone repository
    # - Checkout to base_commit
    # - Checkout specific branch if needed
    
def make_env_script_list(instance, specs, env_name):
    """Generate commands to install dependencies"""
    # Language-specific:
    # - Python: conda/pip install packages
    # - JavaScript: npm/pnpm/yarn install
    # - Java: maven/gradle dependencies
    # - etc.
    
def make_eval_script_list(instance, specs, env_name, repo_directory, base_commit, test_patch):
    """Generate commands to run tests"""
    # 1. Apply test patch
    # 2. Run test command (pytest, npm test, cargo test, etc.)
    # 3. Wrap output with markers: START_TEST_OUTPUT ... END_TEST_OUTPUT
```

#### 3. Docker Build System: `docker_build.py`

**Purpose**: Build and manage Docker images using a layered caching strategy.

**Three-Layer Hierarchy**:

```python
def build_base_images(client, dataset, force_rebuild):
    """
    Build base images with language runtimes.
    Cached across all repositories of the same language.
    
    Example: sweb.base.py.x86_64:latest
    - Ubuntu 22.04
    - Python 3.9
    - Git, curl, wget
    """

def build_env_images(client, dataset, force_rebuild, max_workers):
    """
    Build environment images with repository dependencies.
    Cached based on hash of env_script_list.
    
    Example: sweb.env.py.x86_64.a1b2c3...:latest
    - Based on base image
    - Django 3.0 dependencies
    - pytest, coverage tools
    """

def build_instance_images(client, dataset, force_rebuild, max_workers):
    """
    Build instance images with repository code.
    Built per instance (no caching between runs by default).
    
    Example: sweb.eval.x86_64.django__django-10301:latest
    - Based on env image
    - Cloned django/django
    - Checked out to base_commit
    """

def build_container(test_spec, client, run_id):
    """
    Create a container from the instance image.
    Container is ephemeral, destroyed after evaluation.
    """
```

**Cache Levels** (controlled by `--cache_level` argument):
- `none`: No caching, rebuild everything
- `base`: Cache only base images
- `env` (default): Cache base + environment images (~100GB storage)
- `instance`: Cache all images (~2TB storage)

#### 4. Docker Utilities: `docker_utils.py`

**Purpose**: Low-level Docker operations for container management.

**Key Functions**:
```python
def copy_to_container(container, src: Path, dst: Path):
    """
    Copy file from host to container using tar archive.
    Used for transferring patches and test scripts.
    """

def exec_run_with_timeout(container, cmd: str, timeout: int):
    """
    Execute command in container with timeout.
    Returns: (output, timed_out, runtime)
    
    Implementation:
    - Run command in separate thread
    - Monitor thread with timeout
    - Kill process if timeout exceeded
    """

def cleanup_container(client, container, logger):
    """
    Stop and remove container.
    Handles force-kill if normal stop fails.
    """

def should_remove(image_name, cache_level, clean, prior_images):
    """
    Determine if image should be removed based on cache strategy.
    """
```

#### 5. Grading System: `grading.py`

**Purpose**: Analyze test results and determine if the patch resolves the issue.

**Core Logic**:
```python
def get_eval_report(test_spec, prediction, test_log_path, include_tests_status):
    """
    Main grading function.
    
    Returns:
    {
        "instance_id": {
            "patch_exists": True,
            "patch_successfully_applied": True,
            "resolved": True,  # or False
            "tests_status": {
                "FAIL_TO_PASS": {"success": [...], "failure": [...]},
                "PASS_TO_PASS": {"success": [...], "failure": [...]}
            }
        }
    }
    """
    # 1. Check if patch exists and was applied
    if not prediction['model_patch']:
        return {"patch_is_None": True, "resolved": False}
    
    # 2. Parse test output using language-specific log parser
    eval_status_map, found = get_logs_eval(test_spec, test_log_path)
    if not found:
        return {"patch_successfully_applied": False, "resolved": False}
    
    # 3. Compare against gold results
    report = get_eval_tests_report(eval_status_map, {
        "FAIL_TO_PASS": test_spec.FAIL_TO_PASS,
        "PASS_TO_PASS": test_spec.PASS_TO_PASS
    })
    
    # 4. Determine resolution status
    resolution = get_resolution_status(report)
    return {"resolved": resolution == "RESOLVED_FULL", "tests_status": report}

def get_resolution_status(report):
    """
    Resolution Criteria:
    - FULL:    100% F2P pass + 100% P2P pass
    - PARTIAL: Some F2P pass (>0%, <100%) + 100% P2P pass
    - NO:      Otherwise
    """
    f2p_rate = len(report['FAIL_TO_PASS']['success']) / len(report['FAIL_TO_PASS'])
    p2p_rate = len(report['PASS_TO_PASS']['success']) / len(report['PASS_TO_PASS'])
    
    if f2p_rate == 1.0 and p2p_rate == 1.0:
        return "RESOLVED_FULL"
    elif 0 < f2p_rate < 1.0 and p2p_rate == 1.0:
        return "RESOLVED_PARTIAL"
    else:
        return "RESOLVED_NO"
```

#### 6. Log Parsers: `log_parsers/`

**Purpose**: Extract test results from test framework output (language-specific).

**Python Example** (`log_parsers/python.py`):
```python
def parse_log_pytest(log, test_spec):
    """
    Parse pytest output to extract test status.
    
    Input: Raw pytest output
    Output: {"test_name": "PASSED" | "FAILED" | "ERROR" | "SKIPPED"}
    
    Pytest formats:
    - Short: "test_file.py::test_name PASSED"
    - Verbose: "test_file.py::test_name ... ok"
    """
    status_map = {}
    
    # Regex patterns for pytest output
    for line in log.split('\n'):
        match = re.search(r'(test_\w+\.py::\S+)\s+(PASSED|FAILED|ERROR|SKIPPED)', line)
        if match:
            test_name, status = match.groups()
            status_map[test_name] = status
    
    return status_map
```

**JavaScript Example** (`log_parsers/javascript.py`):
```python
def parse_log_jest(log, test_spec):
    """
    Parse Jest JSON output.
    Jest can output structured JSON for easier parsing.
    """
    try:
        results = json.loads(log)
        status_map = {}
        for test_result in results['testResults']:
            for assertion in test_result['assertionResults']:
                name = f"{assertion['ancestorTitles']} > {assertion['title']}"
                status = "PASSED" if assertion['status'] == 'passed' else "FAILED"
                status_map[name] = status
        return status_map
    except json.JSONDecodeError:
        # Fallback to text parsing
        return parse_log_jest_text(log, test_spec)
```

#### 7. Language-Specific Configuration: `constants/`

**Purpose**: Define repository configurations, test commands, and dependencies.

**Structure** (`constants/python.py`):
```python
SPECS_DJANGO = {
    "3.0": {
        "python": "3.6",                  # Python version
        "packages": "requirements.txt",   # Dependency source
        "install": "python -m pip install -e .",
        "test_cmd": "./tests/runtests.py --verbosity 2",
        "eval_commands": [                # Environment setup
            "export LANG=en_US.UTF-8",
            "export LC_ALL=en_US.UTF-8"
        ]
    },
    "4.2": {
        "python": "3.9",
        "packages": "requirements.txt",
        "install": "python -m pip install -e .",
        "test_cmd": "./tests/runtests.py --verbosity 2"
    }
}

# Map repository to version specifications
MAP_REPO_VERSION_TO_SPECS_PY = {
    "django/django": SPECS_DJANGO,
    "sympy/sympy": SPECS_SYMPY,
    "scikit-learn/scikit-learn": SPECS_SKLEARN,
    # ... more repositories
}
```

**JavaScript Structure** (`constants/javascript.py`):
```python
SPECS_CHART_JS = {
    "4.2": {
        "install": ["pnpm install", "pnpm run build"],
        "test_cmd": [
            "pnpm install",
            "pnpm run build",
            'xvfb-run su chromeuser -c "karma start ./karma.conf.cjs --single-run"'
        ],
        "docker_specs": {
            "node_version": "21.6.2",
            "pnpm_version": "7.9.0",
            "run_args": {"cap_add": ["SYS_ADMIN"]}  # For Chromium
        }
    }
}
```

#### 8. Dockerfile Templates: `dockerfiles/`

**Purpose**: Generate Dockerfiles for different languages and configurations.

**Example** (`dockerfiles/python.py`):
```python
def get_dockerfile_base(platform, arch, language, **docker_specs):
    """
    Generate base image Dockerfile.
    
    Returns Dockerfile string with:
    - Base Ubuntu image
    - Python installation (via conda)
    - Git, build tools
    """
    return f"""
    FROM ubuntu:{docker_specs['ubuntu_version']}
    
    # Install system dependencies
    RUN apt-get update && apt-get install -y \\
        git curl wget build-essential
    
    # Install conda
    RUN wget https://repo.anaconda.com/miniconda/...
    RUN conda install python={docker_specs['python_version']}
    
    # Create testbed directory
    RUN mkdir /testbed
    WORKDIR /testbed
    """

def get_dockerfile_env(platform, arch, language, base_image_key, **docker_specs):
    """
    Generate environment image Dockerfile.
    
    Returns Dockerfile string with:
    - Based on base image
    - Copy and run setup_env.sh script
    """
    return f"""
    FROM {base_image_key}
    
    COPY ./setup_env.sh /root/setup_env.sh
    RUN /bin/bash /root/setup_env.sh
    """

def get_dockerfile_instance(platform, language, env_image_key):
    """
    Generate instance image Dockerfile.
    
    Returns Dockerfile string with:
    - Based on env image
    - Copy and run setup_repo.sh script
    """
    return f"""
    FROM {env_image_key}
    
    COPY ./setup_repo.sh /root/setup_repo.sh
    RUN /bin/bash /root/setup_repo.sh
    """
```

### Evaluation Workflow Example

Let's trace a complete evaluation for `django__django-10301`:

```bash
python -m swebench.harness.run_evaluation \
    --dataset_name SWE-bench/SWE-bench_Lite \
    --predictions_path my_predictions.json \
    --max_workers 4 \
    --run_id my_run
```

**Step-by-step execution**:

1. **Load Data** (`run_evaluation.py::main()`)
   ```python
   predictions = get_predictions_from_file("my_predictions.json")
   # [{"instance_id": "django__django-10301", "model_patch": "..."}]
   
   dataset = load_swebench_dataset("SWE-bench/SWE-bench_Lite", "test")
   # [{"instance_id": "django__django-10301", "repo": "django/django", ...}]
   ```

2. **Create TestSpec** (`test_spec/test_spec.py::make_test_spec()`)
   ```python
   test_spec = TestSpec(
       instance_id="django__django-10301",
       repo="django/django",
       version="3.0",
       language="py",
       arch="x86_64",
       FAIL_TO_PASS=["test_remove_permission_after_delete"],
       PASS_TO_PASS=["test_create_permission", ...],
       repo_script_list=[
           "git clone https://github.com/django/django.git /testbed",
           "cd /testbed && git checkout 3fe5d0128b7a231c195eff7c5bf3dbd7fd0e8222"
       ],
       env_script_list=[
           "conda install -n testbed python=3.6",
           "pip install -r requirements.txt"
       ],
       eval_script_list=[
           "cd /testbed",
           "git apply /tmp/test.patch",
           "./tests/runtests.py --verbosity 2 test_remove_permission_after_delete test_create_permission ..."
       ]
   )
   ```

3. **Build Images** (`docker_build.py`)
   ```python
   # Check if base image exists
   base_image = "sweb.base.py.x86_64:latest"
   if not client.images.get(base_image):
       build_image(base_image, dockerfile=get_dockerfile_base(...))
   
   # Check if env image exists (hash-based)
   env_image = "sweb.env.py.x86_64.a1b2c3d4e5f6:latest"
   if not client.images.get(env_image):
       build_image(env_image, dockerfile=get_dockerfile_env(...))
   
   # Build instance image
   instance_image = "sweb.eval.x86_64.django__django-10301:latest"
   build_image(instance_image, dockerfile=get_dockerfile_instance(...))
   ```

4. **Execute Evaluation** (`run_evaluation.py::run_instance()`)
   ```python
   # Create and start container
   container = client.containers.create(
       image="sweb.eval.x86_64.django__django-10301:latest",
       name="sweb.eval.django__django-10301.my_run",
       command="tail -f /dev/null"
   )
   container.start()
   
   # Copy patch
   patch_file.write_text(predictions[0]['model_patch'])
   copy_to_container(container, patch_file, "/tmp/patch.diff")
   
   # Apply patch
   result = container.exec_run("git apply /tmp/patch.diff", workdir="/testbed")
   if result.exit_code != 0:
       raise EvaluationError("Patch failed to apply")
   
   # Run tests
   eval_script = "\n".join(test_spec.eval_script_list)
   test_output, timed_out, runtime = exec_run_with_timeout(
       container, 
       f"/bin/bash -c '{eval_script}'", 
       timeout=1800
   )
   
   # Save output
   test_output_path.write_text(test_output)
   
   # Cleanup
   cleanup_container(client, container)
   ```

5. **Grade Results** (`grading.py::get_eval_report()`)
   ```python
   # Parse test output
   log_parser = MAP_REPO_TO_PARSER["django/django"]  # parse_log_pytest
   status_map = log_parser(test_output, test_spec)
   # {
   #   "test_remove_permission_after_delete": "PASSED",
   #   "test_create_permission": "PASSED",
   #   ...
   # }
   
   # Compare against expected results
   f2p_success = [t for t in test_spec.FAIL_TO_PASS if status_map.get(t) == "PASSED"]
   f2p_failure = [t for t in test_spec.FAIL_TO_PASS if status_map.get(t) != "PASSED"]
   p2p_success = [t for t in test_spec.PASS_TO_PASS if status_map.get(t) == "PASSED"]
   p2p_failure = [t for t in test_spec.PASS_TO_PASS if status_map.get(t) != "PASSED"]
   
   # Determine resolution
   resolved = (len(f2p_failure) == 0 and len(p2p_failure) == 0)
   
   # Write report
   report = {
       "django__django-10301": {
           "patch_exists": True,
           "patch_successfully_applied": True,
           "resolved": resolved,
           "tests_status": {
               "FAIL_TO_PASS": {"success": f2p_success, "failure": f2p_failure},
               "PASS_TO_PASS": {"success": p2p_success, "failure": p2p_failure}
           }
       }
   }
   report_path.write_text(json.dumps(report, indent=4))
   ```

6. **Generate Final Report** (`reporting.py::make_run_report()`)
   ```python
   # Aggregate all instance reports
   total_instances = len(dataset)
   resolved_instances = sum(1 for r in reports if r['resolved'])
   resolution_rate = resolved_instances / total_instances
   
   final_report = {
       "run_id": "my_run",
       "total_instances": total_instances,
       "resolved_instances": resolved_instances,
       "resolution_rate": resolution_rate,
       "instances": reports
   }
   
   # Save to evaluation_results/my_run.json
   ```

---

## Reusable Components for New Evaluations

### Overview

The SWE-bench architecture is designed for extensibility. Most core components are **language-agnostic** and can be reused for new datasets with minimal modifications. Only **language-specific** components need to be added for new languages.

### Dataset Format Requirements

For your new dataset to work with SWE-bench, it must follow this structure:

```jsonl
{
  "instance_id": "unique_identifier",
  "repo": "owner/repo",
  "base_commit": "git_commit_hash",
  "version": "version_key_in_constants",
  "test_patch": "diff --git a/test/...\n...",
  "FAIL_TO_PASS": ["test_that_should_pass_after_fix"],
  "PASS_TO_PASS": ["test_that_should_remain_passing"],
  "problem_statement": "Description of the issue...",
  "patch": "gold_solution_diff",
  "hints_text": "Additional context from issue discussions",
  "created_at": "2023-01-15T10:30:00Z",
  "environment_setup_commit": "commit_hash_for_env_setup"
}
```

**Required fields** (must be present for evaluation):
- `instance_id`: Unique identifier (e.g., `"kotlinx__coroutines-3456"`)
- `repo`: GitHub repository (e.g., `"Kotlin/kotlinx.coroutines"`)
- `base_commit`: Git commit hash where the bug exists
- `version`: Key in your language-specific constants (e.g., `"1.7"` in `MAP_REPO_VERSION_TO_SPECS_KOTLIN`)
- `test_patch`: Git diff containing new/modified tests that expose the bug
- `FAIL_TO_PASS`: List of test names that should pass after applying correct fix
- `PASS_TO_PASS`: List of test names that should remain passing (regression tests)

**Optional fields** (provide context but not used during evaluation):
- `problem_statement`: Human-readable description of the issue
- `patch`: Gold/reference solution as git diff (used for validation/analysis only)
- `hints_text`: Additional context from issue comments or discussions
- `created_at`: Timestamp in ISO 8601 format (e.g., `"2023-01-15T10:30:00Z"`)
- `environment_setup_commit`: Alternative commit for dependency installation (Python-specific, defaults to `base_commit` if not provided)

### Fully Reusable Components (No Modification Needed)

#### 1. Core Orchestration (`run_evaluation.py`)

**What it does**:
- Command-line interface for evaluation
- Parallel execution management
- Report generation
- Logging and error handling

**Reusability**: **100%**

**Why**: The orchestration logic is completely independent of programming languages, test frameworks, or repository structure. It only coordinates the evaluation pipeline.

**How to use**:
```bash
# Works for any dataset that follows the SWE-bench format
python -m swebench.harness.run_evaluation \
    --dataset_name path/to/your/dataset.jsonl \
    --predictions_path path/to/predictions.json \
    --max_workers 8 \
    --run_id kotlin_project_eval
```

#### 2. Docker Infrastructure (`docker_build.py`, `docker_utils.py`)

**What it does**:
- Three-layer image building (base → env → instance)
- Container lifecycle management
- Patch application
- Command execution with timeout
- Image caching strategies

**Reusability**: **100%**

**Why**: Docker operations are language-agnostic. The system doesn't care whether it's running `pytest` or `cargo test` – it just executes commands in containers.

**How to use**:
- No changes needed
- The system automatically uses the appropriate Docker specs from your language-specific constants

#### 3. Grading Logic (`grading.py`)

**What it does**:
- FAIL_TO_PASS / PASS_TO_PASS verification
- Resolution status computation (FULL/PARTIAL/NO)
- Report generation

**Reusability**: **100%**

**Why**: The grading algorithm is based on comparing test status maps (pass/fail), which is universal across all languages and test frameworks.

**How to use**:
- No changes needed
- Works as long as your log parser returns a proper status map

#### 4. Test Specification Core (`test_spec/test_spec.py`)

**What it does**:
- TestSpec dataclass definition
- Image key generation
- Dockerfile property generation

**Reusability**: **95%**

**Why**: The TestSpec structure is language-agnostic. Only the script generation delegates to language-specific functions.

**Potential modifications**:
- None required for new languages
- May need extension for new Docker platform architectures

#### 5. Utilities (`utils.py`)

**What it does**:
- Dataset loading from HuggingFace/local files
- Prediction file parsing
- Patch manipulation utilities
- Threading utilities

**Reusability**: **100%**

**Why**: These are general-purpose utilities with no language-specific logic.

### Language-Specific Components (Required for New Languages)

To extend SWE-bench to a new programming language (e.g., Swift), the following steps would be necessary:

1.  **Define Constants**: Add a new file in `swebench/harness/constants/` (e.g., `javascript.py`) to specify repository-specific installation and test commands.
2.  **Add a Dockerfile Template**: Create a new file in `swebench/harness/dockerfiles/` (e.g., `javascript.py`) that defines the Dockerfile for the new language's environment.
3.  **Implement a Log Parser**: Create a new log parser in `swebench/harness/log_parsers/` to extract test results from the output of the new language's testing frameworks.
4. **Update Aggregation Files** (see below)
5.  **Update `make_test_spec`**: Modify the `make_test_spec` function in `swebench/harness/test_spec/test_spec.py` to generate the appropriate test scripts for the new language.

#### 1. Constants: `constants/kotlin.py`

**Purpose**: Define repository configurations and test commands.

**Template**:
```python
# Test commands for Kotlin
TEST_GRADLE = "./gradlew test --no-daemon"
TEST_MAVEN = "mvn test"

# Repository specifications
SPECS_KOTLINX_COROUTINES = {
    "1.7": {
        "kotlin": "1.9",                          # Language version
        "install": ["./gradlew build -x test"],   # Build without tests
        "test_cmd": TEST_GRADLE,                  # Test command
        "docker_specs": {
            "jdk_version": "17",                  # JDK for Kotlin
        }
    },
    "1.8": {
        "kotlin": "1.9",
        "install": ["./gradlew build -x test"],
        "test_cmd": TEST_GRADLE,
        "docker_specs": {
            "jdk_version": "21",
        }
    }
}

# Map repository names to specifications
MAP_REPO_VERSION_TO_SPECS_KOTLIN = {
    "Kotlin/kotlinx.coroutines": SPECS_KOTLINX_COROUTINES,
    "JetBrains/kotlin": SPECS_KOTLIN_COMPILER,
    # ... more Kotlin repositories
}

# Repository-specific installation instructions (if needed)
MAP_REPO_TO_INSTALL_KOTLIN = {}

# Export for aggregation in constants/__init__.py
__all__ = [
    "MAP_REPO_VERSION_TO_SPECS_KOTLIN",
    "MAP_REPO_TO_INSTALL_KOTLIN",
]
```

**What to include**:
- Language/runtime version specifications
- Test commands for each repository version
- Build/installation commands
- Environment variables needed
- Docker specifications (e.g., JDK version for Kotlin/Java)

#### 2. Dockerfile Template: `dockerfiles/kotlin.py`

**Purpose**: Generate Dockerfiles for Kotlin environments.

**Template**:
```python
def get_dockerfile_base(platform, arch, language, **docker_specs):
    """
    Create base image with JDK and Kotlin.
    """
    jdk_version = docker_specs.get("jdk_version", "17")
    ubuntu_version = docker_specs.get("ubuntu_version", "22.04")
    
    return f"""
FROM --platform={platform} ubuntu:{ubuntu_version}

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git curl wget unzip build-essential

# Install JDK
RUN apt-get install -y openjdk-{jdk_version}-jdk

# Install Kotlin compiler (if needed globally)
RUN wget https://github.com/JetBrains/kotlin/releases/download/v1.9.0/kotlin-compiler-1.9.0.zip && \\
    unzip kotlin-compiler-1.9.0.zip -d /opt && \\
    ln -s /opt/kotlinc/bin/kotlinc /usr/local/bin/kotlinc

# Install Gradle
RUN wget https://services.gradle.org/distributions/gradle-8.0-bin.zip && \\
    unzip gradle-8.0-bin.zip -d /opt && \\
    ln -s /opt/gradle-8.0/bin/gradle /usr/local/bin/gradle

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-{jdk_version}-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Create testbed directory
RUN mkdir /testbed
WORKDIR /testbed
"""

def get_dockerfile_env(platform, arch, language, base_image_key, **docker_specs):
    """
    Environment image: install project dependencies.
    """
    return f"""
FROM {base_image_key}

# Copy and run environment setup script
COPY ./setup_env.sh /root/setup_env.sh
RUN /bin/bash /root/setup_env.sh
"""

def get_dockerfile_instance(platform, language, env_image_key):
    """
    Instance image: clone repository and checkout commit.
    """
    return f"""
FROM {env_image_key}

# Copy and run repository setup script
COPY ./setup_repo.sh /root/setup_repo.sh
RUN /bin/bash /root/setup_repo.sh
"""
```

**What to include**:
- Language runtime installation (JDK for Kotlin/Java)
- Build tool installation (Gradle, Maven)
- System dependencies
- Environment variable setup

#### 3. Log Parser: `log_parsers/kotlin.py`

**Purpose**: Parse test output to extract test status.

**Template**:
```python
import re

def parse_log_gradle(log: str, test_spec) -> dict[str, str]:
    """
    Parse Gradle test output.
    
    Gradle test output format:
    org.example.CoroutineTest > testSuspendFunction() PASSED
    org.example.FlowTest > testCollect() FAILED
    """
    status_map = {}
    
    # Regex for Gradle test output
    # Format: ClassName > testMethod() STATUS
    pattern = r'([\w\.]+)\s+>\s+([\w]+)\(\)\s+(PASSED|FAILED|SKIPPED)'
    
    for line in log.split('\n'):
        match = re.search(pattern, line)
        if match:
            class_name, test_name, status = match.groups()
            full_name = f"{class_name}.{test_name}"
            status_map[full_name] = status
    
    return status_map

def parse_log_maven(log: str, test_spec) -> dict[str, str]:
    """
    Parse Maven Surefire test output.
    
    Maven can generate XML reports, which are easier to parse.
    """
    status_map = {}
    
    # Try to parse XML report if available
    try:
        import xml.etree.ElementTree as ET
        # Maven writes to target/surefire-reports/
        # We'd need to access these files from the container
        # For now, parse text output
    except:
        pass
    
    # Fallback to text parsing
    # Format: [ERROR] test.example.TestClass.testMethod:42 Expected... 
    pattern = r'\[(\w+)\]\s+([\w\.]+)\.([\w]+)'
    
    for line in log.split('\n'):
        match = re.search(pattern, line)
        if match:
            status_type, class_name, test_name = match.groups()
            full_name = f"{class_name}.{test_name}"
            status = "FAILED" if status_type == "ERROR" else "PASSED"
            status_map[full_name] = status
    
    return status_map

# Map repository to appropriate parser
MAP_REPO_TO_PARSER_KOTLIN = {
    "Kotlin/kotlinx.coroutines": parse_log_gradle,
    "JetBrains/kotlin": parse_log_gradle,
    # ... more repositories
}

__all__ = ["MAP_REPO_TO_PARSER_KOTLIN"]
```

**What to include**:
- Parser function(s) for your test framework(s)
- Regex patterns or XML parsing logic
- Mapping from repository names to parser functions
- Handling for different test output formats (verbose, quiet, XML, JSON, TAP)

#### 4. Update Aggregation Files

After creating the three language-specific files, update the aggregation files:

**`constants/__init__.py`**:
```python
from swebench.harness.constants.kotlin import *

MAP_REPO_VERSION_TO_SPECS = {
    # ... existing languages
    **MAP_REPO_VERSION_TO_SPECS_KOTLIN,
}

MAP_REPO_TO_INSTALL = {
    # ... existing languages
    **MAP_REPO_TO_INSTALL_KOTLIN,
}

MAP_REPO_TO_EXT = {
    # ... existing languages
    **{k: "kt" for k in MAP_REPO_VERSION_TO_SPECS_KOTLIN.keys()},
}
```

**`log_parsers/__init__.py`**:
```python
from swebench.harness.log_parsers.kotlin import MAP_REPO_TO_PARSER_KOTLIN

MAP_REPO_TO_PARSER = {
    # ... existing languages
    **MAP_REPO_TO_PARSER_KOTLIN,
}
```

**`dockerfiles/__init__.py`** (create if doesn't exist):
```python
from swebench.harness.dockerfiles.kotlin import (
    get_dockerfile_base as get_dockerfile_base_kotlin,
    get_dockerfile_env as get_dockerfile_env_kotlin,
    get_dockerfile_instance as get_dockerfile_instance_kotlin,
)
```

### Example: Adding Support for Swift

Here's a complete example of adding Swift support:

**1. `constants/swift.py`**:
```python
TEST_SWIFT = "swift test"
TEST_XCODE = "xcodebuild test -scheme MyScheme"

SPECS_ALAMOFIRE = {
    "5.8": {
        "swift": "5.9",
        "install": ["swift package resolve"],
        "test_cmd": TEST_SWIFT,
        "docker_specs": {
            "swift_version": "5.9",
        }
    }
}

MAP_REPO_VERSION_TO_SPECS_SWIFT = {
    "Alamofire/Alamofire": SPECS_ALAMOFIRE,
}

MAP_REPO_TO_INSTALL_SWIFT = {}
```

**2. `dockerfiles/swift.py`**:
```python
def get_dockerfile_base(platform, arch, language, **docker_specs):
    swift_version = docker_specs.get("swift_version", "5.9")
    return f"""
FROM --platform={platform} swift:{swift_version}

RUN apt-get update && apt-get install -y git curl

RUN mkdir /testbed
WORKDIR /testbed
"""

def get_dockerfile_env(platform, arch, language, base_image_key, **docker_specs):
    return f"""
FROM {base_image_key}
COPY ./setup_env.sh /root/setup_env.sh
RUN /bin/bash /root/setup_env.sh
"""

def get_dockerfile_instance(platform, language, env_image_key):
    return f"""
FROM {env_image_key}
COPY ./setup_repo.sh /root/setup_repo.sh
RUN /bin/bash /root/setup_repo.sh
"""
```

**3. `log_parsers/swift.py`**:
```python
import re

def parse_log_swift(log: str, test_spec) -> dict[str, str]:
    """
    Parse Swift test output.
    
    Format:
    Test Case '-[MyTests.MyTestClass testExample]' passed (0.001 seconds).
    Test Case '-[MyTests.MyTestClass testFailure]' failed (0.002 seconds).
    """
    status_map = {}
    
    pattern = r"Test Case '-\[([\w\.]+) ([\w]+)\]' (passed|failed)"
    
    for line in log.split('\n'):
        match = re.search(pattern, line)
        if match:
            class_name, test_name, status = match.groups()
            full_name = f"{class_name}.{test_name}"
            status_map[full_name] = "PASSED" if status == "passed" else "FAILED"
    
    return status_map

MAP_REPO_TO_PARSER_SWIFT = {
    "Alamofire/Alamofire": parse_log_swift,
}
```

**4. Update aggregation files** as described above.

**5. Create Swift dataset**:
```jsonl
{
  "instance_id": "alamofire__alamofire-1234",
  "repo": "Alamofire/Alamofire",
  "base_commit": "abc123...",
  "version": "5.8",
  "test_patch": "diff --git a/Tests/...",
  "FAIL_TO_PASS": ["AlamofireTests.RequestTests.testUploadMultipart"],
  "PASS_TO_PASS": ["AlamofireTests.RequestTests.testBasicRequest", ...]
}
```

**6. Run evaluation**:
```bash
python -m swebench.harness.run_evaluation \
    --dataset_name path/to/swift_dataset.jsonl \
    --predictions_path my_swift_predictions.json \
    --max_workers 4 \
    --run_id swift_eval
```

### Multi-Language Dataset Support

SWE-bench can handle datasets with mixed languages in a single evaluation run:

```jsonl
{"instance_id": "django-1234", "repo": "django/django", "version": "3.0", ...}
{"instance_id": "chartjs-5678", "repo": "chartjs/Chart.js", "version": "4.2", ...}
{"instance_id": "kotlinx-9012", "repo": "Kotlin/kotlinx.coroutines", "version": "1.7", ...}
```

The system automatically:
1. Determines language from `MAP_REPO_TO_EXT`
2. Uses appropriate Dockerfile template
3. Uses appropriate log parser
4. All in the same evaluation run

### Best Practices for New Datasets

#### 1. Test Your Configuration First

Before creating a full dataset, test with a single instance:

```python
# test_kotlin_config.py
from swebench.harness.test_spec.test_spec import make_test_spec

test_instance = {
    "instance_id": "kotlinx__coroutines-test",
    "repo": "Kotlin/kotlinx.coroutines",
    "base_commit": "abc123...",
    "version": "1.7",
    "test_patch": "...",
    "FAIL_TO_PASS": ["..."],
    "PASS_TO_PASS": ["..."]
}

spec = make_test_spec(test_instance)
print(spec.base_dockerfile)
print(spec.env_dockerfile)
print(spec.install_repo_script)
```

#### 2. Validate Your Log Parser

Test your log parser with real test output:

```python
# test_kotlin_parser.py
from swebench.harness.log_parsers.kotlin import parse_log_gradle

sample_output = """
org.jetbrains.kotlinx.coroutines.flow.FlowTest > testBasicFlow() PASSED
org.jetbrains.kotlinx.coroutines.flow.FlowTest > testFlowCombine() FAILED
"""

status_map = parse_log_gradle(sample_output, None)
assert status_map["org.jetbrains.kotlinx.coroutines.flow.FlowTest.testBasicFlow"] == "PASSED"
assert status_map["org.jetbrains.kotlinx.coroutines.flow.FlowTest.testFlowCombine"] == "FAILED"
```

#### 3. Handle Test Framework Variations

Different repositories may use different test frameworks:

```python
# constants/kotlin.py
SPECS_KOTLINX_COROUTINES = {
    "1.7": {
        "test_cmd": "./gradlew test",  # Gradle
    }
}

SPECS_KTOR = {
    "2.3": {
        "test_cmd": "mvn test",  # Maven
    }
}

# log_parsers/kotlin.py
MAP_REPO_TO_PARSER_KOTLIN = {
    "Kotlin/kotlinx.coroutines": parse_log_gradle,
    "ktorio/ktor": parse_log_maven,
}
```

#### 4. Consider Test Execution Time

Some tests may be slow. Use appropriate timeouts:

```python
# constants/kotlin.py
SPECS_KOTLINX_COROUTINES = {
    "1.7": {
        "test_cmd": "./gradlew test",
        "timeout": 3600,  # 1 hour for slow integration tests
    }
}
```

#### 5. Handle Special Cases

Some repositories need special setup:

```python
# constants/kotlin.py
SPECS_KTOR = {
    "2.3": {
        "pre_install": [
            "apt-get update && apt-get install -y docker.io",  # If tests need Docker
        ],
        "eval_commands": [
            "export DATABASE_URL=postgresql://localhost/test",  # Environment vars
        ],
        "docker_specs": {
            "run_args": {
                "cap_add": ["NET_ADMIN"],  # Special capabilities
            }
        }
    }
}
```

### Reusability Summary

| Component | Reusability | Effort | Notes |
|-----------|------------|--------|-------|
| Core orchestration | 100% | None | Works for any dataset |
| Docker infrastructure | 100% | None | Language-agnostic |
| Grading logic | 100% | None | Universal test verification |
| Test spec core | 95% | Minimal | May need new platform support |
| Utilities | 100% | None | General-purpose |
| Constants | 0% | Medium | Per-language, per-repository |
| Dockerfiles | 0% | Medium | Per-language templates |
| Log parsers | 0% | Medium | Per-framework parsers |

**Total effort for new language**: ~4-8 hours
- 2-3 hours: Constants (repository specifications)
- 1-2 hours: Dockerfile templates
- 1-2 hours: Log parsers
- 1 hour: Testing and validation

**Total effort for new repository in existing language**: ~30 minutes
- Add repository specification to existing constants file
- No new Dockerfile or log parser needed (reuse existing)

### Cloud Evaluation Support

SWE-bench includes built-in support for cloud-based evaluation via **Modal**:

```bash
python -m swebench.harness.run_evaluation \
    --dataset_name your_dataset.jsonl \
    --predictions_path predictions.json \
    --modal true \
    --parallelism 50  # Run 50 instances in parallel
```

**Benefits**:
- No local Docker installation needed
- Massive parallelism (100+ instances simultaneously)
- Automatic resource scaling
- Pre-built images cached in the cloud

**Implementation** (`modal_eval/`):
- Wraps the same evaluation logic
- Deploys containers to Modal infrastructure
- Returns results in the same format

This works for any language/dataset without modifications.

---

## Conclusion

SWE-bench's architecture is designed for **maximum reusability** across programming languages and software projects. The key design principles are:

1. **Separation of Concerns**: Core logic (orchestration, Docker, grading) is completely independent of language-specific details
2. **Modular Extension Points**: Adding new language support requires only 3 small files
3. **Consistent Abstractions**: TestSpec, status maps, and grading logic work identically across all languages
4. **Docker Isolation**: Every evaluation runs in a clean, reproducible environment
5. **Language-Agnostic Grading**: Test verification is based on FAIL_TO_PASS/PASS_TO_PASS, which translates to any test framework

**To create evaluations for a new dataset**:
1. Reuse ~95% of existing code (orchestration, Docker, grading)
2. Add 3 language-specific files if needed (constants, dockerfiles, log_parsers)
3. Format your dataset following the SWE-bench schema
4. Run evaluation with the same command-line interface

The system is production-ready for Python, JavaScript, C, Java, Go, Rust, Ruby, and PHP, and can be extended to any language with a test framework in under a day of development.
