import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

# S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL") # Useful for MinIO or alternative providers
if AWS_ENDPOINT_URL == "":
    AWS_ENDPOINT_URL = None

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
    endpoint_url=AWS_ENDPOINT_URL
)

def upload_file(file_obj, storage_key, content_type=None):
    """Uploads a file-like object to S3."""
    if not S3_BUCKET_NAME:
        raise ValueError("S3_BUCKET_NAME environment variable is not set")
    
    extra_args = {}
    if content_type:
        extra_args["ContentType"] = content_type

    try:
        s3_client.upload_fileobj(file_obj, S3_BUCKET_NAME, storage_key, ExtraArgs=extra_args)
        return True
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        return False

def download_file(storage_key, download_path):
    """Downloads a file from S3 to a local path."""
    if not S3_BUCKET_NAME:
        raise ValueError("S3_BUCKET_NAME environment variable is not set")
        
    try:
        s3_client.download_file(S3_BUCKET_NAME, storage_key, download_path)
        return True
    except ClientError as e:
        print(f"Error downloading from S3: {e}")
        return False

def get_file_url(storage_key, expiration=3600):
    """Generates a presigned URL for the given storage key."""
    if not S3_BUCKET_NAME:
        raise ValueError("S3_BUCKET_NAME environment variable is not set")
        
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': storage_key},
            ExpiresIn=expiration
        )
        return response
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return None

def delete_file(storage_key):
    """Deletes a file from S3."""
    if not S3_BUCKET_NAME:
        raise ValueError("S3_BUCKET_NAME environment variable is not set")
        
    try:
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=storage_key)
        return True
    except ClientError as e:
        print(f"Error deleting from S3: {e}")
        return False
