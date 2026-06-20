# Skill Test Report: {skill_name}

- **Tested at**: {timestamp}
- **Skill path**: `{skill_path}`
- **Overall**: {verdict}

## L1 Structure Lint
- Status: {l1_status}
- Errors: {l1_errors}
- Warnings: {l1_warnings}

## L2 Trigger Eval
- Status: {l2_status}
- Precision / Recall / F1: {l2_precision} / {l2_recall} / {l2_f1}
- Failed cases:
{l2_failures}

## L3 Behavior Eval
- Status: {l3_status}
- Passed: {l3_passed}/{l3_total}
- Avg cost (USD): {l3_avg_cost}
- Avg duration (s): {l3_avg_duration}
- Failed cases:
{l3_failures}

## L4 A/B Benchmark (optional)
{l4_section}

## 综合建议
{recommendation}
