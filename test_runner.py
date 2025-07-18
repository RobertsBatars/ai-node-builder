# test_runner.py
import asyncio
import websockets
import json
import os
import sys
from glob import glob

# Configuration
SERVER_URI = "ws://localhost:8000/ws"
TESTS_DIR = "tests/"
TEST_FILE_PATTERN = "test_*.json"

async def run_single_test(uri, test_file_path):
    """
    Connects to the WebSocket server and runs a single workflow test.
    """
    print(f"--- Running test: {os.path.basename(test_file_path)} ---")
    try:
        with open(test_file_path, 'r') as f:
            test_data = json.load(f)
            graph_data = test_data['graph_data']
            start_node_id = str(test_data['start_node_id'])
    except (Exception, KeyError) as e:
        print(f"  ERROR: Could not read, parse, or find required keys in {test_file_path}: {e}")
        return "FAIL"

    if not start_node_id:
        print("  ERROR: No start_node_id found in the test file.")
        return "FAIL"
    
    try:
        async with websockets.connect(uri, open_timeout=5) as websocket:
            # Send the 'run' action
            await websocket.send(json.dumps({
                "action": "run",
                "graph": graph_data,
                "start_node_id": start_node_id
            }))

            # Listen for messages
            assertion_executed = False
            while True:
                try:
                    message_str = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    
                    try:
                        message_obj = json.loads(message_str)
                        msg_type = message_obj.get("type")

                        if msg_type == "engine_log":
                            message_text = message_obj.get("message", "")
                            print(f"  [SERVER] {message_text}")
                            if "Assertion Failed" in message_text or "Error in" in message_text:
                                print(f"  RESULT: Test failed with error.")
                                return "FAIL"
                            if "Workflow finished" in message_text:
                                # Only the frontend run should determine test pass/fail
                                if message_obj.get("run_id") == "frontend_run":
                                    if not assertion_executed:
                                        print(f"  ERROR: Workflow finished but no assertion was executed.")
                                        return "FAIL"
                                    else:
                                        print(f"  RESULT: Test passed.")
                                        return "PASS"
                        
                        elif msg_type == "test" and message_obj.get("source") == "node":
                            payload = message_obj.get("payload", {})
                            print(f"  [Node Event] {payload.get('node_type')}: {payload.get('data')}")
                            assertion_executed = True
                        
                        # Other message types can be ignored

                    except (json.JSONDecodeError, AttributeError):
                        print(f"  ERROR: Received invalid message from server: {message_str}")
                        return "FAIL"

                except asyncio.TimeoutError:
                    print("  ERROR: Test timed out. No 'Workflow finished' message received.")
                    return "FAIL"
                except websockets.exceptions.ConnectionClosed:
                    print("  ERROR: Connection closed unexpectedly.")
                    return "FAIL"

    except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError):
        print("\nERROR: Connection to the server failed.")
        print("Please ensure the main application is running: python main.py")
        return "ERROR"
    except Exception as e:
        print(f"  An unexpected error occurred: {e}")
        return "FAIL"

async def main():
    """
    Discovers and runs all workflow tests.
    """
    test_files = glob(os.path.join(TESTS_DIR, TEST_FILE_PATTERN))
    if not test_files:
        print(f"No test files found in '{TESTS_DIR}' matching '{TEST_FILE_PATTERN}'.")
        sys.exit(0)

    print(f"Found {len(test_files)} test(s).")
    
    results = {"PASS": 0, "FAIL": 0}
    
    for test_file in test_files:
        # To avoid complex connection management, run tests sequentially
        result = await run_single_test(SERVER_URI, test_file)
        if result == "ERROR":
            # If we can't connect to the server, abort all tests
            sys.exit(1)
        results[result] += 1
        print("-" * (len(os.path.basename(test_file)) + 16))


    print("\n--- Test Summary ---")
    print(f"  Passed: {results['PASS']}")
    print(f"  Failed: {results['FAIL']}")
    print("--------------------")

    if results["FAIL"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())