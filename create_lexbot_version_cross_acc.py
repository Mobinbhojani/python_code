# This script is to upgrade lex bot versions across AWS accounts using boto3.

print("--- I AM RUNNING THE NEW, CORRECT FILE ---")

import boto3
import time
import requests 

# --- Configuration ---
# *** MODIFIED: Added separate configs for Source (Account A) and Target (Account B) ***

# 1. SOURCE ACCOUNT (Account A - where the bot is exported FROM)
SOURCE_AWS_PROFILE = 'optum' # <-- Your AWS CLI profile for Account A
SOURCE_AWS_REGION = 'us-east-1'
SOURCE_BOT_ID = 'S45AWRRHVE'
SOURCE_BOT_VERSION_TO_DEPLOY = '3'

# 2. TARGET ACCOUNT (Account B - where the bot is imported TO)
TARGET_AWS_PROFILE = 'mobin28' # <-- Your AWS CLI profile for Account B
TARGET_AWS_REGION = 'us-east-1'
TARGET_BOT_ID = 'JJXVBBSFFI'
TARGET_BOT_SERVICE_ROLE_ARN = 'arn:aws:iam::186615815686:role/aws-service-role/lexv2.amazonaws.com/AWSServiceRoleForLexV2Bots_OJK0QJFFBMD' # <-- Make sure this ARN is for Account B!
SOURCE_LOCALE_IDS = ['en_US'] 
# --------------------

def synchronize_bot_version():
    """
    Exports a bot from a SOURCE ACCOUNT and imports it into a TARGET ACCOUNT.
    """

    # *** MODIFIED: Create two separate clients for each account ***
    
    # Client for Account A (Source)
    source_session = boto3.Session(profile_name=SOURCE_AWS_PROFILE, region_name=SOURCE_AWS_REGION)
    source_client = source_session.client('lexv2-models')
    
    # Client for Account B (Target)
    target_session = boto3.Session(profile_name=TARGET_AWS_PROFILE, region_name=TARGET_AWS_REGION)
    target_client = target_session.client('lexv2-models')

    # --- Phase 1: Export from Source Account (Account A) ---
    print(f"1. Exporting Source Bot {SOURCE_BOT_ID} (Account A) Version {SOURCE_BOT_VERSION_TO_DEPLOY}...")

    try:
        # *** MODIFIED: Use source_client ***
        export_response = source_client.create_export(
            resourceSpecification={
                'botExportSpecification': {
                    'botId': SOURCE_BOT_ID,
                    'botVersion': SOURCE_BOT_VERSION_TO_DEPLOY,
                }
            },
            fileFormat='LexJson'
        )
        export_id = export_response['exportId']

    except Exception as e:
        print(f"❌ Failed to start export: {e}")
        return

    # Poll/Wait for export to complete
    export_status = 'INPROGRESS'
    status_response = {} 
    
    while export_status == 'INPROGRESS':
        time.sleep(10)
        try:
            # *** MODIFIED: Use source_client ***
            status_response = source_client.describe_export(exportId=export_id)
            export_status = status_response['exportStatus'].strip().upper()
            print(f"   Export Status: {status_response['exportStatus']}")
        except source_client.exceptions.ResourceNotFoundException:
            print(f"❌ Export job {export_id} not found. Aborting.")
            return
        except Exception as e:
            print(f"❌ Error checking export status: {e}")
            return

    # --- Loop has exited. Now check the FINAL status robustly ---
    s3_url = "" 
    if export_status == 'COMPLETED' and 'downloadUrl' in status_response:
        print(f"✅ Export completed successfully.")
        s3_url = status_response['downloadUrl']
    elif export_status == 'FAILED':
        print(f"❌ Export failed with status: FAILED. Aborting.")
        if 'failureReasons' in status_response:
             print(f"     Failure Reasons: {status_response['failureReasons']}")
        return
    elif export_status == 'COMPLETED':
        print(f"❌ Export completed, but 'downloadUrl' was not found in the response.")
        print(f"   DEBUG: Full response: {status_response}")
        return
    else:
        print(f"❌ Export finished with unexpected status: {export_status}. Aborting.")
        print(f"   DEBUG: Full response: {status_response}")
        return

    # --- Phase 2: Re-Upload and Import into Target Account (Account B) ---
    print(f"\n2. Starting import process for Target Bot {TARGET_BOT_ID} (Account B) DRAFT...")

    try:
        # --- Step 2a: Get Target Bot Name (from Account B) ---
        print("   Getting target bot name...")
        # *** MODIFIED: Use target_client ***
        desc_bot_response = target_client.describe_bot(botId=TARGET_BOT_ID)
        target_bot_name = desc_bot_response['botName']
        print(f"   Target Bot Name: {target_bot_name}")

        # --- Step 2b: Download the exported file (from Account A's S3) ---
        print(f"   Downloading exported file from S3...")
        response = requests.get(s3_url) # This URL is pre-signed, so no auth is needed
        response.raise_for_status() 
        exported_file_content = response.content
        print(f"   File downloaded ({len(exported_file_content)} bytes).")

        # --- Step 2c: Get a new pre-signed URL (from Account B) ---
        print("   Getting pre-signed URL for import...")
        # *** MODIFIED: Use target_client ***
        upload_url_response = target_client.create_upload_url()
        upload_url = upload_url_response['uploadUrl']
        import_job_id = upload_url_response['importId'] 
        
        # --- Step 2d: Upload the file (to Account B's S3) ---
        print("   Uploading file to import location...")
        headers = {'Content-Type': 'application/zip'}
        upload_response = requests.put(upload_url, data=exported_file_content, headers=headers) # This URL is also pre-signed
        upload_response.raise_for_status()
        print("   File uploaded successfully.")

        # --- Step 2e: Start the import (in Account B) ---
        print(f"   Starting import job {import_job_id}...")
        # *** MODIFIED: Use target_client ***
        import_response = target_client.start_import(
            importId=import_job_id, 
            resourceSpecification={
                'botImportSpecification': {
                    'botName': target_bot_name, 
                    'roleArn': TARGET_BOT_SERVICE_ROLE_ARN,
                    'dataPrivacy': {'childDirected': False},
                    'idleSessionTTLInSeconds': 300,
                }
            },
            mergeStrategy='Overwrite' 
        )
        print("✅ Import initiated to overwrite DRAFT content.")

        # Poll/Wait for import to complete
        import_status = 'INPROGRESS'
        desc_import = {} 
        
        while import_status == 'INPROGRESS':
            time.sleep(10)
            try:
                # *** MODIFIED: Use target_client ***
                desc_import = target_client.describe_import(importId=import_job_id)
                import_status = desc_import['importStatus'].strip().upper() 
                print(f"   Import Status: {desc_import['importStatus']}")
            except target_client.exceptions.ResourceNotFoundException:
                print(f"❌ Import job {import_job_id} not found. Aborting.")
                return
            except Exception as e:
                print(f"❌ Error checking import status: {e}")
                return

        if import_status != 'COMPLETED':
            print(f"  ❌ Import failed for {TARGET_BOT_ID}. Status: {import_status}. Cannot create version.")
            if 'failureReasons' in desc_import:
                 print(f"     Failure Reasons: {desc_import['failureReasons']}")
            return

    except requests.exceptions.RequestException as e:
        print(f"❌ Error during file download/upload: {e}")
        return
    except Exception as e:
        print(f"❌ Error during import: {e}")
        return

    # --- Phase 3: Create New Version on Target Bot (in Account B) ---
    print(f"\n3. Creating new version on Target Bot (locking in {', '.join(SOURCE_LOCALE_IDS)})...")

    version_locale_specification = {
        locale_id: {'sourceBotVersion': 'DRAFT'}
        for locale_id in SOURCE_LOCALE_IDS
    }

    try:
        # *** MODIFIED: Use target_client ***
        version_response = target_client.create_bot_version(
            botId=TARGET_BOT_ID,
            description=f"Synchronized from Source {SOURCE_BOT_ID} v{SOURCE_BOT_VERSION_TO_DEPLOY}. Includes {', '.join(SOURCE_LOCALE_IDS)}.",
            botVersionLocaleSpecification=version_locale_specification
        )
        
        new_version = version_response['botVersion']
        print(f"✨ SUCCESS! Target Bot {TARGET_BOT_ID} now has new Version: {new_version}.")
        print(f"   Build Status: {version_response['botStatus']}")
        print("\nFinal step: Remember to update the target bot's alias (e.g., PROD) to point to this new version.")

    except target_client.exceptions.ConflictException:
         print(f"⚠️ Error creating version: A build or version creation might already be in progress for {TARGET_BOT_ID}. Try again later.")
    except Exception as e:
        print(f"❌ Error creating version: {e}")

if __name__ == "__main__":
    synchronize_bot_version()