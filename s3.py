"""
S3-compatible storage module for Nuvemhost
Supports AWS S3, MinIO, DigitalOcean Spaces, etc.
Also provides LocalStorage fallback for development.
"""
import os
import io
import zipfile
import shutil
import mimetypes
from typing import List, Optional, BinaryIO
from uuid import uuid4
from werkzeug.utils import secure_filename

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None
    Config = None
    ClientError = Exception


class S3Storage:
    """S3-compatible storage handler for project files"""
    
    def __init__(
        self,
        endpoint_url: str = None,
        access_key: str = None,
        secret_key: str = None,
        bucket_name: str = None,
        region: str = 'us-east-1',
        use_ssl: bool = True
    ):
        """
        Initialize S3 storage client
        
        Args:
            endpoint_url: S3 endpoint (e.g., 'https://s3.amazonaws.com', 'http://localhost:9000')
            access_key: AWS access key ID
            secret_key: AWS secret access key
            bucket_name: Bucket name for storage
            region: AWS region
            use_ssl: Use SSL/TLS for connection
        """
        self.bucket_name = bucket_name
        self.use_ssl = use_ssl
        
        # Configure boto3 client
        config = Config(
            region_name=region,
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'standard'}
        )
        
        self.client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=config,
            use_ssl=use_ssl
        )
        
        # Ensure bucket exists
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """Create bucket if it doesn't exist"""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    if self.client.meta.region_name == 'us-east-1':
                        self.client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.client.meta.region_name}
                        )
                except ClientError as ce:
                    raise Exception(f"Failed to create bucket: {ce}")
            elif error_code == '403':
                raise Exception(f"Access denied to bucket: {self.bucket_name}")
            else:
                raise
    
    def _project_prefix(self, project_id: str) -> str:
        """Get S3 prefix for a project"""
        return f"projects/{project_id}/"
    
    def _file_key(self, project_id: str, file_path: str) -> str:
        """Get full S3 key for a file"""
        # Normalize path
        file_path = file_path.lstrip('/')
        return f"{self._project_prefix(project_id)}{file_path}"
    
    # ==================== PROJECT OPERATIONS ====================
    
    def upload_project(self, project_id: str, zip_file: BinaryIO) -> List[str]:
        """
        Upload and extract ZIP file to S3
        
        Returns:
            List of extracted file paths
        """
        extracted_files = []
        prefix = self._project_prefix(project_id)
        
        # Read ZIP content
        zip_content = zip_file.read()
        zip_buffer = io.BytesIO(zip_content)
        
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            for member in zip_ref.namelist():
                # Skip directories and dangerous paths
                if member.endswith('/') or member.startswith('/') or '..' in member:
                    continue
                
                # Check file extension
                if '.' in member:
                    ext = member.rsplit('.', 1)[1].lower()
                    # We'll validate extensions at the app level
                
                # Extract file content
                file_content = zip_ref.read(member)
                
                # Upload to S3
                key = f"{prefix}{member}"
                self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=file_content,
                    ContentType=mimetypes.guess_type(member)[0] or 'application/octet-stream'
                )
                extracted_files.append(member)
        
        return extracted_files
    
    def project_exists(self, project_id: str) -> bool:
        """Check if project has any files"""
        prefix = self._project_prefix(project_id)
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=1
            )
            return 'Contents' in response and len(response['Contents']) > 0
        except ClientError:
            return False
    
    def delete_project(self, project_id: str) -> bool:
        """Delete all files for a project"""
        prefix = self._project_prefix(project_id)
        
        try:
            # List all objects
            paginator = self.client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
            
            # Delete in batches
            for page in pages:
                if 'Contents' in page:
                    objects = [{'Key': obj['Key']} for obj in page['Contents']]
                    self.client.delete_objects(
                        Bucket=self.bucket_name,
                        Delete={'Objects': objects, 'Quiet': True}
                    )
            return True
        except ClientError as e:
            print(f"Error deleting project {project_id}: {e}")
            return False
    
    def list_files(self, project_id: str) -> List[str]:
        """List all files in a project"""
        prefix = self._project_prefix(project_id)
        files = []
        
        try:
            paginator = self.client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        # Remove prefix to get relative path
                        rel_path = obj['Key'][len(prefix):]
                        if rel_path:  # Skip empty (directory marker)
                            files.append(rel_path)
        except ClientError:
            pass
        
        return files
    
    # ==================== FILE OPERATIONS ====================
    
    def get_file(self, project_id: str, file_path: str) -> Optional[bytes]:
        """Get file content as bytes"""
        key = self._file_key(project_id, file_path)
        
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise
    
    def get_file_text(self, project_id: str, file_path: str) -> Optional[str]:
        """Get file content as text (UTF-8)"""
        content = self.get_file(project_id, file_path)
        if content is None:
            return None
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            return None
    
    def save_file(self, project_id: str, file_path: str, content: str, content_type: str = None) -> bool:
        """Save text file to S3"""
        key = self._file_key(project_id, file_path)
        
        if content_type is None:
            content_type = mimetypes.guess_type(file_path)[0] or 'text/plain'
        
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content.encode('utf-8'),
                ContentType=content_type
            )
            return True
        except ClientError as e:
            print(f"Error saving file {file_path}: {e}")
            return False
    
    def save_file_bytes(self, project_id: str, file_path: str, content: bytes, content_type: str = None) -> bool:
        """Save binary file to S3"""
        key = self._file_key(project_id, file_path)
        
        if content_type is None:
            content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType=content_type
            )
            return True
        except ClientError as e:
            print(f"Error saving file {file_path}: {e}")
            return False
    
    def delete_file(self, project_id: str, file_path: str) -> bool:
        """Delete a single file"""
        key = self._file_key(project_id, file_path)
        
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False
    
    def file_exists(self, project_id: str, file_path: str) -> bool:
        """Check if file exists"""
        key = self._file_key(project_id, file_path)
        
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False
    
    # ==================== PUBLIC ACCESS (for serving) ====================
    
    def generate_presigned_url(self, project_id: str, file_path: str, expiration: int = 3600) -> str:
        """Generate presigned URL for temporary public access"""
        key = self._file_key(project_id, file_path)
        
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except ClientError:
            return None
    
    def get_file_metadata(self, project_id: str, file_path: str) -> Optional[dict]:
        """Get file metadata (size, content-type, last-modified)"""
        key = self._file_key(project_id, file_path)
        
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=key)
            return {
                'size': response.get('ContentLength', 0),
                'content_type': response.get('ContentType', 'application/octet-stream'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag', '').strip('"')
            }
        except ClientError:
            return None


class LocalStorage:
    """Local filesystem storage - fallback for development"""
    
    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.getenv("UPLOAD_FOLDER", "./uploads")
        os.makedirs(self.base_path, exist_ok=True)
    
    def _project_path(self, project_id: str) -> str:
        return os.path.join(self.base_path, project_id)
    
    def _file_path(self, project_id: str, file_path: str) -> str:
        file_path = file_path.lstrip('/')
        return os.path.join(self._project_path(project_id), file_path)
    
    def upload_project(self, project_id: str, zip_file: BinaryIO) -> List[str]:
        extracted_files = []
        project_dir = self._project_path(project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        zip_content = zip_file.read()
        zip_buffer = io.BytesIO(zip_content)
        
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            for member in zip_ref.namelist():
                if member.endswith('/') or member.startswith('/') or '..' in member:
                    continue
                
                file_content = zip_ref.read(member)
                full_path = os.path.join(project_dir, member)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                with open(full_path, 'wb') as f:
                    f.write(file_content)
                extracted_files.append(member)
        
        return extracted_files
    
    def project_exists(self, project_id: str) -> bool:
        return os.path.exists(self._project_path(project_id))
    
    def delete_project(self, project_id: str) -> bool:
        project_dir = self._project_path(project_id)
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
            return True
        return False
    
    def list_files(self, project_id: str) -> List[str]:
        project_dir = self._project_path(project_id)
        files = []
        
        if not os.path.exists(project_dir):
            return files
        
        for root, dirs, filenames in os.walk(project_dir):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, project_dir)
                files.append(rel_path)
        
        return files
    
    def get_file(self, project_id: str, file_path: str) -> Optional[bytes]:
        full_path = self._file_path(project_id, file_path)
        if not os.path.exists(full_path):
            return None
        with open(full_path, 'rb') as f:
            return f.read()
    
    def get_file_text(self, project_id: str, file_path: str) -> Optional[str]:
        content = self.get_file(project_id, file_path)
        if content is None:
            return None
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            return None
    
    def save_file(self, project_id: str, file_path: str, content: str, content_type: str = None) -> bool:
        full_path = self._file_path(project_id, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving file {file_path}: {e}")
            return False
    
    def save_file_bytes(self, project_id: str, file_path: str, content: bytes, content_type: str = None) -> bool:
        full_path = self._file_path(project_id, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        try:
            with open(full_path, 'wb') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving file {file_path}: {e}")
            return False
    
    def delete_file(self, project_id: str, file_path: str) -> bool:
        full_path = self._file_path(project_id, file_path)
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        except Exception:
            pass
        return False
    
    def file_exists(self, project_id: str, file_path: str) -> bool:
        full_path = self._file_path(project_id, file_path)
        return os.path.exists(full_path)
    
    def generate_presigned_url(self, project_id: str, file_path: str, expiration: int = 3600) -> str:
        # Not applicable for local storage
        return None
    
    def get_file_metadata(self, project_id: str, file_path: str) -> Optional[dict]:
        full_path = self._file_path(project_id, file_path)
        if not os.path.exists(full_path):
            return None
        stat = os.stat(full_path)
        return {
            'size': stat.st_size,
            'content_type': mimetypes.guess_type(file_path)[0] or 'application/octet-stream',
            'last_modified': stat.st_mtime,
            'etag': ''
        }


# Global instance (initialized in app.py)
storage = None


def init_storage(
    endpoint_url: str = None,
    access_key: str = None,
    secret_key: str = None,
    bucket_name: str = None,
    region: str = 'us-east-1',
    use_ssl: bool = True,
    local_path: str = None
):
    """Initialize global storage instance (S3 or Local fallback)"""
    global storage
    
    if all([endpoint_url, access_key, secret_key, bucket_name]) and BOTO3_AVAILABLE:
        try:
            storage = S3Storage(
                endpoint_url=endpoint_url,
                access_key=access_key,
                secret_key=secret_key,
                bucket_name=bucket_name,
                region=region,
                use_ssl=use_ssl
            )
            print("S3 Storage initialized")
        except Exception as e:
            print(f"Failed to initialize S3, falling back to local: {e}")
            storage = LocalStorage(local_path)
    else:
        if not BOTO3_AVAILABLE:
            print("boto3 not installed, using local storage")
        else:
            print("S3 not fully configured, using local storage")
        storage = LocalStorage(local_path)
    
    return storage


def get_storage():
    """Get global storage instance"""
    if storage is None:
        raise RuntimeError("Storage not initialized. Call init_storage() first.")
    return storage