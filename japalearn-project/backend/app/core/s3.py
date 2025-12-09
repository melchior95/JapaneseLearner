"""S3/MinIO storage utilities."""
from __future__ import annotations

import io
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError

from .config import get_settings

settings = get_settings()

# Create S3 client
s3_client = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint_url,
    aws_access_key_id=settings.s3_access_key_id,
    aws_secret_access_key=settings.s3_secret_access_key,
    region_name=settings.s3_region,
)


def ensure_bucket_exists() -> None:
    """Ensure the S3 bucket exists, create if it doesn't."""
    try:
        s3_client.head_bucket(Bucket=settings.s3_bucket)
    except ClientError:
        # Bucket doesn't exist, create it
        try:
            s3_client.create_bucket(Bucket=settings.s3_bucket)
        except ClientError as e:
            print(f"Error creating bucket: {e}")


def upload_file(file_data: bytes, key: str, content_type: str = "application/octet-stream") -> str:
    """
    Upload file to S3/MinIO.

    Args:
        file_data: File bytes to upload
        key: S3 key (path) for the file
        content_type: MIME type of the file

    Returns:
        Public URL to the uploaded file
    """
    ensure_bucket_exists()

    try:
        s3_client.put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=file_data,
            ContentType=content_type,
        )

        # Generate public URL
        url = f"{settings.s3_endpoint_url}/{settings.s3_bucket}/{key}"
        return url

    except ClientError as e:
        print(f"Error uploading file: {e}")
        raise


def upload_fileobj(file_obj: BinaryIO, key: str, content_type: str = "application/octet-stream") -> str:
    """
    Upload file object to S3/MinIO.

    Args:
        file_obj: File-like object to upload
        key: S3 key (path) for the file
        content_type: MIME type of the file

    Returns:
        Public URL to the uploaded file
    """
    ensure_bucket_exists()

    try:
        s3_client.upload_fileobj(
            file_obj,
            settings.s3_bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )

        # Generate public URL
        url = f"{settings.s3_endpoint_url}/{settings.s3_bucket}/{key}"
        return url

    except ClientError as e:
        print(f"Error uploading file object: {e}")
        raise


def delete_file(key: str) -> None:
    """Delete file from S3/MinIO."""
    try:
        s3_client.delete_object(Bucket=settings.s3_bucket, Key=key)
    except ClientError as e:
        print(f"Error deleting file: {e}")
        raise


def file_exists(key: str) -> bool:
    """Check if file exists in S3/MinIO."""
    try:
        s3_client.head_object(Bucket=settings.s3_bucket, Key=key)
        return True
    except ClientError:
        return False
