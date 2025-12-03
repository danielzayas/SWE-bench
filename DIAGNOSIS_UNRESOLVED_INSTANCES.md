# Diagnosis: SWE-bench Unresolved Instances with Gold Patches

## Issue Summary
User reported 10 unresolved instances when running the SWE-bench evaluation harness against golden patches using:
```bash
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-Bench_Verified \
    --predictions_path gold \
    --max_workers 8 \
    --run_id test_gold
```

### Affected Instances
- astropy__astropy-7606
- astropy__astropy-8707
- astropy__astropy-8872
- django__django-10097
- psf__requests-1724
- psf__requests-1766
- psf__requests-1921
- psf__requests-2317
- sphinx-doc__sphinx-8595
- sphinx-doc__sphinx-9711

### Observed Symptoms
Manual inspection of logs showed only pytest warnings (not actual test failures), such as:
```
E               pytest.PytestRemovedIn8Warning: Support for nose tests is deprecated...
```

## Root Cause Analysis

### 1. CLI Command Review ✅
The user's command syntax is **VALID**:
- `--dataset_name princeton-nlp/SWE-Bench_Verified` is a correct dataset name
- `--predictions_path gold` is the correct way to test golden patches
- Both `princeton-nlp/` and `SWE-bench/` prefixes are supported for datasets

### 2. Evaluation Flow Analysis
The evaluation determines if an instance is "resolved" based on:
- All FAIL_TO_PASS tests must pass (fail → pass after patch)
- All PASS_TO_PASS tests must pass (pass → pass after patch)
- If either condition fails, the instance is marked as "unresolved"

Key code locations:
- `swebench/harness/grading.py`: Lines 215-232 define resolution status
- `swebench/harness/test_spec/test_spec.py`: Line 59 shows eval script uses `set -uxo pipefail` (NO `set -e`)
- This means the script continues even if pytest exits with non-zero code

### 3. Log Parser Issues - PRIMARY ROOT CAUSE 🔴
The core issue involves the **pytest log parser** used for these repositories:

#### Relevant Code History:
1. **July 17, 2024** (commit 1f7781b): Major refactoring for astropy support
   - Split astropy versions into two groups (old vs new)
   - Added `TEST_ASTROPY_PYTEST` with `-o console_output_style=classic`
   - Added support in log parser for older pytest output formats
   
2. **August 15, 2024** (commit dc6b81e): Pinned tox packages for sphinx
   - Fixed `tox==4.16.0` and `tox-current-env==0.0.11`
   
3. **December 5, 2024** (commit 7afd86f): Fixed pytest_v2 log parser bug
   - Added length checks to prevent IndexError on invalid log lines
   - This fix addressed cases where log lines didn't have expected format

4. **January 13, 2025** (commit d83e100): Major refactoring for SWE-bench Multimodal
   - Split `constants.py` into multiple language-specific files
   - Reorganized dockerfiles and log parsers into subdirectories

#### Log Parser Behavior:
The affected repositories use these parsers:
- **astropy**: `parse_log_pytest_v2` (line 265 in `log_parsers/python.py`)
- **requests**: `parse_log_pytest_options` (line 262)
- **sphinx**: `parse_log_pytest_v2` (line 267)

The `parse_log_pytest_v2` parser (lines 144-170):
```python
def parse_log_pytest_v2(log: str, test_spec: TestSpec) -> dict[str, str]:
    test_status_map = {}
    escapes = "".join([chr(char) for char in range(1, 32)])
    for line in log.split("\n"):
        line = re.sub(r"\[(\d+)m", "", line)
        translator = str.maketrans("", "", escapes)
        line = line.translate(translator)
        if any([line.startswith(x.value) for x in TestStatus]):
            if line.startswith(TestStatus.FAILED.value):
                line = line.replace(" - ", " ")
            test_case = line.split()
            if len(test_case) >= 2:  # Added in Dec 2024 fix
                test_status_map[test_case[1]] = test_case[0]
        elif any([line.endswith(x.value) for x in TestStatus]):
            test_case = line.split()
            if len(test_case) >= 2:  # Added in Dec 2024 fix
                test_status_map[test_case[0]] = test_case[1]
    return test_status_map
```

#### Potential Issues:
1. **Pytest warnings with "E" prefix**: Lines starting with "E" (like the example warning) don't match TestStatus values (PASSED, FAILED, ERROR, SKIPPED, XFAIL), so they're ignored by the parser.

2. **Missing END_TEST_OUTPUT marker**: If the eval script fails before writing the END_TEST_OUTPUT marker, the evaluation fails at `grading.py` line 74-76:
   ```python
   elif not (START_TEST_OUTPUT in content and END_TEST_OUTPUT in content):
       return {}, False
   ```

3. **Empty test results**: If the log parser returns an empty `status_map`, all tests are considered failed, making the instance unresolved.

4. **Version mismatch**: The user's fork might be on an outdated commit before the December 2024 parser fix.

### 4. Test Command Configuration
Current test commands (from `constants/python.py`):

**Astropy:**
- Versions 3.0+: `pytest -rA` (line 564: `TEST_PYTEST`)
- Versions 0.1-1.3: `pytest -rA -vv -o console_output_style=classic --tb=no` (line 603: `TEST_ASTROPY_PYTEST`)

**Requests:**
- All versions: `pytest -rA` (line 185: `TEST_PYTEST`)

**Sphinx:**
- All versions: `tox --current-env -epy39 -v --` (line 481: `TEST_SPHINX`)
- Plus pre_install: `sed -i 's/pytest/pytest -rA/' tox.ini`

The `-rA` flag shows a short test summary, which the log parsers expect.

## Diagnosis Summary

The most likely root causes, in order of probability:

### 1. **Outdated Codebase** (MOST LIKELY) 🎯
The user's fork at `/Users/danielzayas/Development/SWE-bench/SWE-bench` may not include:
- The December 2024 pytest_v2 log parser fix (commit 7afd86f)
- The January 2025 refactoring (commit d83e100)
- Other critical fixes from July-December 2024

**Evidence**: The log parser had a bug causing IndexError on certain log lines, which would result in empty status maps and unresolved instances.

### 2. **Log Parser Robustness Issues**
Even with the December fix, the parser may still fail on certain edge cases:
- Unusual pytest output formats
- Plugin-generated warnings that don't match expected patterns
- ANSI escape sequences not fully stripped

### 3. **Dataset/Version Mismatch**
The specific versions of astropy/sphinx/requests in SWE-bench_Verified might:
- Use pytest versions with different output formats
- Have pytest configurations that alter output
- Generate warnings that interfere with parsing

## Recommended Next Steps

### Immediate Actions:

1. **Verify Code Version** ✅ CRITICAL
   ```bash
   cd /Users/danielzayas/Development/SWE-bench/SWE-bench
   git log --oneline -1
   git log --grep="pytest_v2" --oneline
   ```
   Check if commit 7afd86f or later is included.

2. **Update to Latest Main** ✅ RECOMMENDED
   ```bash
   git fetch upstream
   git merge upstream/main
   # or
   git rebase upstream/main
   ```

3. **Re-run with Verbose Logging** 📝
   ```bash
   python -m swebench.harness.run_evaluation \
       --dataset_name princeton-nlp/SWE-bench_Verified \
       --predictions_path gold \
       --max_workers 1 \
       --instance_ids astropy__astropy-8707 \
       --run_id debug_test
   ```
   Then inspect `logs/run_evaluation/debug_test/gold/astropy__astropy-8707/test_output.txt`

4. **Check for Missing Markers** 🔍
   In the test output file, verify:
   - `>>>>> Start Test Output` is present
   - `>>>>> End Test Output` is present
   - Test results are between these markers

5. **Inspect Parsed Results** 🔬
   Look at `logs/run_evaluation/debug_test/gold/astropy__astropy-8707/report.json` to see:
   - Was patch successfully applied?
   - What tests were expected vs actual results
   - What resolution status was computed

### Long-term Fixes:

1. **Enhance Log Parser Robustness**
   - Add more defensive checks for edge cases
   - Better handling of pytest warnings and plugin output
   - Log parser test suite with problematic outputs

2. **Improve Error Reporting**
   - When an instance is unresolved, log WHY (parser failed, tests failed, etc.)
   - Add warnings when END_TEST_OUTPUT is missing
   - Better diagnostics in report.json

3. **Add Regression Tests**
   - Create test cases for these specific instances
   - Ensure future changes don't break parsing

4. **Documentation Update**
   - Document known issues with specific pytest versions
   - Add troubleshooting guide for unresolved instances

## Expected Resolution

After updating to the latest codebase (with the December 2024 fix), these instances should resolve successfully. If they don't:

1. The issue is likely in the specific pytest output format for these versions
2. A new log parser fix may be needed
3. Consider reporting as a bug with actual log files attached

## Additional Notes

- The eval script is designed to NOT exit early (`set -uxo pipefail` without `-e`)
- This allows it to complete and write END_TEST_OUTPUT even if tests fail
- The pytest warnings shown by the user should NOT cause test failures
- The issue is most likely in log PARSING, not test execution
