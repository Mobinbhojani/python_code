import boto3

# --- Configuration ---
# Replace with your Amazon Connect instance ID and region
CONNECT_INSTANCE_ID = 'c7906530-9561-4db1-831b-a22d671f3205'
AWS_REGION = 'us-east-1'

# Specify the phone number and contact flow you want to associate
PHONE_NUMBER = '+18333079426'  # Use E.164 format, e.g., +15551234567
CONTACT_FLOW_NAME = 'demo-boto-flow-v1.0.0.json'

# The AWS profile name to use
AWS_PROFILE_NAME = 'optum'
# --------------------

def get_phone_number_id(instance_id, phone_number, client):
    """Finds the ID of a phone number by its E.164 string."""
    try:
        response = client.list_phone_numbers_v2(TargetArn=f"arn:aws:connect:{AWS_REGION}:085222924671:instance/{instance_id}")
        
        for number in response['ListPhoneNumbersSummaryList']:
            if number['PhoneNumber'] == phone_number:
                return number['PhoneNumberId']
        
        print(f"❌ Error: Phone number '{phone_number}' not found.")
        return None
    except Exception as e:
        print(f"❌ An error occurred while fetching phone number ID: {e}")
        return None

def get_contact_flow_id(instance_id, flow_name, client):
    """Finds the ID of a contact flow by its name."""
    try:
        response = client.list_contact_flows(InstanceId=instance_id)
        
        for flow in response['ContactFlowSummaryList']:
            if flow['Name'] == flow_name:
                return flow['Id']
        
        print(f"❌ Error: Contact flow '{flow_name}' not found.")
        return None
    except Exception as e:
        print(f"❌ An error occurred while fetching contact flow ID: {e}")
        return None

def associate_flow_with_phone_number():
    """Associates a contact flow with a phone number."""
    try:
        # Create a Boto3 session with the specified profile
        session = boto3.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION)
        client = session.client('connect')

        # Get the IDs for the phone number and contact flow
        phone_number_id = get_phone_number_id(CONNECT_INSTANCE_ID, PHONE_NUMBER, client)
        contact_flow_id = get_contact_flow_id(CONNECT_INSTANCE_ID, CONTACT_FLOW_NAME, client)

        if not phone_number_id or not contact_flow_id:
            return

        print(f"Associating phone number '{PHONE_NUMBER}' with contact flow '{CONTACT_FLOW_NAME}'...")
        
        # Use the associate_phone_number_contact_flow API call
        client.associate_phone_number_contact_flow(
            InstanceId=CONNECT_INSTANCE_ID,
            PhoneNumberId=phone_number_id,
            ContactFlowId=contact_flow_id
        )

        print("✅ Association successful.")
    
    except client.exceptions.InvalidRequestException as e:
        print(f"❌ An AWS error occurred: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    associate_flow_with_phone_number()