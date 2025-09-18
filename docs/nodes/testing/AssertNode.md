---
title: "Assert Node"
description: "Validates that actual values match expected values for automated testing"
category: "Testing"
tags: ["testing", "assertion", "validation", "comparison", "automation", "test-runner"]
author: "AI Node Builder"
version: "1.0.0"
---

# Assert Node

## Overview
The Assert Node is the primary testing component for automated workflow validation. It compares actual values against expected values and provides structured feedback for test runners. When assertions fail, the node throws an AssertionError that stops workflow execution, making it essential for test automation.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `actual` | ANY | Yes | No | The actual value to test |
| `expected` | ANY | Yes | Yes | The expected value to compare against |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `on_success` | ANY | Receives the actual value when assertion passes |
| `on_failure` | ANY | Not used (node throws exception on failure) |

## Examples

### Basic Value Testing
Connect a Text Node with "Hello" to the `expected` input and the output of a processing node to the `actual` input. If the values match, the assertion passes and the actual value flows to `on_success`.

### Numeric Comparison
Use Number Nodes to test mathematical operations: connect an Add Node's result to `actual` and a Number Node with the expected sum to `expected`.

### Workflow Validation
Place Assert Nodes at key points in workflows to validate intermediate results and ensure data transformations work correctly.

### Test Chain Construction
Connect multiple Assert Nodes in sequence by linking the `on_success` output of one to the `actual` input of the next, creating comprehensive test suites.

## Behavior & Execution

### Comparison Logic
- **Numeric Comparison**: Attempts to convert both values to float for mathematical comparison
- **String Fallback**: If numeric conversion fails, compares values as strings
- **Type Handling**: Consistent behavior regardless of input types

### Success Path
- When values match, the actual value passes to `on_success` output
- `on_failure` output is skipped using `SKIP_OUTPUT`
- Workflow execution continues normally

### Failure Path
- When values don't match, an `AssertionError` is thrown
- Error message includes both actual and expected values
- Workflow execution stops immediately
- Test runner receives failure notification

### Test Event Integration
- Sends structured `TEST_EVENT` messages to the test runner
- Message includes status, actual value, and expected value
- Compatible with automated testing infrastructure

## Message Structure

### Success Message
```json
{
  "status": "SUCCESS",
  "actual": "actual_value",
  "expected": "expected_value"
}
```

### Failure Message
```json
{
  "status": "FAILURE", 
  "actual": "actual_value",
  "expected": "expected_value"
}
```

## Test Runner Integration

### Automated Testing
- The test runner monitors for `AssertionError` exceptions
- Tests pass only when all Assert Nodes execute successfully
- Single assertion failure causes entire test to fail

### Message Protocol
- Uses `MessageType.TEST_EVENT` for structured communication
- Test runners can capture and process assertion results
- Enables detailed test reporting and analysis

### Workflow Testing
- Place Assert Nodes at workflow endpoints to validate final results
- Use multiple Assert Nodes to test intermediate states
- Essential component for JSON-based test files in `/tests/` directory

## Comparison Details

### Numeric Precision
- Both values converted to float when possible
- Enables mathematical comparison (10.0 == 10)
- More accurate than string comparison for numbers

### String Comparison
- Used when numeric conversion fails
- Case-sensitive exact matching
- Handles text, mixed types, and complex objects

### Type Conversion
- Graceful handling of type mismatches
- No exceptions thrown during comparison
- Consistent fallback behavior

## Error Messages

### Assertion Failure Format
```
Assertion Failed: Actual value 'X' does not match expected value 'Y'.
```

### Debugging Information
- Console output shows actual vs expected with types
- Clear indication of SUCCESS or FAILURE status
- Detailed logging for troubleshooting

## Common Use Cases
- **Unit Testing**: Validate individual node outputs
- **Integration Testing**: Test complete workflow results
- **Regression Testing**: Ensure changes don't break existing functionality
- **Data Validation**: Verify data transformations and calculations
- **API Testing**: Validate responses from external services
- **Mathematical Verification**: Test arithmetic and logical operations

## Testing Patterns

### Single Assertion
Simple validation of one expected outcome.

### Chain Assertions
Multiple Assert Nodes connected sequentially to test multiple conditions.

### Parallel Assertions
Multiple Assert Nodes testing different aspects of the same data.

### Conditional Testing
Combine with Decision Nodes to test different scenarios.

## Test File Integration

### JSON Test Structure
Assert Nodes are essential components of test files in the `/tests/` directory. Tests pass only when all Assert Nodes execute without throwing exceptions.

### Test Execution
- Test runner loads and executes workflow JSON files
- Monitors for AssertionError exceptions
- Reports success only when all assertions pass

## Related Nodes
- **Text Node / Number Node**: Provide expected values for comparison
- **Log Node**: For additional test logging (though uses different message types)
- **Display Output Node**: For showing test results
- **Decision Node**: For conditional test execution

## Tips & Best Practices
- Use meaningful expected values that clearly indicate test intent
- Place Assert Nodes at critical validation points in workflows
- Remember that assertion failures stop workflow execution immediately
- Use the dependency flag on `expected` input to ensure values are ready
- Chain assertions by connecting `on_success` outputs for comprehensive testing
- Monitor console output for detailed assertion information
- Consider edge cases and boundary conditions in your test values