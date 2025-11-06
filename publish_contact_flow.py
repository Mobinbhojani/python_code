import boto3
import json
import os

# --- Configuration ---
# Replace with your Amazon Connect instance ID and region
CONNECT_INSTANCE_ID = 'c7906530-9561-4db1-831b-a22d671f3205'
AWS_REGION = 'us-east-1'

# Replace with the ID of the existing contact flow you want to update
CONTACT_FLOW_ID = '7a77f53a-1e18-449a-9b9c-6c73cb28511c'

# The name and description of the flow to be updated. This is for reference.
CONTACT_FLOW_NAME = 'demo-boto-flow-20251013-112048'
CONTACT_FLOW_DESCRIPTION = 'Updated contact flow from local JSON file.'

# The JSON file containing the new flow content
JSON_FILE_NAME = 'demo-boto-flow-v1.0.1.json'
# --------------------

# Add the profile name you want to use
AWS_PROFILE_NAME = 'optum'
# --------------------

def update_and_publish_contact_flow():
    """
    Reads a JSON file, updates an existing AWS Connect contact flow,
    and publishes a new version.
    """
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(script_dir, JSON_FILE_NAME)

        # Check if the JSON file exists
        if not os.path.exists(json_file_path):
            print(f"❌ Error: JSON file '{JSON_FILE_NAME}' not found in the script's directory.")
            return

        # Read the content of the JSON file
        with open(json_file_path, 'r') as file:
            contact_flow_content = file.read()

        # Validate if the content is valid JSON
        try:
            json.loads(contact_flow_content)
        except json.JSONDecodeError:
            print(f"❌ Error: The file '{JSON_FILE_NAME}' is not a valid JSON.")
            return

        # Create a Boto3 session with the specified profile
        session = boto3.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION)

        # Create the Boto3 client for Amazon Connect
        client = session.client('connect')

        # Step 1: Update the content of the existing contact flow
        print(f"Updating content for flow ID: {CONTACT_FLOW_ID}...")
        update_response = client.update_contact_flow_content(
            InstanceId=CONNECT_INSTANCE_ID,
            ContactFlowId=CONTACT_FLOW_ID,
            Content=contact_flow_content
        )
        print("✅ Content updated successfully.")

        # Step 2: Publish a new version of the contact flow
        # This will create a new immutable version of the flow with a new version number.
        print("Publishing a new version of the flow...")
        publish_response = client.create_contact_flow_version(
            InstanceId=CONNECT_INSTANCE_ID,
            ContactFlowId=CONTACT_FLOW_ID,
            Description=CONTACT_FLOW_DESCRIPTION 
        )

        print(f"✅ Successfully published new version: {publish_response['Version']}")
        print(f"ARN: {publish_response['ContactFlowArn']}")
    
    except client.exceptions.InvalidRequestException as e:
        print(f"❌ An AWS error occurred: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    update_and_publish_contact_flow()