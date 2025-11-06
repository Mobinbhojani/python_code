import boto3

# --- Configuration ---
# Replace with your Amazon Connect instance ID and region
CONNECT_INSTANCE_ID = 'c7906530-9561-4db1-831b-a22d671f3205'
AWS_REGION = 'us-east-1'

# Replace with the IDs from your Amazon Connect instance
ROUTING_PROFILE_ID = '99cdaa29-d249-48b1-a08a-dee5a83308e6'
SECURITY_PROFILE_IDS = ['94c46866-5689-45f9-bcb8-eabd06a1ab7a'] # grab it from aws cli
HIERARCHY_GROUP_ID = 'your_hierarchy_group_id' # Optional

# New user's details
USER_LOGIN_NAME = 'Mobinpy'
USER_FIRST_NAME = 'Mobin'
USER_LAST_NAME = 'Bhojani'
USER_PASSWORD = 'Iq123456' # AWS will hash this. Ensure it meets password policy.
# --------------------

# Add the profile name you want to use
AWS_PROFILE_NAME = 'optum'
# --------------------

def create_connect_user():
    """
    Creates a new Amazon Connect user with the specified settings.
    """
    try:

        # Create a Boto3 session with the specified profile
        session = boto3.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION)

        # Create the Boto3 client for Amazon Connect
        client = session.client('connect')

        # Create the user
        response = client.create_user(
            InstanceId=CONNECT_INSTANCE_ID,
            Username=USER_LOGIN_NAME,
            PhoneConfig={
                'PhoneType': 'SOFT_PHONE',
                'AutoAccept': False,
            },
            RoutingProfileId=ROUTING_PROFILE_ID,
            SecurityProfileIds=SECURITY_PROFILE_IDS,
            IdentityInfo={
                'FirstName': USER_FIRST_NAME,
                'LastName': USER_LAST_NAME,
            },
            Tags={
                'Environment': 'dev',
                'ManagedBy': 'boto3-script'
            }
        )

        print(f"✅ User '{USER_LOGIN_NAME}' created successfully.")
        print(f"User ID: {response['UserId']}")
        print(f"User ARN: {response['UserArn']}")
    
    except client.exceptions.InvalidRequestException as e:
        print(f"❌ An AWS error occurred: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    create_connect_user()