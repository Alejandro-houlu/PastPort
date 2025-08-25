"""
S3 Service for PastPort - DigitalOcean Spaces Integration
Handles private file access with presigned URLs for secure image retrieval
"""
import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

# PastPort S3 Configuration
BUCKET_NAME = "pastport-bucket"
REGION_NAME = "sgp1"
ENDPOINT_URL = "https://sgp1.digitaloceanspaces.com"

class S3Service:
    def __init__(self):
        """Initialize S3 client with PastPort DigitalOcean Spaces configuration"""
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=REGION_NAME,
                endpoint_url=ENDPOINT_URL,
                aws_access_key_id=os.getenv('ACCESS_KEY'),
                aws_secret_access_key=os.getenv('SECRET_KEY')
            )
            self.bucket_name = BUCKET_NAME
        except NoCredentialsError:
            logger.error("S3 credentials not found in environment variables")
            raise Exception("S3 credentials not configured")
    
    def list_folder_contents(self, folder_path: str) -> List[str]:
        """
        List all objects in a specific S3 folder
        
        Args:
            folder_path: S3 folder path (e.g., 'pastport/artifact_images/rafflesia_870a2f4d/')
        
        Returns:
            List of object keys in the folder
        """
        try:
            # Ensure folder path ends with '/'
            if not folder_path.endswith('/'):
                folder_path += '/'
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=folder_path
            )
            
            if 'Contents' not in response:
                logger.warning(f"No objects found in folder: {folder_path}")
                return []
            
            # Extract object keys and filter out the folder itself
            object_keys = [
                obj['Key'] for obj in response['Contents'] 
                if obj['Key'] != folder_path  # Exclude the folder entry itself
            ]
            
            logger.info(f"Found {len(object_keys)} objects in folder: {folder_path}")
            return object_keys
            
        except ClientError as e:
            logger.error(f"Error listing folder contents: {e}")
            return []
    
    def get_first_image(self, folder_path: str) -> Optional[str]:
        """
        Get the first image file from an artifact folder
        
        Args:
            folder_path: S3 folder path (e.g., 'pastport/artifact_images/rafflesia_870a2f4d/')
        
        Returns:
            Object key of the first image file, or None if no images found
        """
        try:
            object_keys = self.list_folder_contents(folder_path)
            
            if not object_keys:
                logger.warning(f"No objects found in folder: {folder_path}")
                return None
            
            # Filter for image files (common image extensions)
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
            image_files = [
                key for key in object_keys 
                if any(key.lower().endswith(ext) for ext in image_extensions)
            ]
            
            if not image_files:
                logger.warning(f"No image files found in folder: {folder_path}")
                return None
            
            # Sort to ensure consistent ordering and return first image
            image_files.sort()
            first_image = image_files[0]
            
            logger.info(f"Found first image: {first_image}")
            return first_image
            
        except Exception as e:
            logger.error(f"Error getting first image from folder {folder_path}: {e}")
            return None
    
    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for secure access to private S3 objects
        
        Args:
            object_key: S3 object key (full path to file)
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Presigned URL string, or None if generation failed
        """
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned URL for: {object_key}")
            return presigned_url
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL for {object_key}: {e}")
            return None
    
    def download_object(self, object_key: str) -> Optional[bytes]:
        """
        Download object content as bytes for streaming responses
        
        Args:
            object_key: S3 object key (full path to file)
        
        Returns:
            Object content as bytes, or None if download failed
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            content = response['Body'].read()
            logger.info(f"Downloaded object: {object_key} ({len(content)} bytes)")
            return content
            
        except ClientError as e:
            logger.error(f"Error downloading object {object_key}: {e}")
            return None
    
    def get_object_info(self, object_key: str) -> Optional[dict]:
        """
        Get metadata information about an S3 object
        
        Args:
            object_key: S3 object key (full path to file)
        
        Returns:
            Dictionary with object metadata, or None if object not found
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag')
            }
            
        except ClientError as e:
            logger.error(f"Error getting object info for {object_key}: {e}")
            return None


# Global S3 service instance
s3_service = S3Service()
