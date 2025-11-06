import boto3
import json
import os

# --- Configuration ---
# Replace with your Amazon Connect instance ID and region
CONNECT_INSTANCE_ID = 'c7906530-9561-4db1-831b-a22d671f3205'
AWS_REGION = 'us-east-1'

# Replace with your desired name and description
MODULE_NAME = 'Maint-Module'
MODULE_DESCRIPTION = 'A module for maintaining customer information.'

# The JSON file containing the module content
JSON_FILE_NAME = 'contact_flow_module.json'

# The AWS profile name to use
AWS_PROFILE_NAME = 'optum'
# --------------------

def create_connect_flow_module():
    """
    Reads a JSON file and creates a new Amazon Connect Contact Flow Module.
    """
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(script_dir, JSON_FILE_NAME)

        if not os.path.exists(json_file_path):
            print(f"❌ Error: JSON file '{JSON_FILE_NAME}' not found.")
            return

        with open(json_file_path, 'r') as file:
            module_content = file.read()

        try:
            # Validate if the content is valid JSON before sending
            json.loads(module_content)
        except json.JSONDecodeError:
            print(f"❌ Error: The file '{JSON_FILE_NAME}' is not a valid JSON.")
            return

        # Create a Boto3 session with the specified profile
        session = boto3.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION)
        client = session.client('connect')

        # Use the create_contact_flow_module method
        print(f"Creating Contact Flow Module: {MODULE_NAME}...")
        response = client.create_contact_flow_module(
            InstanceId=CONNECT_INSTANCE_ID,
            Name=MODULE_NAME,
            Description=MODULE_DESCRIPTION,
            Content=module_content
        )

        print(f"✅ Successfully created Contact Flow Module: {response['Id']}")
        print(f"Module ARN: {response['Arn']}")
    
    except client.exceptions.InvalidRequestException as e:
        print(f"❌ An AWS error occurred: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    create_connect_flow_module()