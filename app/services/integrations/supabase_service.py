"""Supabase service for media storage."""
import mimetypes
import os
from datetime import timedelta
from typing import Optional
from uuid import uuid4

from supabase import Client, create_client

from app.core.config import SUPABASE_BUCKET, SUPABASE_KEY, SUPABASE_URL
from app.core.logging import logger


class SupabaseService:
    """Service for handling Supabase storage operations."""
    
    _client: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client."""
        if cls._client is None:
            if not SUPABASE_URL or not SUPABASE_KEY:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_KEY must be set in environment variables"
                )
            cls._client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Supabase client initialized")
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
        Upload a file to Supabase storage.
        
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
                response = client.storage.from_(SUPABASE_BUCKET).upload(
                    file_path,
                    file_content,
                    {
                        "content-type": content_type,
                        "x-upsert": "false"
                    }
                )
                logger.debug(f"Upload response: {response}")
            except Exception as upload_error:
                logger.error(f"Upload failed - Bucket: {SUPABASE_BUCKET}, Path: {file_path}")
                logger.error(f"Upload error details: {str(upload_error)}")
                logger.error(f"Error type: {type(upload_error).__name__}")
                
                # Try to extract more details from the error
                if hasattr(upload_error, 'response'):
                    logger.error(f"Response status: {getattr(upload_error.response, 'status_code', 'N/A')}")
                    logger.error(f"Response body: {getattr(upload_error.response, 'text', 'N/A')}")
                
                raise ValueError(f"Failed to upload file to Supabase storage: {str(upload_error)}")
            
            logger.info(f"File uploaded to Supabase: {file_path}")
            
            # Get public URL (or signed URL for private buckets)
            public_url = client.storage.from_(SUPABASE_BUCKET).get_public_url(file_path)
            
            return {
                "url": public_url,
                "path": file_path,
                "filename": filename,
                "content_type": content_type,
                "size": len(file_content)
            }
            
        except ValueError as ve:
            # Re-raise ValueError with our custom message
            raise
        except Exception as e:
            logger.error(f"Error uploading file to Supabase: {e}")
            logger.error(f"Error type: {type(e).__name__}")
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
            signed_url = client.storage.from_(SUPABASE_BUCKET).create_signed_upload_url(
                file_path
            )
            
            logger.info(f"Generated signed upload URL for: {file_path}")
            
            return {
                "signed_url": signed_url["signedURL"],
                "path": file_path,
                "token": signed_url.get("token"),
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
            
            signed_url = client.storage.from_(SUPABASE_BUCKET).create_signed_url(
                file_path,
                expires_in
            )
            
            return signed_url["signedURL"]
            
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
            
            client.storage.from_(SUPABASE_BUCKET).remove([file_path])
            
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
            
            files = client.storage.from_(SUPABASE_BUCKET).list(
                folder,
                {
                    "limit": limit,
                    "sortBy": {"column": "created_at", "order": "desc"}
                }
            )
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files from Supabase: {e}")
            raise
