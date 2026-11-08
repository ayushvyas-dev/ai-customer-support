# AI Customer Support Agent - Evaluation Report

- **Generated At:** 2026-11-08T13:50:16.720723
- **Total Test Cases:** 5
- **Passed:** 4 (80.0%)
- **Failed:** 1
- **Section Classification Accuracy:** 100.0%
- **Action Decision Accuracy:** 80.0%
- **Key Phrase Compliance:** 80.0%
- **Execution Mode:** Live Agent

## Category Breakdown

| Category | Total | Passed | Failed | Pass Rate |
| :--- | :---: | :---: | :---: | :---: |
| answer_accuracy | 5 | 4 | 1 | 80.0% |

## Detailed Results

| ID | Name | Category | Status | Expected | Actual | Error / Notes |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| eval-001 | nexa-one-specs-and-price | answer_accuracy | PASSED | `smartphone/reply` | `smartphone/reply` |  |
| eval-002 | nexa-one-pro-specs-and-display-refresh | answer_accuracy | PASSED | `smartphone/reply` | `smartphone/reply` |  |
| eval-003 | nexa-lite-specs-and-pricing | answer_accuracy | PASSED | `smartphone/reply` | `smartphone/reply` |  |
| eval-004 | in-the-box-charger-inquiry | answer_accuracy | FAILED | `accessories/reply` | `accessories/escalate` | Missing required phrase: 'not included'; Missing required phrase: 'USB-C'; Missing required phrase: 'cable'; Missing required phrase: 'separately' |
| eval-005 | all-models-5g-and-dual-sim | answer_accuracy | PASSED | `smartphone/reply` | `smartphone/reply` |  |
