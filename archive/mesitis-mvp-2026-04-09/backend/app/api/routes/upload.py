import os
import uuid
import boto3
import json
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from botocore.exceptions import ClientError

router = APIRouter(prefix="/upload", tags=["Uploads"])

MINIO_URL = "http://minio:9000" 
PUBLIC_MINIO_URL = "http://localhost:9000" 
ACCESS_KEY = "admin"
SECRET_KEY = "SuperSecretPassword123!"
BUCKET_NAME = "realestate-files"

s3_client = boto3.client(
    's3',
    endpoint_url=MINIO_URL,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name='us-east-1' 
)

def ensure_bucket_exists():
    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
    except ClientError:
        s3_client.create_bucket(Bucket=BUCKET_NAME)
        policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{BUCKET_NAME}/*"]
            }]
        }
        s3_client.put_bucket_policy(Bucket=BUCKET_NAME, Policy=json.dumps(policy))

@router.post("/")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    ensure_bucket_exists()
    uploaded_urls = []
    
    for file in files:
        try:
            file_ext = os.path.splitext(file.filename)[1]
            new_filename = f"{uuid.uuid4()}{file_ext}"
            
            s3_client.upload_fileobj(
                file.file, 
                BUCKET_NAME, 
                new_filename,
                ExtraArgs={"ContentType": file.content_type}
            )
            
            file_url = f"{PUBLIC_MINIO_URL}/{BUCKET_NAME}/{new_filename}"
            uploaded_urls.append(file_url)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    return {"urls": uploaded_urls}