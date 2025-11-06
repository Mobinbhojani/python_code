print("--- I AM RUNNING THE NEW, CORRECT FILE ---")

import boto3
import time
import json
import os
import requests # <-- ADD THIS IMPORT

# --- Configuration ---
AWS_REGION = 'us-east-1'
AWS_PROFILE_NAME = 'optum'

# 1. SOURCE BOT (The bot with the FINAL version you want to clone)
SOURCE_BOT_ID = 'S45AWRRHVE'
SOURCE_BOT_VERSION_TO_DEPLOY = '3'
# *** MODIFIED: Set to only one locale ***
SOURCE_LOCALE_IDS = ['en_US'] 

# 2. TARGET BOT (The bot you want to update from version 3 to 4)
TARGET_BOT_ID = 'BYLIO6KSFV'
TARGET_BOT_SERVICE_ROLE_ARN = 'arn:aws:iam::085222924671:role/aws-service-role/lexv2.amazonaws.com/AWSServiceRoleForLexV2Bots_mybot'
# --------------------

def synchronize_bot_version():
    """
    Exports a specific version from a source bot and imports it into
    the DRAFT of a target bot, then creates a new version on the target bot.
    """
    session = boto3.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION)
    client = session.client('lexv2-models')

    # --- Phase 1: Export ALL Locales from the Source Bot ---
    print(f"1. Exporting Source Bot {SOURCE_BOT_ID} Version {SOURCE_BOT_VERSION_TO_DEPLOY}...")

    try:
        export_response = client.create_export(
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
    # *** FIX: Changed 'IN_PROGRESS' to 'INPROGRESS' ***
    export_status = 'INPROGRESS'
    status_response = {} 
    
    # *** FIX: Changed 'IN_PROGRESS' to 'INPROGRESS' ***
    while export_status == 'INPROGRESS':
        time.sleep(10)
        try:
            status_response = client.describe_export(exportId=export_id)
            export_status = status_response['exportStatus'].strip().upper()
            print(f"   Export Status: {status_response['exportStatus']}")
        except client.exceptions.ResourceNotFoundException:
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

    # --- Phase 2: Re-Upload and Import into Target Bot's DRAFT ---
    print(f"\n2. Starting import process for Target Bot {TARGET_BOT_ID} DRAFT...")

    try:
        # --- NEW STEP 2a: Get Target Bot Name (required for import) ---
        print("   Getting target bot name...")
        desc_bot_response = client.describe_bot(botId=TARGET_BOT_ID)
        target_bot_name = desc_bot_response['botName']
        print(f"   Target Bot Name: {target_bot_name}")

        # --- NEW STEP 2b: Download the exported file ---
        print(f"   Downloading exported file from S3...")
        response = requests.get(s3_url)
        response.raise_for_status() # Will raise an error if download failed
        exported_file_content = response.content
        print(f"   File downloaded ({len(exported_file_content)} bytes).")

        # --- NEW STEP 2c: Get a new pre-signed URL to UPLOAD the file ---
        print("   Getting pre-signed URL for import...")
        upload_url_response = client.create_upload_url()
        upload_url = upload_url_response['uploadUrl']
        import_job_id = upload_url_response['importId'] # Use this ID
        
        # --- NEW STEP 2d: Upload the file to the new URL ---
        print("   Uploading file to import location...")
        headers = {'Content-Type': 'application/zip'}
        upload_response = requests.put(upload_url, data=exported_file_content, headers=headers)
        upload_response.raise_for_status()
        print("   File uploaded successfully.")

        # --- NEW STEP 2e: Start the import (using correct parameters) ---
        print(f"   Starting import job {import_job_id}...")
        import_response = client.start_import(
            importId=import_job_id, # Use the ID from create_upload_url
            resourceSpecification={
                'botImportSpecification': {
                    'botName': target_bot_name, # <-- FIX: Use botName
                    'roleArn': TARGET_BOT_SERVICE_ROLE_ARN,
                    'dataPrivacy': {'childDirected': False},
                    'idleSessionTTLInSeconds': 300,
                }
            },
            mergeStrategy='Overwrite' # Overwrites DRAFT
            # <-- FIX: Removed fileFormat and s3Location
        )
        print("✅ Import initiated to overwrite DRAFT content.")

        # Poll/Wait for import to complete
        # *** FIX: Changed 'IN_PROGRESS' to 'INPROGRESS' ***
        import_status = 'INPROGRESS'
        desc_import = {} 
        
        # *** FIX: Changed 'IN_PROGRESS' to 'INPROGRESS' ***
        while import_status == 'INPROGRESS':
            time.sleep(10)
            try:
                desc_import = client.describe_import(importId=import_job_id)
                import_status = desc_import['importStatus'].strip().upper() 
                print(f"   Import Status: {desc_import['importStatus']}")
            except client.exceptions.ResourceNotFoundException:
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

    # --- Phase 3: Create New Version on Target Bot ---
    print(f"\n3. Creating new version on Target Bot (locking in {', '.join(SOURCE_LOCALE_IDS)})...")

    version_locale_specification = {
        locale_id: {'sourceBotVersion': 'DRAFT'}
        for locale_id in SOURCE_LOCALE_IDS
    }

    try:
        version_response = client.create_bot_version(
            botId=TARGET_BOT_ID,
            description=f"Synchronized from Source {SOURCE_BOT_ID} v{SOURCE_BOT_VERSION_TO_DEPLOY}. Includes {', '.join(SOURCE_LOCALE_IDS)}.",
            botVersionLocaleSpecification=version_locale_specification
        )
        
        new_version = version_response['botVersion']
        print(f"✨ SUCCESS! Target Bot {TARGET_BOT_ID} now has new Version: {new_version}.")
        print(f"   Build Status: {version_response['botStatus']}")
        print("\nFinal step: Remember to update the target bot's alias (e.g., PROD) to point to this new version.")

    except client.exceptions.ConflictException:
         print(f"⚠️ Error creating version: A build or version creation might already be in progress for {TARGET_BOT_ID}. Try again later.")
    except Exception as e:
        print(f"❌ Error creating version: {e}")

if __name__ == "__main__":
    synchronize_bot_version()