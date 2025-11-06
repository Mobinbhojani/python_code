import boto3
import json
import os

# --- Configuration ---
# Replace with your Amazon Connect instance ID and region
CONNECT_INSTANCE_ID = 'c7906530-9561-4db1-831b-a22d671f3205'
AWS_REGION = 'us-east-1'

# Replace with your desired contact flow name and description
CONTACT_FLOW_NAME = 'demo-boto-flow-v1.0.0.json'
CONTACT_FLOW_DESCRIPTION = 'Contact flow created from a local JSON file.'
JSON_FILE_NAME = 'demo-boto-flow-v1.0.0.json'
# --------------------

# Add the profile name you want to use
AWS_PROFILE_NAME = 'optum'
# --------------------

def create_contact_flow_from_file():
    """
    Reads a JSON file and creates an AWS Connect contact flow.
    """
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(script_dir, JSON_FILE_NAME)

        # Check if the JSON file exists
        if not os.path.exists(json_file_path):
            print(f"Error: JSON file '{JSON_FILE_NAME}' not found in the script's directory.")
            return

        # Read the content of the JSON file
        with open(json_file_path, 'r') as file:
            contact_flow_content = file.read()

        # Validate if the content is valid JSON
        try:
            json.loads(contact_flow_content)
        except json.JSONDecodeError:
            print(f"Error: The file '{JSON_FILE_NAME}' is not a valid JSON.")
            return

        # Create a Boto3 session with the specified profile
        session = boto3.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION)

        # Create the Boto3 client for Amazon Connect
        client = session.client('connect')

        # Use the create_contact_flow method
        response = client.create_contact_flow(
            InstanceId=CONNECT_INSTANCE_ID,
            Name=CONTACT_FLOW_NAME,
            Type='CONTACT_FLOW',
            Description=CONTACT_FLOW_DESCRIPTION,
            Content=contact_flow_content
        )

        print(f"✅ Successfully created contact flow: {response['ContactFlowId']}")
        print(f"ARN: {response['ContactFlowArn']}")
    
    except boto3.exceptions.botocore.exceptions.ClientError as e:
        print(f"❌ An AWS error occurred: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    create_contact_flow_from_file()