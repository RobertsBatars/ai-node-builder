---
title: "Receive Event Node"
description: "Listens for internal events and starts parallel workflows"
category: "Events"
tags: ["events", "communication", "parallel", "workflows", "internal"]
author: "AI Node Builder"
version: "1.0.0"
---

# Receive Event Node

## Overview
The Receive Event Node is part of the **inter-workflow event communication system** that enables data exchange and coordination between parallel workflows. It listens for internal events with specific IDs sent by other workflows. When an event is received, it starts a new parallel workflow execution, enabling sophisticated workflow orchestration patterns.

This node works together with SendEventNode, AwaitEventNode, and ReturnEventDataNode to form a complete inter-workflow communication framework managed by the EventManager.

## Input Sockets
This node has no input sockets - it serves as a workflow starting point triggered by internal events.

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `data` | ANY | The data payload sent with the event |
| `event_id` | TEXT | The event ID this node is listening for |
| `await_id` | TEXT | Correlation ID for await/response patterns (skipped if not present) |

## Widgets
- **listen_id**: Text input (default: "event_1") - The event ID to listen for

## Examples

### Basic Event Communication
Set up parallel workflows by using Send Event Node in one workflow and Receive Event Node in another with the same event ID.

### Data Broadcasting
One workflow can send data to multiple parallel workflows by using multiple Receive Event Nodes with the same listen_id.

## Behavior & Execution
- Registers with EventManager for internal event listening
- Triggers new workflow runs when matching events are received
- Supports both simple data and await/response patterns
- Each received event creates an independent workflow execution

## Related Nodes

### Inter-Workflow Event Communication System
These nodes work together as part of the inter-workflow communication framework:
- **Send Event Node**: Sends events to trigger this node and other receivers
- **Await Event Node**: Sends events and waits for responses (extends Send Event functionality)
- **Return Event Data Node**: Sends responses back to awaiting workflows

### Other Event System Nodes
- **Display Input Event Node**: UI interaction events (not inter-workflow communication)
- **Webhook Node**: External HTTP events (not inter-workflow communication)