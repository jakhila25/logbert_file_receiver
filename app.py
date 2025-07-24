

from fastapi import FastAPI, UploadFile, File
import shutil
import os
from dotenv import load_dotenv
load_dotenv()
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import redis
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="File Receiver Service")

# Add CORS middleware — allow all origins
# ✅ Add CORS middleware — allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # Allow all origins (wildcard)
    allow_credentials=True,
    allow_methods=["*"],            # Allow all HTTP methods
    allow_headers=["*"],            # Allow all headers
)
    
# S3 configuration (replace with your actual values or use environment variables)
#S3_BUCKET = os.getenv("S3_BUCKET", "your-s3-bucket-name")
#S3_REGION = os.getenv("S3_REGION", "us-east-1")
#S3_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "your-access-key")
#S3_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "your-secret-key")

# S3 configuration
S3_BUCKET="group13506"
S3_REGION="eu-north-1"
AWS_ACCESS_KEY_ID="AKIARVB2F2G73CRY5NS3"
AWS_SECRET_ACCESS_KEY="hKN6yDq83kEsWCKB5miv1ygw/dFH9i2dISx6fR3Y"


# Initialize S3 client
s3_client = boto3.client(
    "s3",
    region_name=S3_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)


# Redis configuration (use os.getenv for safety and support username/password)
#REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
#REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
#REDIS_QUEUE = os.getenv("REDIS_QUEUE", "logbert_uploads")
#REDIS_USERNAME = os.getenv("REDIS_USERNAME")
#REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# Redis configuration
REDIS_HOST="redis-19932.c263.us-east-1-2.ec2.redns.redis-cloud.com"
REDIS_PORT="19932"
REDIS_USERNAME="default"
REDIS_PASSWORD="SrPY3JUt6TXi33BPdDRDiW9fIplx2BJe"
REDIS_QUEUE="logbert_uploads"

redis_kwargs = dict(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)
if REDIS_USERNAME:
    redis_kwargs["username"] = REDIS_USERNAME
if REDIS_PASSWORD:
    redis_kwargs["password"] = REDIS_PASSWORD

redis_client = redis.Redis(**redis_kwargs)


@app.post("/upload/")
async def upload_log(file: UploadFile = File(...)):
    # Upload directly to S3 from UploadFile
    try:
        s3_client.upload_fileobj(file.file, S3_BUCKET, file.filename)
        s3_status = "uploaded to S3"
        # Notify Redis queue
        try:
            redis_client.lpush(REDIS_QUEUE, file.filename)
            redis_status = "queued"
        except Exception as redis_exc:
            redis_status = f"Redis queue failed: {str(redis_exc)}"
    except (BotoCoreError, ClientError) as e:
        s3_status = f"S3 upload failed: {str(e)}"
        redis_status = None

    return {
        "filename": file.filename,
        "s3_status": s3_status,
        "redis_status": redis_status
    }
