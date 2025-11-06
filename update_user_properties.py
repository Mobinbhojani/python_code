import boto3
import csv
import os

# --- Configuration ---
# Replace with your Amazon Connect instance ID and region
CONNECT_INSTANCE_ID = 'c7906530-9561-4db1-831b-a22d671f3205'
AWS_REGION = 'us-east-1'
AWS_PROFILE_NAME = 'optum'
CSV_FILE_NAME = 'users_to_update.csv'
# --------------------

def get_user_id_by_username(client, username, instance_id):
    """Finds the User ID for a given username."""
    try:
        response = client.list_users(InstanceId=instance_id, MaxResults=1000)
        for user in response['UserSummaryList']:
            if user['Username'] == username:
                return user['Id']
        print(f"User '{username}' not found.")
        return None
    except Exception as e:
        print(f"An error occurred while fetching user ID for '{username}': {e}")
        return None

def update_users_from_csv():
    """
    Reads a CSV file and updates Amazon Connect users for each row.
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_path = os.path.join(script_dir, CSV_FILE_NAME)

        if not os.path.exists(csv_file_path):
            print(f"❌ Error: CSV file '{CSV_FILE_NAME}' not found.")
            return

        session = boto3.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION)
        client = session.client('connect')

        with open(csv_file_path, 'r', newline='') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                username = row.get('Username')
                if not username:
                    print("Skipping a row with a missing Username.")
                    continue

                user_id = get_user_id_by_username(client, username, CONNECT_INSTANCE_ID)
                if not user_id:
                    continue

                print(f"Updating user: {username} (ID: {user_id})")
                
                # Update Routing Profile
                new_routing_profile_id = row.get('NewRoutingProfileId')
                if new_routing_profile_id:
                    client.update_user_routing_profile(
                        InstanceId=CONNECT_INSTANCE_ID,
                        UserId=user_id,
                        RoutingProfileId=new_routing_profile_id
                    )
                    print("  ✅ Routing Profile updated.")

                # Update Security Profiles
                new_security_profile_ids_str = row.get('NewSecurityProfileIds')
                if new_security_profile_ids_str:
                    security_profile_ids_list = new_security_profile_ids_str.split(';')
                    client.update_user_security_profiles(
                        InstanceId=CONNECT_INSTANCE_ID,
                        UserId=user_id,
                        SecurityProfileIds=security_profile_ids_list
                    )
                    print("  ✅ Security Profiles updated.")

                # Update Hierarchy Group
                # new_hierarchy_group_id = row.get('NewHierarchyGroupId')
                # if new_hierarchy_group_id:
                #     client.update_user_hierarchy(
                #         InstanceId=CONNECT_INSTANCE_ID,
                #         UserId=user_id,
                #         HierarchyGroupId=new_hierarchy_group_id
                #     )
                    print("  ✅ Hierarchy Group updated.")
                
                print(f"✅ All updates for user '{username}' complete.")
                print("-" * 20)

    except Exception as e:
        print(f"❌ A critical error occurred: {e}")

if __name__ == "__main__":
    update_users_from_csv()