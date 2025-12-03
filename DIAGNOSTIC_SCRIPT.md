# Diagnostic Script for Unresolved Instances

This document provides commands and scripts to diagnose the unresolved instances issue.

## Quick Diagnostic Commands

### 1. Run a Single Unresolved Instance

```bash
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path gold \
    --max_workers 1 \
    --instance_ids astropy__astropy-8707 \
    --run_id diagnostic_astropy_8707
```

### 2. Check Test Output

After running, examine the test output:

```bash
cat logs/run_evaluation/diagnostic_astropy_8707/gold/astropy__astropy-8707/test_output.txt | head -100
```

Look for:
- Presence of `>>>>> Start Test Output` and `>>>>> End Test Output` markers
- Test result lines (PASSED, FAILED, etc.)
- Warning messages and their format
- Whether tests actually pass despite warnings

### 3. Check Report

```bash
cat logs/run_evaluation/diagnostic_astropy_8707/gold/astropy__astropy-8707/report.json | python -m json.tool
```

Check:
- `resolved` field (should be `true` if tests pass)
- `patch_successfully_applied` (should be `true`)
- `tests_status` section to see which tests passed/failed

### 4. Parse Test Output Manually

Create a Python script to test the parser:

```python
from swebench.harness.log_parsers.python import parse_log_astropy
from swebench.harness.test_spec.test_spec import TestSpec

# Load test output
with open('logs/run_evaluation/diagnostic_astropy_8707/gold/astropy__astropy-8707/test_output.txt', 'r') as f:
    log_content = f.read()

# Extract content between markers
START_TEST_OUTPUT = ">>>>> Start Test Output"
END_TEST_OUTPUT = ">>>>> End Test Output"

if START_TEST_OUTPUT in log_content and END_TEST_OUTPUT in log_content:
    test_content = log_content.split(START_TEST_OUTPUT)[1].split(END_TEST_OUTPUT)[0]
    
    # Create a minimal TestSpec (you'll need to load the actual instance)
    # test_spec = ... (load from dataset)
    
    # Parse
    # status_map = parse_log_astropy(test_content, test_spec)
    # print(f"Found {len(status_map)} test results")
    # print(status_map)
else:
    print("Markers not found!")
```

## Expected Test Output Format

For pytest with `-rA -vv` (astropy format), you should see lines like:

```
PASSED astropy/io/fits/tests/test_header.py::TestRecordValuedKeywordCards::test_update_rvkc
FAILED astropy/io/fits/tests/test_something.py::test_something
```

Warnings might appear as:
```
E               pytest.PytestRemovedIn8Warning: Support for nose tests is deprecated...
```

The parser should:
1. Strip ANSI codes
2. Look for lines starting with PASSED, FAILED, SKIPPED, ERROR, XFAIL
3. Extract test name (second token) and status (first token)

## Common Issues to Check

1. **Missing Markers**: If `START_TEST_OUTPUT` or `END_TEST_OUTPUT` are missing, parsing will fail
2. **Empty Status Map**: If parser returns `{}`, no tests were found
3. **Incomplete Results**: If only some tests are parsed, the instance may be marked unresolved
4. **Warning Interference**: Warnings might appear in a format that confuses line-by-line parsing

## Next Steps After Diagnosis

1. If tests actually pass but instance is unresolved:
   - Check if status map is incomplete
   - Verify all required tests are in the map
   - Check if warnings are causing parsing issues

2. If parser returns empty map:
   - Check test output format
   - Verify markers are present
   - Check if pytest output format changed

3. If specific tests are missing:
   - Check if test names match expected format
   - Verify parser is handling test name format correctly
   - Check for special characters or formatting issues
