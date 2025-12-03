# SWE-bench Unresolved Instances Investigation Report

## Executive Summary

This report investigates 10 unresolved instances reported by a SWE-bench user when running the evaluation harness with golden patches. The root cause appears to be pytest warnings being misinterpreted by the log parser, causing instances to be marked as unresolved even when tests actually pass.

## 1. CLI Command Review

### User's Command
```bash
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-Bench_Verified \
    --predictions_path gold \
    --max_workers 8 \
    --run_id test_gold
```

### Issues Identified

1. **Dataset Name Case Sensitivity**: 
   - User used: `princeton-nlp/SWE-Bench_Verified` (uppercase 'B' in Bench)
   - Documented: `princeton-nlp/SWE-bench_Verified` (lowercase 'b' in bench)
   - **Impact**: The normalization logic in `swebench/harness/utils.py` (lines 149-158) only handles lowercase variations. The exact dataset name `princeton-nlp/SWE-Bench_Verified` may not be normalized correctly, though HuggingFace may handle it case-insensitively.

2. **Command Syntax**: 
   - The command syntax is otherwise correct according to the documentation
   - Using `--predictions_path gold` is the documented way to test with golden patches
   - `--max_workers 8` is within recommended limits

### Recommended Command
```bash
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path gold \
    --max_workers 8 \
    --run_id test_gold
```

## 2. Root Cause Analysis

### Unresolved Instances
- `astropy__astropy-7606`
- `astropy__astropy-8707`
- `astropy__astropy-8872`
- `django__django-10097`
- `psf__requests-1724`
- `psf__requests-1766`
- `psf__requests-1921`
- `psf__requests-2317`
- `sphinx-doc__sphinx-8595`
- `sphinx-doc__sphinx-9711`

### Problem Description

The user reported that logs for unresolved instances (e.g., `astropy__astropy-8707`) contain pytest warnings like:

```
E               pytest.PytestRemovedIn8Warning: Support for nose tests is deprecated and will be removed in a future release.
E               astropy/io/fits/tests/test_header.py::TestRecordValuedKeywordCards::test_update_rvkc is using nose-specific method: `setup(self)`
E               To remove this warning, rename it to `setup_method(self)`
```

These are **warnings**, not test failures, but the evaluation harness is marking these instances as unresolved.

### Technical Analysis

#### Log Parsing Flow

1. **Test Execution** (`run_evaluation.py`):
   - Tests are run in Docker containers
   - Output is captured between `START_TEST_OUTPUT` and `END_TEST_OUTPUT` markers
   - Output is written to `test_output.txt`

2. **Log Parsing** (`grading.py:get_logs_eval`):
   - Extracts content between markers
   - Calls repository-specific parser (e.g., `parse_log_astropy` for astropy)
   - Returns a status map: `{test_name: status}`

3. **Status Determination** (`grading.py:get_eval_report`):
   - Compares parsed results against expected results
   - Determines if instance is resolved based on:
     - `FAIL_TO_PASS` tests must pass
     - `PASS_TO_PASS` tests must continue passing

#### Pytest Parser Behavior

The pytest parsers (`log_parsers/python.py`) look for lines starting with TestStatus enum values:
- `FAILED`
- `PASSED`
- `SKIPPED`
- `ERROR`
- `XFAIL`

**Key Issue**: Pytest's error display format uses "E" prefix for errors/warnings. When pytest emits warnings like `PytestRemovedIn8Warning`, they appear in the output with an "E" prefix, but they are **not** actual test failures.

#### Potential Root Causes

1. **Parser Misinterpretation**: 
   - The parser checks `line.startswith(TestStatus.value)` for lines starting with FAILED, PASSED, SKIPPED, ERROR, XFAIL
   - Warning lines with "E" prefix should NOT match these patterns, but there may be edge cases
   - If warnings appear in a format like "ERROR: pytest.PytestRemovedIn8Warning", the parser might misclassify it

2. **Missing Test Results**:
   - If warnings interfere with parsing or test output format, the status map might be empty or incomplete
   - An empty/incomplete status map would cause `get_eval_report` to mark the instance as unresolved
   - The grading logic requires ALL `FAIL_TO_PASS` tests to pass and ALL `PASS_TO_PASS` tests to pass

3. **Test Output Format Issues**:
   - Pytest's verbose output format (`-rA -vv`) used by astropy may interleave warnings with test results
   - Warnings might appear between test result lines, causing the parser to miss some results
   - The parser processes lines sequentially and may skip lines if format is unexpected

4. **Empty Status Map**:
   - If `get_logs_eval` returns an empty status map `{}`, the instance will be marked as unresolved
   - This happens if no test results are found between `START_TEST_OUTPUT` and `END_TEST_OUTPUT` markers
   - Warnings might cause pytest to exit with a non-zero code or produce malformed output

### Code Locations

- **Log Parsing**: `swebench/harness/log_parsers/python.py`
  - `parse_log_pytest_v2` (used for astropy, sphinx, scikit-learn)
  - `parse_log_pytest_options` (used for requests)
  - `parse_log_django` (used for django)

- **Grading Logic**: `swebench/harness/grading.py`
  - `get_logs_eval`: Extracts and parses test output
  - `get_eval_report`: Determines resolution status

- **Test Execution**: `swebench/harness/run_evaluation.py`
  - `run_instance`: Executes tests and captures output

## 3. Recommended Next Steps

### Immediate Actions

1. **Reproduce the Issue**:
   ```bash
   python -m swebench.harness.run_evaluation \
       --dataset_name princeton-nlp/SWE-bench_Verified \
       --predictions_path gold \
       --max_workers 1 \
       --instance_ids astropy__astropy-8707 \
       --run_id debug_warnings
   ```

2. **Examine Test Output**:
   - Check `logs/run_evaluation/debug_warnings/gold/astropy__astropy-8707/test_output.txt`
   - Verify that tests actually pass despite warnings
   - Check `logs/run_evaluation/debug_warnings/gold/astropy__astropy-8707/report.json` for resolution status

3. **Analyze Parser Behavior**:
   - Add debug logging to the pytest parser to see what lines are being processed
   - Verify that warnings are not being misclassified as test failures

### Potential Fixes

1. **Improve Warning Handling**:
   - Filter out pytest warning lines before parsing
   - Add logic to distinguish between actual test errors and warnings
   - Consider using pytest's `--disable-warnings` flag or `PYTHONWARNINGS` environment variable

2. **Enhance Parser Robustness**:
   - Make parsers more resilient to warning messages
   - Add validation to ensure parsed results match expected test counts
   - Improve error handling when parsing fails

3. **Add Warning Suppression**:
   - For repositories with known warning issues, add warning suppression to test commands
   - Similar to how sympy uses `PYTHONWARNINGS='ignore::UserWarning,ignore::SyntaxWarning'`

### Example Fix for Astropy

In `swebench/harness/constants/python.py`, the astropy test command could be modified:

```python
TEST_ASTROPY_PYTEST = "pytest -rA -vv -o console_output_style=classic --tb=no -W ignore::pytest.PytestRemovedIn8Warning"
```

Or add to the eval script generation to suppress warnings.

## 4. Verification Steps

1. **Run Single Instance**:
   ```bash
   python -m swebench.harness.run_evaluation \
       --dataset_name princeton-nlp/SWE-bench_Verified \
       --predictions_path gold \
       --max_workers 1 \
       --instance_ids astropy__astropy-8707 \
       --run_id verify_fix
   ```

2. **Check Results**:
   - Verify `report.json` shows `resolved: true`
   - Confirm all `FAIL_TO_PASS` and `PASS_TO_PASS` tests are marked as passed

3. **Run All Unresolved Instances**:
   ```bash
   python -m swebench.harness.run_evaluation \
       --dataset_name princeton-nlp/SWE-bench_Verified \
       --predictions_path gold \
       --max_workers 8 \
       --instance_ids astropy__astropy-7606 astropy__astropy-8707 astropy__astropy-8872 \
                      django__django-10097 psf__requests-1724 psf__requests-1766 \
                      psf__requests-1921 psf__requests-2317 sphinx-doc__sphinx-8595 \
                      sphinx-doc__sphinx-9711 \
       --run_id verify_all
   ```

## 5. Conclusion

The root cause appears to be pytest warnings interfering with the log parsing process, causing instances to be incorrectly marked as unresolved even when tests pass. The fix should focus on:

1. Suppressing or filtering warnings in test output
2. Improving parser robustness to handle warning messages
3. Adding validation to ensure parsing results are complete

This is likely a known issue that should be addressed to improve evaluation accuracy.
