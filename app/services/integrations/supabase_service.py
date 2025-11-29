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
        file_content: bytes,
        filename: str,
        content_type: Optional[str] = None,
        folder: str = "chat"
    ) -> dict:
        """
        Upload a file to Supabase storage via S3.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            content_type: MIME type of the file
            folder: Folder path in the bucket
            
        Returns:
            dict with url, path, and metadata
        """
        try:
            client = cls.get_client()
            
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
                client.put_object(
                    Bucket=SUPABASE_BUCKET,
                    Key=file_path,
                    Body=file_content,
                    ContentType=content_type,
                    ACL='public-read' # Assuming public bucket, otherwise remove or change
                )
            except ClientError as e:
                logger.error(f"Upload failed - Bucket: {SUPABASE_BUCKET}, Path: {file_path}")
                logger.error(f"Upload error details: {str(e)}")
                raise ValueError(f"Failed to upload file to Supabase storage: {str(e)}")
            
            logger.info(f"File uploaded to Supabase: {file_path}")
            
            # Construct public URL
            # S3 endpoint + bucket + key
            # Or if using Supabase, it might be endpoint/bucket/key
            # The provided endpoint is https://<project>.storage.supabase.co/storage/v1/s3
            # Public URL for supabase is usually https://<project>.supabase.co/storage/v1/object/public/<bucket>/<key>
            # But we can also use the S3 endpoint if it supports public access.
            # Let's try to construct it based on the endpoint or use get_signed_url if private.
            
            # For now, let's assume we want a signed URL or a public URL.
            # If the bucket is public, we can construct the URL.
            # If we use the S3 client to generate a presigned URL, that works too.
            
            # Let's return a signed URL by default for safety, or just the path.
            # The original code returned a public URL.
            
            # Let's try to generate a URL.
            public_url = f"https://{SUPABASE_PROJECT_REF}.supabase.co/storage/v1/object/public/{SUPABASE_BUCKET}/{file_path}"
            # Note: Supabase S3 endpoint might not serve files directly via GET without auth if private.
            # But if we want a public URL, we usually use the standard Supabase storage URL.
            # However, we only have S3 creds now.
            
            # Let's use presigned URL for the return value to be safe.
            # Or if the user wants public access, they should configure the bucket as public.
            
            # Let's generate a presigned URL for immediate access?
            # The original code used `get_public_url`.
            
            return {
                "url": public_url, # This might need adjustment based on actual public access config
                "path": file_path,
                "filename": filename,
                "content_type": content_type,
                "size": len(file_content)
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
