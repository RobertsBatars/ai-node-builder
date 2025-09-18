---
title: "Webhook Node"
description: "HTTP server event node that triggers workflows from external POST requests"
category: "Events"
tags: ["events", "webhook", "http", "server", "external", "integration", "api"]
author: "AI Node Builder"
version: "1.0.0"
---

# Webhook Node

## Overview
The Webhook Node is an event-driven node that starts an HTTP server and triggers workflows when it receives POST requests to a configured endpoint. This enables external systems, APIs, and services to trigger AI Node Builder workflows remotely.

## Input Sockets
This node has no input sockets - it serves as a workflow starting point triggered by external HTTP requests.

## Output Sockets
| Socket | Type | Description |
|--------|------|-------------|
| `received_data` | TEXT | The POST request body content received from the external caller |

## Widgets
- **port**: Number input (default: 8181) - The HTTP server port
  - Range: 1024 to 65535 (standard user port range)
  - Avoid system ports below 1024

- **path**: Text input (default: "/webhook") - The endpoint path to listen on
  - Must start with "/" (e.g., "/webhook", "/api/trigger", "/callback")
  - Case-sensitive path matching

## Examples

### Basic Webhook Setup
1. Add a Webhook Node to your workflow
2. Configure port (e.g., 8181) and path (e.g., "/webhook")
3. Click "Listen for Events" in the interface
4. Send a POST request to `http://localhost:8181/webhook`
5. The workflow triggers and the POST body content flows to downstream nodes

### External API Integration
Configure the webhook with path "/api/callback" and provide the URL `http://localhost:8181/api/callback` to external services that need to trigger your workflow.

### JSON Data Processing
Connect the webhook output to JSON processing nodes to handle structured data from external APIs:
Webhook Node → JSON Parser → Data Processing → Response

### Multiple Webhook Endpoints
Use multiple Webhook Nodes with different paths to create multiple endpoints on the same port or different ports for different types of integrations.

## Behavior & Execution

### Server Lifecycle
1. **Start Listening**: Creates HTTP server on specified port in a separate thread
2. **Request Handling**: Processes POST requests to the configured path
3. **Workflow Triggering**: Calls the workflow trigger callback with POST body data
4. **Stop Listening**: Cleanly shuts down the server and thread

### Threading Model
- HTTP server runs in a separate daemon thread
- Uses `asyncio.run_coroutine_threadsafe()` to safely trigger workflows
- Main asyncio event loop remains responsive during server operation

### Request Processing
- Only responds to POST requests on the configured path
- Returns 200 OK with `{"status": "ok"}` for successful requests
- Returns 404 for requests to other paths
- Passes the entire POST body as payload to the workflow

### Payload Injection
- POST request body is stored in `self.memory['initial_payload']`
- The `execute()` method retrieves this payload and outputs it
- Supports any text-based content (JSON, XML, plain text, etc.)

## HTTP Server Details

### Request Handler
- Accepts POST requests only on the configured path
- Extracts Content-Length header for proper body reading
- Decodes POST body as UTF-8 text
- Provides appropriate HTTP status responses

### Port Configuration
- Uses the standard user port range (1024-65535)
- Avoid conflicts with other services on the same port
- Consider firewall settings for external access

### Path Matching
- Exact path matching (case-sensitive)
- Must include leading "/" in configuration
- Supports any valid URL path structure

### Error Handling
- Server startup failures are logged and reported
- Invalid requests return appropriate HTTP status codes
- Thread cleanup on shutdown prevents resource leaks

## Integration Patterns

### External API Callbacks
Configure external services to POST to your webhook URL when events occur (payment completed, data updated, etc.).

### Microservice Communication
Use webhooks to receive notifications from other microservices in your architecture.

### Third-Party Integrations
Connect with services like GitHub webhooks, Stripe payments, or monitoring systems.

### IoT Device Integration
Allow IoT devices to trigger workflows by sending sensor data or alerts via HTTP POST.

## Security Considerations
- The server accepts all incoming connections on the configured port
- No built-in authentication or authorization
- Consider running behind a proxy for production use
- Validate and sanitize incoming data in downstream nodes
- Be cautious about exposing the server to external networks

## Network Configuration
- Server binds to all interfaces ('') by default
- Accessible via localhost and external IPs if network allows
- Consider firewall rules for external access
- Test connectivity from external systems before deployment

## Common Use Cases
- **API Callbacks**: Receive notifications from external services
- **External Triggers**: Allow other systems to start workflows
- **Data Ingestion**: Accept data from external sources
- **Event-Driven Processing**: Respond to external events immediately
- **Integration Hub**: Central point for receiving external data
- **Monitoring Alerts**: Trigger workflows from monitoring systems

## Troubleshooting
- **Port in use**: Change to a different port if the configured port is already occupied
- **Connection refused**: Check firewall settings and ensure server is listening
- **404 responses**: Verify the exact path configuration matches your requests
- **Threading issues**: Server runs in separate thread - ensure proper startup/shutdown

## Related Nodes
- **Display Input Event Node**: For internal UI-triggered events
- **JSON Parser Nodes**: For processing structured webhook data
- **HTTP Client Nodes**: For making outbound HTTP requests
- **Log Node**: For monitoring webhook activity

## Tips & Best Practices
- Use descriptive paths that clearly indicate the webhook purpose
- Test webhook endpoints with tools like curl or Postman
- Monitor server logs for connection and error information
- Consider implementing authentication in downstream nodes for security
- Use different ports for different environments (development, staging, production)
- Document webhook URLs and expected payload formats for external integrators
- Remember to stop listening when done to free up network resources