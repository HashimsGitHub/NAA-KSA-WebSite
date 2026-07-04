import base64
import mimetypes
from pathlib import Path
from typing import Dict
from uuid import uuid4

from azure.storage.blob import ContentSettings

from api.shared.config import ALLOWED_IMAGE_EXTENSIONS, BLOB_CONTAINERS
from api.shared.storage_client import StorageClient


class MediaService:
    """KISS image upload service: stores images in Blob Storage and returns the URL."""

    TARGETS = {
        "profile": BLOB_CONTAINERS["profile_images"],
        "blog": BLOB_CONTAINERS["blog_images"],
        "event": BLOB_CONTAINERS["event_images"],
    }

    def __init__(self):
        self.storage = StorageClient()

    def upload_image_base64(self, target: str, file_name: str, content_base64: str) -> Dict:
        if target not in self.TARGETS:
            raise ValueError("target must be profile, blog or event")

        suffix = Path(file_name).suffix.lower()
        if suffix not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError("Only jpg, jpeg, png, gif and webp images are allowed")

        if "," in content_base64:
            content_base64 = content_base64.split(",", 1)[1]

        raw = base64.b64decode(content_base64)
        if len(raw) > 10 * 1024 * 1024:
            raise ValueError("Image is too large")

        container_name = self.TARGETS[target]
        container = self.storage.container(container_name)
        blob_name = f"{target}/{uuid4()}{suffix}"
        content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"

        blob = container.get_blob_client(blob_name)
        blob.upload_blob(raw, overwrite=True, content_settings=ContentSettings(content_type=content_type))

        return {
            "url": blob.url,
            "container": container_name,
            "blob_path": blob_name,
            "file_name": file_name,
            "content_type": content_type,
            "size": len(raw),
        }
