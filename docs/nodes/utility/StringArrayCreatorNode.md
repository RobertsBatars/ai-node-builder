---
title: "String Array Creator Node"
description: "Converts dynamic inputs into a flattened string array with advanced configuration options"
category: "Utility"
tags: ["utility", "array", "strings", "dynamic", "configuration", "aggregation"]
author: "AI Node Builder"
version: "1.0.0"
---

# String Array Creator Node

## Overview
The String Array Creator Node is a highly configurable utility that converts dynamic array inputs into a single flattened string array. It demonstrates advanced socket configuration patterns and provides multiple behavioral modes for different use cases.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `inputs` | ANY[] | Yes | Configurable | Dynamic array input with behavior controlled by widgets |

The socket behavior is dynamically configured during the load phase based on widget settings.

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `string_array` | ANY | The processed array or single item based on configuration |

## Widgets

### Socket Behavior Control
- **wait_toggle**: Boolean (default: true) - Controls socket waiting behavior
  - **True**: Normal waiting behavior for inputs
  - **False**: Uses `do_not_wait` behavior (executes without waiting for inputs)

- **dependency_toggle**: Boolean (default: true) - Controls dependency pulling
  - **True**: Socket uses dependency pattern (pulls data when waiting)
  - **False**: Socket doesn't use dependency pattern
  - **Note**: Only applies when wait_toggle is true (do_not_wait overrides dependency)

### Processing Control
- **single_item_passthrough**: Boolean (default: true) - Output format control
  - **True**: If result has exactly one item, output the item directly instead of an array
  - **False**: Always output as an array, even for single items

- **accumulate**: Boolean (default: false) - Input accumulation behavior
  - **False**: Only uses the latest/newest input, ignoring accumulated data
  - **True**: Processes all accumulated inputs (original behavior)

## Socket Configuration Details

The node dynamically configures its input socket during the `load()` phase:

### Wait Behavior
- When `wait_toggle` is **false**: Socket gets `"do_not_wait": True`
- When `wait_toggle` is **true**: Normal waiting behavior

### Dependency Behavior
- When `dependency_toggle` is **true** AND `wait_toggle` is **true**: Socket gets `"is_dependency": True`
- Otherwise: No dependency flag (per engine priority rules)

### Priority Rules
The engine enforces that `do_not_wait` takes priority over `is_dependency`, ensuring predictable behavior.

## Processing Modes

### Accumulation Modes
- **Non-accumulating (default)**: Only processes the latest input, ideal for real-time processing
- **Accumulating**: Processes all inputs received, ideal for batch processing

### Output Modes
- **Array output**: Always returns an array `[item1, item2, ...]`
- **Single passthrough**: Returns single items directly when result contains exactly one element

## Examples

### Basic Array Creation
1. Set accumulate to true, single_item_passthrough to false
2. Connect multiple Text Nodes to the dynamic input array
3. Result: Array containing all connected text values

### Real-time Processing
1. Set accumulate to false (default)
2. Connect a dynamic source that updates frequently
3. Result: Only the most recent value is processed

### Single Item Workflow
1. Connect one input, keep single_item_passthrough as true
2. Result: The single item is output directly, not wrapped in an array

### Non-blocking Collection
1. Set wait_toggle to false for do_not_wait behavior
2. Node executes immediately without waiting for all inputs
3. Useful for collecting available data without blocking

## Behavior & Execution

### Dynamic Socket Configuration
- Socket properties are rebuilt completely during load() to prevent flag pollution
- Configuration is logged for debugging
- Changes take effect when workflow is restarted

### Input Processing
1. Determines which inputs to process based on accumulate setting
2. Flattens any nested arrays in the input
3. Handles single values by appending to result array
4. Applies output formatting based on single_item_passthrough

### Flattening Logic
- If input item is already an array/tuple: extends the result with its contents
- If input item is a single value: appends to the result
- Maintains order of processing

## Advanced Configuration Patterns

### Real-time Data Processing
```
wait_toggle: true
dependency_toggle: false  
accumulate: false
single_item_passthrough: true
```
Process latest data with dependency pulling disabled.

### Batch Collection
```
wait_toggle: true
dependency_toggle: true
accumulate: true
single_item_passthrough: false
```
Collect all inputs with dependency pulling for complete data sets.

### Non-blocking Aggregation
```
wait_toggle: false
dependency_toggle: (ignored)
accumulate: false
single_item_passthrough: true
```
Execute immediately with available data, no waiting.

## Load-time vs Runtime Configuration

This node demonstrates **load-time socket configuration** where socket behavior is determined by widget values during workflow initialization. This differs from runtime configuration patterns that use `NodeStateUpdate`.

### Configuration Timing
- Socket properties are set once during `load()`
- Changes require workflow restart to take effect
- More efficient than runtime configuration for static behavior

## Common Use Cases
- **Data Aggregation**: Collect multiple inputs into a single array
- **Real-time Processing**: Process only the latest data updates
- **Flexible Output**: Choose between array and single-item output
- **Non-blocking Collection**: Gather available data without waiting
- **Configuration Testing**: Demonstrate different socket behaviors

## Debugging Features
- Configuration logging shows final socket setup
- Execution logging shows processing mode and item counts
- Clear indication of accumulation vs. latest-only behavior

## Related Nodes
- **Text Node**: Common input source for array creation
- **Concatenate Array Node**: For joining array elements into strings
- **Counter Node**: For providing sequential inputs
- **Display Output Node**: For visualizing array results

## Tips & Best Practices
- Understanding socket configuration helps with advanced node development
- Use accumulate=false for real-time scenarios, true for batch processing
- single_item_passthrough is useful for workflows that handle variable input counts
- Test different configurations to understand socket behavior patterns
- Monitor logs to verify configuration and processing behavior
- Restart workflows when changing widget values for socket reconfiguration