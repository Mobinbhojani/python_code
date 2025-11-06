import boto3
import csv
import os

# --- Configuration ---
# Replace with your Amazon Connect instance ID and region
CONNECT_INSTANCE_ID = 'c7906530-9561-4db1-831b-a22d671f3205'
AWS_REGION = 'us-east-1'

# The AWS profile name to use
AWS_PROFILE_NAME = 'optum'

# CSV file name
CSV_FILE_NAME = 'users.csv'
# --------------------

def create_users_from_csv():
    """
    Reads a CSV file and creates Amazon Connect users for each row.
    """
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_path = os.path.join(script_dir, CSV_FILE_NAME)

        if not os.path.exists(csv_file_path):
            print(f"❌ Error: CSV file '{CSV_FILE_NAME}' not found.")
            return

        # Create a Boto3 session with the specified profile
        session = boto3.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION)
        client = session.client('connect')

        with open(csv_file_path, 'r', newline='') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    # Construct the create_user parameters from the CSV row
                    user_params = {
                        'InstanceId': CONNECT_INSTANCE_ID,
                        'Username': row['Username'],
                        'IdentityInfo': {
                            'FirstName': row['FirstName'],
                            'LastName': row['LastName'],
                        },
                        'PhoneConfig': {
                            'PhoneType': 'SOFT_PHONE',
                            'AutoAccept': False,
                        },
                        'RoutingProfileId': row['RoutingProfileId'],
                        'SecurityProfileIds': [row['SecurityProfileId']],
                    }
                    
                    # Add optional HierarchyGroupId if it exists
                    if 'HierarchyGroupId' in row and row['HierarchyGroupId']:
                        user_params['HierarchyGroupId'] = row['HierarchyGroupId']
                    
                    # Call the create_user API for each row
                    print(f"Creating user: {row['Username']}...")
                    response = client.create_user(**user_params)
                    
                    print(f"✅ User '{row['Username']}' created successfully.")
                    print(f"User ID: {response['UserId']}")
                    print("-" * 20)

                except client.exceptions.InvalidRequestException as e:
                    print(f"❌ Error creating user '{row['Username']}': {e}")
                except Exception as e:
                    print(f"❌ An unexpected error occurred for user '{row['Username']}': {e}")

    except Exception as e:
        print(f"❌ A critical error occurred: {e}")

if __name__ == "__main__":
    create_users_from_csv()