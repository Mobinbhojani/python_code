import boto3
import json
import os

# --- Configuration ---
# Replace with your Amazon Connect instance ID and region
CONNECT_INSTANCE_ID = 'c7906530-9561-4db1-831b-a22d671f3205'
AWS_REGION = 'us-east-1'

# The ID of the existing contact flow you want to update
CONTACT_FLOW_ID = '3f794682-2984-4716-acc2-308e74fc80bf'

# The JSON file containing the new flow content
JSON_FILE_NAME = 'demo-boto-flow-v1.0.0.json'

# The AWS profile name to use
AWS_PROFILE_NAME = 'optum'
# --------------------

def update_existing_contact_flow():
    """
    Reads a JSON file and updates an existing AWS Connect contact flow.
    """
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(script_dir, JSON_FILE_NAME)

        if not os.path.exists(json_file_path):
            print(f"❌ Error: JSON file '{JSON_FILE_NAME}' not found.")
            return

        with open(json_file_path, 'r') as file:
            contact_flow_content = file.read()

        try:
            json.loads(contact_flow_content)
        except json.JSONDecodeError:
            print(f"❌ Error: The file '{JSON_FILE_NAME}' is not valid JSON.")
            return

        # Create a Boto3 session with the specified profile
        session = boto3.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION)

        # Create the Boto3 client for Amazon Connect
        client = session.client('connect')

        # Update the content of the existing contact flow
        print(f"Updating content for flow ID: {CONTACT_FLOW_ID}...")
        response = client.update_contact_flow_content(
            InstanceId=CONNECT_INSTANCE_ID,
            ContactFlowId=CONTACT_FLOW_ID,
            Content=contact_flow_content
        )

        print("✅ Content updated successfully.")
        print("Note: The flow has been updated but is not yet published. You must manually publish the changes in the Amazon Connect console.")
    
    except client.exceptions.InvalidRequestException as e:
        print(f"❌ An AWS error occurred: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    update_existing_contact_flow()