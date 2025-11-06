import boto3
import requests

# --- Configuration ---
AWS_REGION = 'us-east-1'
AWS_PROFILE_NAME = 'optum' 
ZIP_FILE_PATH = 'mybot.zip' # Path to your local ZIP file
NEW_BOT_NAME = 'my-bot'
# IAM Role ARN that grants Lex permissions (required for the new bot)
NEW_BOT_ROLE_ARN = 'arn:aws:iam::085222924671:role/aws-service-role/lexv2.amazonaws.com/AWSServiceRoleForLexV2Bots_mybot' 
# --------------------

def clone_lex_bot():
    session = boto3.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION)
    client = session.client('lexv2-models')

    try:
        # 1. Get a pre-signed URL to upload the file
        print("1. Creating upload URL...")
        upload_info = client.create_upload_url()
        upload_url = upload_info['uploadUrl']
        import_id = upload_info['importId']

        # 2. Upload the .zip file to the pre-signed URL
        print(f"2. Uploading bot definition to: {upload_url}...")
        with open(ZIP_FILE_PATH, 'rb') as f:
            headers = {'Content-Type': 'application/zip'}
            response = requests.put(upload_url, data=f, headers=headers)
            response.raise_for_status() # Raise an exception for bad status codes
        print("✅ Upload successful.")

        # 3. Start the import process to create the new bot
        print(f"3. Starting import job for new bot: {NEW_BOT_NAME}...")
        import_response = client.start_import(
            importId=import_id,
            resourceSpecification={
                'botImportSpecification': {
                    'botName': NEW_BOT_NAME,
                    'roleArn': NEW_BOT_ROLE_ARN,
                    'dataPrivacy': {'childDirected': False},
                    'idleSessionTTLInSeconds': 300,
                }
            },
            mergeStrategy='Overwrite' # Use 'FailOnConflict' if you want a clean import
        )
        
        print(f"✅ Import initiated. Import ID: {import_response['importId']}")
        print(f"New Bot Name will be: {NEW_BOT_NAME}")

    except client.exceptions.ResourceConflictException:
        print(f"⚠️ Error: Bot '{NEW_BOT_NAME}' already exists. Skipping creation.")
    except Exception as e:
        print(f"❌ A critical error occurred during cloning: {e}")

if __name__ == "__main__":
    clone_lex_bot()