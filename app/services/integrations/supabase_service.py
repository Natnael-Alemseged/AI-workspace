"""Supabase service for media storage using S3 protocol."""
import mimetypes
import os
from datetime import timedelta
from typing import Optional, Any
from uuid import uuid4

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError

from app.core.config import (
    SUPABASE_BUCKET,
    SUPABASE_S3_ACCESS_KEY_ID,
    SUPABASE_S3_SECRET_ACCESS_KEY,
    SUPABASE_S3_ENDPOINT_URL,
    SUPABASE_S3_REGION_NAME, SUPABASE_PROJECT_REF,
)
from app.core.logging import logger


class SupabaseService:
    """Service for handling Supabase storage operations via S3 protocol."""
    
    _client: Optional[Any] = None
    
    @classmethod
    def get_client(cls) -> Any:
        """Get or create S3 client."""
        if cls._client is None:
            if not SUPABASE_S3_ACCESS_KEY_ID or not SUPABASE_S3_SECRET_ACCESS_KEY:
                raise ValueError(
                    "SUPABASE_S3_ACCESS_KEY_ID and SUPABASE_S3_SECRET_ACCESS_KEY must be set in environment variables"
                )
            
            cls._client = boto3.client(
                's3',
                aws_access_key_id=SUPABASE_S3_ACCESS_KEY_ID,
                aws_secret_access_key=SUPABASE_S3_SECRET_ACCESS_KEY,
                endpoint_url=SUPABASE_S3_ENDPOINT_URL,
                region_name=SUPABASE_S3_REGION_NAME,
                config=BotoConfig(signature_version='s3v4')
            )
            logger.info("Supabase S3 client initialized")
        return cls._client
    
    @classmethod
    async def upload_file(
        cls,
        file_content: bytes = None,
        filename: str = None,
        content_type: Optional[str] = None,
        folder: str = "chat",
        file_obj: Any = None
    ) -> dict:
        """
        Upload a file to Supabase storage via S3.
        
        Args:
            file_content: File content as bytes (optional if file_obj provided)
            filename: Original filename
            content_type: MIME type of the file
            folder: Folder path in the bucket
            file_obj: File-like object to stream (preferred over file_content)
            
        Returns:
            dict with url, path, and metadata
        """
        try:
            client = cls.get_client()
            
            if not filename:
                raise ValueError("Filename is required")

            # Generate unique filename
            file_ext = os.path.splitext(filename)[1]
            unique_filename = f"{uuid4()}{file_ext}"
            file_path = f"{folder}/{unique_filename}"
            
            # Detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = "application/octet-stream"
            
            # Upload file
            logger.debug(f"Uploading to bucket: {SUPABASE_BUCKET}, path: {file_path}")
            
            try:
                # Determine body and size
                if file_obj:
                    body = file_obj
                    # Try to get size if possible, but it's not strictly required for put_object
                    # If we need size for return value, we might need to seek/tell or use fstat
                    try:
                        file_obj.seek(0, os.SEEK_END)
                        size = file_obj.tell()
                        file_obj.seek(0)
                    except Exception:
                        size = 0 # Unknown size
                elif file_content:
                    body = file_content
                    size = len(file_content)
                else:
                    raise ValueError("Either file_content or file_obj must be provided")

                client.put_object(
                    Bucket=SUPABASE_BUCKET,
                    Key=file_path,
                    Body=body,
                    ContentType=content_type,
                    ACL='public-read' # Assuming public bucket, otherwise remove or change
                )
            except ClientError as e:
                logger.error(f"Upload failed - Bucket: {SUPABASE_BUCKET}, Path: {file_path}")
                logger.error(f"Upload error details: {str(e)}")
                raise ValueError(f"Failed to upload file to Supabase storage: {str(e)}")
            
            logger.info(f"File uploaded to Supabase: {file_path}")
            
            # Construct public URL
            public_url = f"https://{SUPABASE_PROJECT_REF}.supabase.co/storage/v1/object/public/{SUPABASE_BUCKET}/{file_path}"
            
            return {
                "url": public_url,
                "path": file_path,
                "filename": filename,
                "content_type": content_type,
                "size": size
            }
            
        except Exception as e:
            logger.error(f"Error uploading file to Supabase: {e}")
            raise
    
    @classmethod
    async def get_signed_upload_url(
        cls,
        filename: str,
        folder: str = "chat",
        expires_in: int = 3600
    ) -> dict:
        """
        Generate a signed URL for direct client-side upload.
        
        Args:
            filename: Original filename
            folder: Folder path in the bucket
            expires_in: URL expiration time in seconds
            
        Returns:
            dict with signed_url and file_path
        """
        try:
            client = cls.get_client()
            
            # Generate unique filename
            file_ext = os.path.splitext(filename)[1]
            unique_filename = f"{uuid4()}{file_ext}"
            file_path = f"{folder}/{unique_filename}"
            
            # Create signed upload URL
            signed_url = client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': SUPABASE_BUCKET,
                    'Key': file_path,
                    'ContentType': mimetypes.guess_type(filename)[0] or 'application/octet-stream'
                },
                ExpiresIn=expires_in
            )
            
            logger.info(f"Generated signed upload URL for: {file_path}")
            
            return {
                "signed_url": signed_url,
                "path": file_path,
                "expires_in": expires_in
            }
            
        except Exception as e:
            logger.error(f"Error generating signed upload URL: {e}")
            raise
    
    @classmethod
    async def get_signed_url(
        cls,
        file_path: str,
        expires_in: int = 3600
    ) -> str:
        """
        Get a signed URL for accessing a private file.
        
        Args:
            file_path: Path to the file in the bucket
            expires_in: URL expiration time in seconds
            
        Returns:
            Signed URL string
        """
        try:
            client = cls.get_client()
            
            signed_url = client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': SUPABASE_BUCKET,
                    'Key': file_path
                },
                ExpiresIn=expires_in
            )
            
            return signed_url
            
        except Exception as e:
            logger.error(f"Error generating signed URL: {e}")
            raise
    
    @classmethod
    async def delete_file(cls, file_path: str) -> bool:
        """
        Delete a file from Supabase storage.
        
        Args:
            file_path: Path to the file in the bucket
            
        Returns:
            True if successful
        """
        try:
            client = cls.get_client()
            
            client.delete_object(Bucket=SUPABASE_BUCKET, Key=file_path)
            
            logger.info(f"File deleted from Supabase: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file from Supabase: {e}")
            raise
    
    @classmethod
    async def list_files(cls, folder: str = "chat", limit: int = 100) -> list:
        """
        List files in a folder.
        
        Args:
            folder: Folder path in the bucket
            limit: Maximum number of files to return
            
        Returns:
            List of file metadata
        """
        try:
            client = cls.get_client()
            
            # Ensure folder ends with /
            if not folder.endswith('/'):
                folder += '/'
            
            response = client.list_objects_v2(
                Bucket=SUPABASE_BUCKET,
                Prefix=folder,
                MaxKeys=limit
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        "name": os.path.basename(obj['Key']),
                        "id": obj['Key'], # Using Key as ID
                        "updated_at": obj['LastModified'].isoformat(),
                        "created_at": obj['LastModified'].isoformat(), # S3 doesn't give created_at separate from LastModified usually
                        "last_accessed_at": obj['LastModified'].isoformat(),
                        "metadata": {
                            "size": obj['Size'],
                            "mimetype": "application/octet-stream" # S3 list doesn't return content type
                        }
                    })
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files from Supabase: {e}")
            raise
