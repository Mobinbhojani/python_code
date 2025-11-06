import boto3
import json
import os

# --- Configuration ---
# Replace with your Amazon Connect instance ID and region
CONNECT_INSTANCE_ID = 'c7906530-9561-4db1-831b-a22d671f3205'
AWS_REGION = 'us-east-1'

# Replace with the name and description for your new routing profile
ROUTING_PROFILE_NAME = 'My-Boto3-Routing-Profile'
ROUTING_PROFILE_DESCRIPTION = 'Routing profile created with Boto3.'

# Replace with the actual Queue IDs from your instance
# You can get these using the list_queues Boto3 method.
SALES_QUEUE_ID = '4499c600-6f4e-4cfc-b4aa-4040cfdd16b4'
SUPPORT_QUEUE_ID = '1d71cf87-9153-4e0b-bb34-1aba6a711a47'
DEFAULT_OUTBOUND_QUEUE_ID = '4499c600-6f4e-4cfc-b4aa-4040cfdd16b4' # <-- NEW: You need to specify a queue ID for outbound calls


# The AWS profile name to use
AWS_PROFILE_NAME = 'optum'
# --------------------

def create_connect_routing_profile():
    """
    Creates a new Amazon Connect routing profile.
    """
    try:
        # Create a Boto3 session with the specified profile
        session = boto3.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION)
        client = session.client('connect')

        # Define the queue configurations for the routing profile
        queue_configs = [
            {
                'QueueReference': {
                    'QueueId': SALES_QUEUE_ID,
                    'Channel': 'VOICE',
                },
                'Priority': 1,
                'Delay': 0
            },
            {
                'QueueReference': {
                    'QueueId': SUPPORT_QUEUE_ID,
                    'Channel': 'VOICE',
                },
                'Priority': 2,
                'Delay': 0
            }
        ]

        # Define the channel capacities for the routing profile
        media_concurrencies = [
            {
                'Channel': 'VOICE',
                'Concurrency': 1
            },
            {
                'Channel': 'CHAT',
                'Concurrency': 1
            }
        ]

        # Create the routing profile
        print(f"Creating routing profile: {ROUTING_PROFILE_NAME}...")
        response = client.create_routing_profile(
            InstanceId=CONNECT_INSTANCE_ID,
            Name=ROUTING_PROFILE_NAME,
            Description=ROUTING_PROFILE_DESCRIPTION,
            DefaultOutboundQueueId=DEFAULT_OUTBOUND_QUEUE_ID, # <-- NEW: Required parameter
            MediaConcurrencies=media_concurrencies, # <-- Now a list
            QueueConfigs=queue_configs
        )

        print(f"✅ Routing profile '{ROUTING_PROFILE_NAME}' created successfully.")
        print(f"Routing Profile ID: {response['RoutingProfileId']}")
        print(f"Routing Profile ARN: {response['RoutingProfileArn']}")
    
    except client.exceptions.InvalidRequestException as e:
        print(f"❌ An AWS error occurred: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    create_connect_routing_profile()