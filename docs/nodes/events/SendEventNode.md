---
title: "Send Event Node"
description: "Sends events to parallel workflows using event IDs"
category: "Events"
tags: ["events", "communication", "parallel", "workflows", "send"]
author: "AI Node Builder"
version: "1.0.0"
---

# Send Event Node

## Overview
The Send Event Node is part of the **inter-workflow event communication system** that enables data exchange and coordination between parallel workflows. It sends events to parallel workflows that are listening for specific event IDs through ReceiveEventNodes. It supports both single event IDs and arrays of event IDs, enabling one-to-many communication patterns between workflows.

This node works together with ReceiveEventNode, AwaitEventNode, and ReturnEventDataNode to form a complete inter-workflow communication framework managed by the EventManager.

## Input Sockets
| Socket | Type | Required | Is Dependency | Description |
|--------|------|----------|---------------|-------------|
| `event_ids` | ANY | No | Yes | Event ID(s) to send to (string or array) |
| `data` | ANY | Yes | No | Data payload to send with the event |

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `sent_count` | NUMBER | Number of events successfully sent |

## Widgets
- **event_id_widget**: Text input (default: "event_1") - Fallback event ID when no input connected

## Examples

### Basic Event Sending
Connect a Text Node with "event_1" to event_ids input and any data source to the data input. Events will be sent to all workflows listening for "event_1".

### Broadcasting to Multiple Events
Connect an array of event IDs to send the same data to multiple different event listeners simultaneously.

## Behavior & Execution
- Detects whether event_ids input is a single string or array
- Sends events through EventManager to registered listeners
- Returns count of successfully sent events
- Uses widget fallback when no event_ids input is connected

## Related Nodes

### Inter-Workflow Event Communication System
These nodes work together as part of the inter-workflow communication framework:
- **Receive Event Node**: Receives and processes events sent by this node
- **Await Event Node**: Extended version that sends events and waits for responses
- **Return Event Data Node**: Completes request/response cycles started by Await Event Node

### Utility Nodes
- **String Array Creator Node**: For creating arrays of event IDs to send to multiple recipients

### Other Event System Nodes
- **Display Input Event Node**: UI interaction events (not inter-workflow communication)
- **Webhook Node**: External HTTP events (not inter-workflow communication)