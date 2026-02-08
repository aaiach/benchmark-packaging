"""Cloud storage integration for competitor packaging images.

Supports multiple cloud storage providers:
- AWS S3
- Google Cloud Storage
- Azure Blob Storage

Images are uploaded with metadata and organized by brand/product.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, Literal
from datetime import datetime, timedelta
import mimetypes

from dotenv import load_dotenv

load_dotenv()


class CloudStorageUploader:
    """Upload images to cloud storage with metadata.
    
    Automatically detects provider based on environment variables:
    - AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY -> AWS S3
    - GOOGLE_APPLICATION_CREDENTIALS -> Google Cloud Storage
    - AZURE_STORAGE_CONNECTION_STRING -> Azure Blob Storage
    """
    
    def __init__(
        self,
        bucket_name: str,
        provider: Optional[Literal["s3", "gcs", "azure"]] = None
    ):
        """Initialize cloud storage uploader.
        
        Args:
            bucket_name: Name of the storage bucket/container.
            provider: Storage provider. Auto-detected if not specified.
        """
        self.bucket_name = bucket_name
        self.provider = provider or self._detect_provider()
        self.client = None
        
        if self.provider:
            self._initialize_client()
    
    def _detect_provider(self) -> Optional[str]:
        """Auto-detect cloud storage provider from environment."""
        if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
            return "s3"
        elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            return "gcs"
        elif os.getenv("AZURE_STORAGE_CONNECTION_STRING"):
            return "azure"
        return None
    
    def _initialize_client(self):
        """Initialize the appropriate cloud storage client."""
        if self.provider == "s3":
            self._initialize_s3()
        elif self.provider == "gcs":
            self._initialize_gcs()
        elif self.provider == "azure":
            self._initialize_azure()
    
    def _initialize_s3(self):
        """Initialize AWS S3 client."""
        try:
            import boto3
            self.client = boto3.client('s3')
        except ImportError:
            raise ImportError(
                "boto3 not installed. Install with: pip install boto3"
            )
    
    def _initialize_gcs(self):
        """Initialize Google Cloud Storage client."""
        try:
            from google.cloud import storage
            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)
        except ImportError:
            raise ImportError(
                "google-cloud-storage not installed. "
                "Install with: pip install google-cloud-storage"
            )
    
    def _initialize_azure(self):
        """Initialize Azure Blob Storage client."""
        try:
            from azure.storage.blob import BlobServiceClient
            connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            self.client = BlobServiceClient.from_connection_string(connection_string)
            self.container_client = self.client.get_container_client(self.bucket_name)
        except ImportError:
            raise ImportError(
                "azure-storage-blob not installed. "
                "Install with: pip install azure-storage-blob"
            )
    
    def upload_image(
        self,
        local_path: str,
        remote_path: str,
        metadata: Optional[Dict[str, str]] = None,
        public: bool = False
    ) -> str:
        """Upload an image to cloud storage.
        
        Args:
            local_path: Local file path.
            remote_path: Remote path in bucket (e.g., "alpro/front_image.jpg").
            metadata: Optional metadata dictionary.
            public: Whether to make the file publicly accessible.
        
        Returns:
            Public URL of the uploaded file.
        
        Raises:
            Exception: If upload fails or no provider configured.
        """
        if not self.provider or not self.client:
            raise Exception(
                "No cloud storage provider configured. "
                "Set AWS_ACCESS_KEY_ID, GOOGLE_APPLICATION_CREDENTIALS, "
                "or AZURE_STORAGE_CONNECTION_STRING in environment."
            )
        
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")
        
        # Detect content type
        content_type, _ = mimetypes.guess_type(str(local_path))
        if not content_type:
            content_type = "application/octet-stream"
        
        # Upload based on provider
        if self.provider == "s3":
            return self._upload_s3(local_path, remote_path, metadata, content_type, public)
        elif self.provider == "gcs":
            return self._upload_gcs(local_path, remote_path, metadata, content_type, public)
        elif self.provider == "azure":
            return self._upload_azure(local_path, remote_path, metadata, content_type, public)
    
    def _upload_s3(
        self,
        local_path: Path,
        remote_path: str,
        metadata: Optional[Dict[str, str]],
        content_type: str,
        public: bool
    ) -> str:
        """Upload to AWS S3."""
        extra_args = {
            "ContentType": content_type,
        }
        
        if metadata:
            extra_args["Metadata"] = metadata
        
        if public:
            extra_args["ACL"] = "public-read"
        
        with open(local_path, 'rb') as f:
            self.client.upload_fileobj(
                f,
                self.bucket_name,
                remote_path,
                ExtraArgs=extra_args
            )
        
        # Generate URL
        region = os.getenv("AWS_REGION", "us-east-1")
        url = f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{remote_path}"
        
        return url
    
    def _upload_gcs(
        self,
        local_path: Path,
        remote_path: str,
        metadata: Optional[Dict[str, str]],
        content_type: str,
        public: bool
    ) -> str:
        """Upload to Google Cloud Storage."""
        blob = self.bucket.blob(remote_path)
        
        if metadata:
            blob.metadata = metadata
        
        blob.upload_from_filename(str(local_path), content_type=content_type)
        
        if public:
            blob.make_public()
        
        return blob.public_url
    
    def _upload_azure(
        self,
        local_path: Path,
        remote_path: str,
        metadata: Optional[Dict[str, str]],
        content_type: str,
        public: bool
    ) -> str:
        """Upload to Azure Blob Storage."""
        blob_client = self.container_client.get_blob_client(remote_path)
        
        with open(local_path, 'rb') as f:
            blob_client.upload_blob(
                f,
                overwrite=True,
                content_settings={
                    "content_type": content_type
                },
                metadata=metadata
            )
        
        # Generate URL
        account_name = self.client.account_name
        url = f"https://{account_name}.blob.core.windows.net/{self.bucket_name}/{remote_path}"
        
        return url
    
    def batch_upload_images(
        self,
        images: list,
        base_path: str = "",
        metadata_factory: Optional[callable] = None,
        public: bool = False
    ) -> Dict[str, str]:
        """Upload multiple images in batch.
        
        Args:
            images: List of local image paths.
            base_path: Base path in bucket to organize images.
            metadata_factory: Optional function to generate metadata per image.
            public: Whether to make files publicly accessible.
        
        Returns:
            Dictionary mapping local paths to cloud URLs.
        """
        results = {}
        
        for local_path in images:
            try:
                local_path = Path(local_path)
                remote_path = f"{base_path}/{local_path.name}" if base_path else local_path.name
                
                metadata = None
                if metadata_factory:
                    metadata = metadata_factory(local_path)
                
                url = self.upload_image(local_path, remote_path, metadata, public)
                results[str(local_path)] = url
                
            except Exception as e:
                print(f"Failed to upload {local_path}: {e}")
                results[str(local_path)] = None
        
        return results
    
    def generate_signed_url(
        self,
        remote_path: str,
        expiration_hours: int = 24
    ) -> Optional[str]:
        """Generate a signed URL for temporary access.
        
        Args:
            remote_path: Path to file in bucket.
            expiration_hours: Hours until URL expires.
        
        Returns:
            Signed URL or None if not supported.
        """
        if not self.provider or not self.client:
            return None
        
        try:
            if self.provider == "s3":
                return self.client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': remote_path},
                    ExpiresIn=expiration_hours * 3600
                )
            
            elif self.provider == "gcs":
                blob = self.bucket.blob(remote_path)
                return blob.generate_signed_url(
                    expiration=timedelta(hours=expiration_hours)
                )
            
            elif self.provider == "azure":
                from azure.storage.blob import generate_blob_sas, BlobSasPermissions
                
                sas_token = generate_blob_sas(
                    account_name=self.client.account_name,
                    container_name=self.bucket_name,
                    blob_name=remote_path,
                    account_key=os.getenv("AZURE_STORAGE_ACCOUNT_KEY"),
                    permission=BlobSasPermissions(read=True),
                    expiry=datetime.utcnow() + timedelta(hours=expiration_hours)
                )
                
                return f"https://{self.client.account_name}.blob.core.windows.net/{self.bucket_name}/{remote_path}?{sas_token}"
        
        except Exception as e:
            print(f"Failed to generate signed URL: {e}")
            return None


def upload_competitor_images_to_cloud(
    dataset_dir: str,
    bucket_name: str,
    provider: Optional[str] = None,
    public: bool = False
) -> Dict[str, str]:
    """Upload all images from a competitor dataset to cloud storage.
    
    Args:
        dataset_dir: Directory containing the dataset (with images/ subdirectory).
        bucket_name: Cloud storage bucket name.
        provider: Storage provider (s3/gcs/azure). Auto-detected if not specified.
        public: Whether to make images publicly accessible.
    
    Returns:
        Dictionary mapping local paths to cloud URLs.
    
    Example:
        >>> urls = upload_competitor_images_to_cloud(
        ...     "output/competitor_packaging/competitor_scrape_20260208_120000",
        ...     "recolt-competitor-packaging"
        ... )
        >>> print(f"Uploaded {len(urls)} images")
    """
    uploader = CloudStorageUploader(bucket_name, provider)
    
    if not uploader.provider:
        raise Exception(
            "No cloud storage provider detected. Please configure:\n"
            "  - AWS: Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY\n"
            "  - GCS: Set GOOGLE_APPLICATION_CREDENTIALS\n"
            "  - Azure: Set AZURE_STORAGE_CONNECTION_STRING"
        )
    
    dataset_path = Path(dataset_dir)
    images_dir = dataset_path / "images"
    
    if not images_dir.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")
    
    # Find all images
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(images_dir.rglob(f"*{ext}"))
    
    print(f"Uploading {len(image_files)} images to {uploader.provider.upper()}...")
    
    # Generate metadata for each image
    def metadata_factory(local_path: Path):
        return {
            "source": "competitor-scraper",
            "uploaded_at": datetime.utcnow().isoformat(),
            "dataset": dataset_path.name
        }
    
    # Upload with organized structure
    base_path = f"competitor_packaging/{dataset_path.name}"
    
    results = uploader.batch_upload_images(
        image_files,
        base_path=base_path,
        metadata_factory=metadata_factory,
        public=public
    )
    
    successful = sum(1 for url in results.values() if url)
    print(f"✓ Uploaded {successful}/{len(image_files)} images successfully")
    
    return results
