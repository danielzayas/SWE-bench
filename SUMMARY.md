# Summary: SWE-bench Unresolved Instances Investigation

## Problem Statement

A user reported 10 unresolved instances when running SWE-bench evaluation with golden patches. The user observed that logs contain only warnings (not errors), suggesting warnings are being misinterpreted as failures.

## Key Findings

### 1. CLI Command Issue
- **Issue**: User used `princeton-nlp/SWE-Bench_Verified` (uppercase 'B')
- **Correct**: Should be `princeton-nlp/SWE-bench_Verified` (lowercase 'b')
- **Impact**: May cause dataset loading issues, though HuggingFace may handle it case-insensitively

### 2. Root Cause Hypothesis
The pytest log parser may be:
1. **Missing test results** due to warning interference
2. **Returning incomplete status maps** when warnings appear in test output
3. **Failing to parse** when warnings change the output format

The parser (`parse_log_pytest_v2`) processes lines sequentially looking for test status prefixes (PASSED, FAILED, etc.). Warnings with "E" prefix should not match, but they may interfere with parsing or cause pytest to produce malformed output.

### 3. Affected Repositories
- **astropy** (3 instances): Uses `parse_log_pytest_v2` with verbose pytest output
- **django** (1 instance): Uses `parse_log_django`
- **requests** (4 instances): Uses `parse_log_pytest_options`
- **sphinx** (2 instances): Uses `parse_log_pytest_v2`

## Recommended Actions

### Immediate (Reproduction)
1. Run a single unresolved instance to verify the issue:
   ```bash
   python -m swebench.harness.run_evaluation \
       --dataset_name princeton-nlp/SWE-bench_Verified \
       --predictions_path gold \
       --max_workers 1 \
       --instance_ids astropy__astropy-8707 \
       --run_id debug_warnings
   ```

2. Examine the test output and report:
   - Check `logs/run_evaluation/debug_warnings/gold/astropy__astropy-8707/test_output.txt`
   - Check `logs/run_evaluation/debug_warnings/gold/astropy__astropy-8707/report.json`
   - Verify if tests actually pass despite warnings

### Short-term (Fix)
1. **Suppress warnings in test commands**:
   - Add `-W ignore::pytest.PytestRemovedIn8Warning` to pytest commands for affected repos
   - Or use `PYTHONWARNINGS` environment variable

2. **Improve parser robustness**:
   - Filter warning lines before parsing
   - Add validation to ensure all expected tests are found
   - Handle cases where warnings appear between test results

3. **Add diagnostic logging**:
   - Log when status map is empty or incomplete
   - Log which tests were found vs expected
   - Help identify parsing issues

### Long-term (Prevention)
1. **Standardize warning handling** across all repositories
2. **Add parser unit tests** with warning scenarios
3. **Improve error messages** when instances are unresolved
4. **Document known issues** with specific repositories

## Files to Review/Modify

1. **`swebench/harness/constants/python.py`**:
   - Modify test commands to suppress warnings (e.g., `TEST_ASTROPY_PYTEST`)

2. **`swebench/harness/log_parsers/python.py`**:
   - Improve `parse_log_pytest_v2` to handle warnings
   - Add warning filtering logic

3. **`swebench/harness/grading.py`**:
   - Add validation for incomplete status maps
   - Improve error messages when parsing fails

## Verification

After implementing fixes, verify by running all unresolved instances:

```bash
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path gold \
    --max_workers 8 \
    --instance_ids astropy__astropy-7606 astropy__astropy-8707 astropy__astropy-8872 \
                   django__django-10097 psf__requests-1724 psf__requests-1766 \
                   psf__requests-1921 psf__requests-2317 sphinx-doc__sphinx-8595 \
                   sphinx-doc__sphinx-9711 \
    --run_id verify_fix
```

All instances should show `resolved: true` in their reports.

## Documentation

- **INVESTIGATION_REPORT.md**: Detailed technical analysis
- **DIAGNOSTIC_SCRIPT.md**: Commands and scripts for diagnosis
- **SUMMARY.md**: This file - executive summary
