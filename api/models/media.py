from dataclasses import dataclass


@dataclass
class MediaAsset:
    media_id: str
    asset_type: str
    linked_entity_id: str
    owner_email: str
    blob_container: str
    blob_path: str
    file_name: str
    content_type: str
    file_size: int
    status: str = "uploaded"
    created_at: str = ""
    approved_by: str = ""
    approved_at: str = ""