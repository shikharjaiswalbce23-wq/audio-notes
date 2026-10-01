# Phase 4 — Object Storage

> **Status:** ✅ Implemented in Phase 4

This document covers:
- S3-compatible storage setup
- `storage_service.py` — upload, download, delete
- Why object storage instead of the database
- Environment variable configuration

---

## Why object storage instead of the database?

It is generally a bad practice to store large binary files (like audio files or images) directly in a relational database (as BLOBs). 
Reasons include:
1. **Performance:** Databases are optimized for structured data and querying. Storing large files increases database size quickly and can slow down backups and queries.
2. **Cost:** Object storage (like Amazon S3, MinIO, or Cloudflare R2) is significantly cheaper per GB compared to block storage used for databases.
3. **Scalability:** Object storage is inherently highly scalable and can serve static/media files directly via CDNs, offloading bandwidth from the main application server.

Instead, we store the file in an object storage bucket and only keep a reference (the `storage_key`) in our database.

## Environment Variable Configuration

The backend uses `boto3` to communicate with any S3-compatible object storage. 
Add the following to your `.env` file:

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name
AWS_ENDPOINT_URL= # (Optional) used for local MinIO or other providers
```

## S3-compatible Storage Setup

You can use Amazon S3, Cloudflare R2, DigitalOcean Spaces, or run a local instance of MinIO.
The application connects to the storage provider using the AWS credentials provided in the environment variables.

## storage_service.py

We created `storage_service.py` which abstracts the interactions with the object storage provider:
- `upload_file()`: Uploads the incoming audio file to the S3 bucket using `boto3`'s `upload_fileobj`.
- `download_file()`: Downloads a file to the local disk (useful later for the worker to process the audio).
- `get_file_url()`: Generates a presigned URL (useful if we want to stream the audio directly to the frontend).
- `delete_file()`: Cleans up the file from object storage when it's no longer needed.

The `main.py` upload endpoint was updated to use `storage_service.upload_file` instead of saving to the local `local_uploads` directory.
