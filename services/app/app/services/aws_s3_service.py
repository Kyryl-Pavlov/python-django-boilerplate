import os

import boto3
from botocore.exceptions import ClientError


def make_s3_client(public: bool = False):
    endpoint = (
        os.getenv("AWS_S3_PUBLIC_ENDPOINT_URL")
        if public
        else os.getenv("AWS_S3_ENDPOINT_URL")
    )
    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        endpoint_url=endpoint,
    )


def ensure_bucket(s3, bucket: str) -> None:
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchBucket"):
            s3.create_bucket(Bucket=bucket)


def upload_file(file_obj, user_id: str, filename: str) -> str:
    bucket = os.getenv("AWS_S3_BUCKET", "media-bucket")
    key = f"media/{user_id}/{filename}"
    s3 = make_s3_client()
    ensure_bucket(s3, bucket)
    s3.upload_fileobj(file_obj, bucket, key)
    return key


def get_presigned_url(s3_key: str) -> str:
    bucket = os.getenv("AWS_S3_BUCKET", "media-bucket")
    expiry = int(os.getenv("PRESIGNED_URL_EXPIRY", 86400))
    return make_s3_client(public=True).generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": s3_key},
        ExpiresIn=expiry,
    )
