from google.cloud import storage
from google.api_core.exceptions import NotFound, Forbidden
import tempfile
import os

bucket_name = "all-ai-jobs"

with tempfile.TemporaryDirectory(dir="../") as temp_dir:
    file_name = "job-xyz.py"
    file_path = os.path.join(temp_dir, file_name)

    # Write the file to the temp path
    with open(file_path, 'w') as file:
        file.write("print('Hello, World!')")

    # Upload script to Google Cloud Storage
    try:
        # Initialize GCS client
        client = storage.Client(project="orchestrai-456719")
        bucket = client.bucket(bucket_name)
        
        # Verify bucket exists
        bucket_exists = bucket.exists()
        if not bucket_exists:
            raise ValueError(f"Bucket {bucket_name} does not exist")

        # Upload the script
        blob = bucket.blob(file_name)
        blob.upload_from_filename(file_path)
        print(f"Uploaded {file_path} to gs://{file_name}")
    except (NotFound, Forbidden, ValueError) as e:
        print(f"Failed to upload script to GCS: {str(e)}")
    except Exception as e:
        print(f"Unexpected error during GCS upload: {str(e)}")
