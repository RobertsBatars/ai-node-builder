---
title: "Number Classifier Node"
description: "Classifies a numeric value into a group based on configurable thresholds, outputting the value passthrough and the matched group index"
category: "Conditional"
tags: ["conditional", "classification", "grouping", "thresholds", "equivalence-partitioning", "boundary-testing", "routing", "numeric"]
author: "AI Node Builder"
version: "1.0.0"
---

# Number Classifier Node

## Overview
The Number Classifier Node assigns an incoming numeric value to a group based on a set of user-defined threshold boundaries. It outputs the original value unchanged (passthrough) alongside a zero-based group index indicating which group the value belongs to. The number of groups is always the number of thresholds plus one.

This node is well-suited for equivalence partitioning workflows (testing one representative value per group) and boundary value testing (verifying correct classification at and around each threshold).

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `value` | NUMBER | Yes | Yes | The numeric value to classify |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `value_out` | ANY | The original input value, passed through unchanged |
| `group_index` | NUMBER | Zero-based index of the group the value was classified into |

## Widgets
- **thresholds**: Text (default: `"50, 80"`)
  - Comma-separated list of numeric boundary values
  - Values are automatically sorted, so order does not matter
  - Any number of thresholds can be specified; N thresholds produce N+1 groups
  - Example: `"25, 50, 75"` produces 4 groups (indices 0–3)

- **boundary_rule**: Combo (default: `"upper_exclusive (<)"`)
  - Controls whether the boundary value itself belongs to the lower or upper group
  - `upper_exclusive (<)`: value **strictly less than** threshold goes to the lower group; value equal to threshold goes to the upper group
  - `upper_inclusive (<=)`: value **less than or equal to** threshold goes to the lower group; value equal to threshold stays in the lower group

## Group Index Reference

With `thresholds = "50, 80"` and `boundary_rule = "upper_exclusive (<)"`:

| Group index | Range |
|-------------|-------|
| 0 | value < 50 |
| 1 | 50 ≤ value < 80 |
| 2 | value ≥ 80 |

With `thresholds = "50, 80"` and `boundary_rule = "upper_inclusive (<=)"`:

| Group index | Range |
|-------------|-------|
| 0 | value ≤ 50 |
| 1 | 50 < value ≤ 80 |
| 2 | value > 80 |

## Examples

### Equivalence Partitioning — Three Groups
1. Create a Number Node and connect it to `value`
2. Set `thresholds` to `"50, 80"`
3. Connect `group_index` to a Log Node to observe the classification
4. Connect `value_out` to any further processing node
5. Run with representative values: 25 (group 0), 65 (group 1), 90 (group 2)

### Boundary Value Testing
1. Set `thresholds` to `"50, 80"` and `boundary_rule` to `"upper_exclusive (<)"`
2. Connect `group_index` and `value_out` to Log Nodes
3. Test the lower boundary (50): run with values 49, 50, 51 — expected group indices 0, 1, 1
4. Test the upper boundary (80): run with values 79, 80, 81 — expected group indices 1, 2, 2
5. Switch `boundary_rule` to `"upper_inclusive (<=)"` and repeat: expected group indices for 49/50/51 become 0, 0, 1

### Scoring or Rating Classification
1. Set `thresholds` to `"40, 70, 90"` to represent fail / pass / good / excellent bands
2. Connect a computed score value to `value`
3. Connect `group_index` to a Display Output Node with labels mapped to each index

## Common Use Cases
- **Equivalence partitioning**: Define meaningful input partitions and verify one representative per group behaves as expected
- **Boundary value analysis**: Confirm correct group assignment at and immediately around each threshold
- **Score or rating bands**: Classify numeric scores into categories such as low / medium / high
- **Sensor range monitoring**: Route or label readings that fall into different operational ranges
- **Data inspection**: Attach a Log Node to `group_index` to audit how values are distributed across groups during a workflow run

## Tips & Best Practices
- Connect `value_out` downstream when you need the original number for further processing after classification
- Connect `group_index` to a Log Node or Display Output Node to make classifications visible during testing
- The `boundary_rule` widget directly affects which group boundary values land in — this is the key variable for boundary value test cases, so test both settings
- Thresholds are sorted automatically; you can enter them in any order
- With zero thresholds entered, the node always returns `group_index = 0` (single group, useful for baseline checks)

## Error Handling
- If the `thresholds` widget contains non-numeric text, the node logs an error and falls back to treating the input as a single group (group index 0)
- If the input `value` cannot be converted to a number, the node logs an error and uses 0.0 for classification

## Related Nodes
- **Number Node**: Provides the numeric input value to classify
- **Decision Node**: Binary conditional routing based on a single comparison; use when only two outcomes are needed
- **Log Node**: Attach to `group_index` or `value_out` to observe classification results
- **Display Output Node**: Show classification results in the Display Panel
