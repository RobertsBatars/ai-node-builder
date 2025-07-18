# test_webhook.py
import requests
import json

# Configuration
# Make sure this matches the port and path set in your WebhookNode in the UI.
WEBHOOK_URL = "http://localhost:8181/webhook"

def trigger_event():
    """
    Sends a POST request to the webhook URL to trigger the event workflow.
    """
    print(f"Sending POST request to {WEBHOOK_URL}...")
    
    # You can send any data you want in the body.
    # A more advanced WebhookNode could parse this and pass it into the workflow.
    payload = {
        "source": "test_script",
        "message": "Hello from the test script!"
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(WEBHOOK_URL, data=json.dumps(payload), headers=headers, timeout=5)
        
        # Check if the request was successful
        response.raise_for_status()
        
        print("Request successful.")
        print("Response from server:", response.json())

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        print("Please ensure the main application is running and you have clicked 'Listen for Events' with a WebhookNode in the graph.")

if __name__ == "__main__":
    trigger_event()
