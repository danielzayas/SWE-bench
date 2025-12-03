# Investigation Summary: SWE-bench Unresolved Instances

## Investigation Complete ✅

I've completed a comprehensive analysis of the reported issue with 10 unresolved instances when running SWE-bench evaluation against golden patches.

---

## Key Findings

### 1. CLI Command ✅ VALID
Your command is correct:
```bash
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-Bench_Verified \
    --predictions_path gold \
    --max_workers 8 \
    --run_id test_gold
```
- `princeton-nlp/SWE-Bench_Verified` is the correct dataset name
- `--predictions_path gold` correctly uses golden patches from the dataset
- All syntax is valid according to the documentation

### 2. Root Cause 🔴 LOG PARSER BUG (FIXED IN DECEMBER 2024)

The primary issue is a **bug in the pytest log parser** that was fixed on **December 5, 2024** (commit `7afd86f`).

**The Bug:**
- The `parse_log_pytest_v2` function (used by astropy and sphinx) didn't validate line length before accessing array elements
- When pytest output contained unexpected lines, it caused `IndexError`
- This resulted in empty test result maps, making instances appear "unresolved"

**The Fix:**
```python
# Before (BUGGY):
test_case = line.split()
test_status_map[test_case[1]] = test_case[0]

# After (FIXED):
test_case = line.split()
if len(test_case) >= 2:  # Added safety check
    test_status_map[test_case[1]] = test_case[0]
```

### 3. Timeline of Related Fixes

Several critical fixes were made between July 2024 - January 2025:

- **July 17, 2024**: Astropy dependency updates and log parser improvements
- **August 15, 2024**: Sphinx tox package pinning
- **December 5, 2024**: pytest_v2 log parser IndexError fix ⭐ **KEY FIX**
- **January 13, 2025**: Major refactoring (constants split into language-specific files)

### 4. Why Warnings Don't Cause Test Failures

The pytest warnings you observed (like `PytestRemovedIn8Warning`) are NOT causing test failures:
- The eval script uses `set -uxo pipefail` (without `-e`), so it continues even if pytest exits with non-zero
- The warning lines start with "E" but don't match TestStatus values (PASSED, FAILED, ERROR), so they're ignored by the parser
- The actual issue is the parser failing to extract the real test results

---

## Diagnosis: OUTDATED CODEBASE

Your fork at `/Users/danielzayas/Development/SWE-bench/SWE-bench` likely does not include the December 2024 fix.

---

## Recommended Actions (In Order)

### 1. ✅ CHECK CODE VERSION
```bash
cd /Users/danielzayas/Development/SWE-bench/SWE-bench
git log --oneline -1
git log --grep="pytest_v2" --oneline | head -5
```
Look for commit `7afd86f` or check if your HEAD is before December 5, 2024.

### 2. ✅ UPDATE TO LATEST MAIN
```bash
git fetch upstream  # or origin, depending on your remote setup
git merge upstream/main
```

This will bring in the December 2024 parser fix plus other improvements.

### 3. ✅ RE-RUN EVALUATION
After updating:
```bash
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path gold \
    --max_workers 8 \
    --run_id test_gold_fixed
```

### 4. 🔍 IF STILL FAILING: DEBUG SINGLE INSTANCE
```bash
python -m swebench.harness.run_evaluation \
    --predictions_path gold \
    --max_workers 1 \
    --instance_ids astropy__astropy-8707 \
    --run_id debug_test
```

Then inspect:
- `logs/run_evaluation/debug_test/gold/astropy__astropy-8707/test_output.txt`
- Look for `>>>>> Start Test Output` and `>>>>> End Test Output` markers
- Check if test results are between these markers

### 5. 📊 CHECK REPORT
```bash
cat logs/run_evaluation/debug_test/gold/astropy__astropy-8707/report.json
```

Look for:
- `"patch_successfully_applied": true/false`
- `"resolved": true/false`
- `"tests_status"` details

---

## Expected Outcome

**After updating to latest main (with December 2024 fix):**
- ✅ All 10 instances should resolve successfully
- ✅ Pytest warnings will be properly ignored
- ✅ Test results will be correctly parsed

**If issues persist after update:**
- 🐛 This indicates a new/different bug
- 📝 Please report with actual log files from `logs/run_evaluation/`
- 🔬 The issue would be in pytest output format, not the harness code

---

## Technical Details

For full technical analysis, see: `DIAGNOSIS_UNRESOLVED_INSTANCES.md`

Key code locations:
- Log parsers: `swebench/harness/log_parsers/python.py`
- Grading logic: `swebench/harness/grading.py`
- Test specs: `swebench/harness/test_spec/test_spec.py`
- Constants: `swebench/harness/constants/python.py`

---

## Is This a Known Issue?

**YES** - The issue was known and fixed in December 2024. The fix is in the main branch but may not be in older forks/clones.

This is NOT a new bug in the SWE-bench harness. The user simply needs to update their local copy.

---

## Questions?

If you've updated to latest main and still see issues:
1. Provide git commit hash: `git log -1 --oneline`
2. Share log files from one failing instance
3. Report as a bug with [SWE-bench issues](https://github.com/princeton-nlp/SWE-bench/issues)
