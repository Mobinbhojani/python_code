import boto3
import json
import os
from datetime import datetime

# --- Configuration ---
# Replace with your Amazon Connect instance ID and region
CONNECT_INSTANCE_ID = 'c7906530-9561-4db1-831b-a22d671f3205'
AWS_REGION = 'us-east-1'

# Base name for the contact flow
CONTACT_FLOW_BASE_NAME = 'demo-boto-flow'
CONTACT_FLOW_DESCRIPTION = 'Contact flow created and published with Boto3.'
JSON_FILE_NAME = 'demo-boto-flow-v1.0.0.json'
# --------------------

# Add the profile name you want to use
AWS_PROFILE_NAME = 'optum'
# --------------------

def create_and_publish_new_flow():
    """
    Reads a JSON file and creates a new published AWS Connect contact flow.
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

        # Generate a unique name for the new flow to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        new_contact_flow_name = f"{CONTACT_FLOW_BASE_NAME}-{timestamp}"
        
        # Create a Boto3 session with the specified profile
        session = boto3.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION)

        # Create the Boto3 client for Amazon Connect
        client = session.client('connect')

        # Create the new contact flow and set its status to PUBLISHED
        print(f"Creating and publishing new contact flow: {new_contact_flow_name}...")
        response = client.create_contact_flow(
            InstanceId=CONNECT_INSTANCE_ID,
            Name=new_contact_flow_name,
            Type='CONTACT_FLOW',
            Description=CONTACT_FLOW_DESCRIPTION,
            Content=contact_flow_content,
            Status='PUBLISHED' # <-- This is the key change
        )

        print(f"✅ Successfully created and published new contact flow: {response['ContactFlowId']}")
        print(f"ARN: {response['ContactFlowArn']}")
    
    except client.exceptions.InvalidRequestException as e:
        print(f"❌ An AWS error occurred: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    create_and_publish_new_flow()