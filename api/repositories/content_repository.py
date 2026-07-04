from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from azure.core.exceptions import ResourceNotFoundError

from shared.config import TABLES, UNIVERSITY_ID
from shared.storage_client import StorageClient


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value) -> str:
    return "" if value is None else str(value).strip()


class ContentRepository:
    """Small Azure Table repository for blogs, events and knowledge-base posts."""

    def __init__(self, table_key: str):
        self.storage = StorageClient()
        self.table = self.storage.table(TABLES[table_key])

    def create(self, item: Dict, created_by: str) -> Dict:
        item_id = item.get("id") or item.get("post_id") or item.get("event_id") or str(uuid4())
        now = utc_now()
        entity = {
            "PartitionKey": UNIVERSITY_ID,
            "RowKey": item_id,
            "id": item_id,
            "title": clean(item.get("title")),
            "summary": clean(item.get("summary")),
            "body": clean(item.get("body") or item.get("description")),
            "category": clean(item.get("category", "knowledge")),
            "tags": clean(item.get("tags")),
            "event_date": clean(item.get("event_date")),
            "venue": clean(item.get("venue")),
            "city": clean(item.get("city")),
            "cover_image_url": clean(item.get("cover_image_url")),
            "status": clean(item.get("status", "published")),
            "created_by": clean(created_by),
            "created_at": now,
            "updated_at": now,
        }
        self.table.create_entity(entity=entity)
        return entity

    def get(self, item_id: str) -> Optional[Dict]:
        try:
            return dict(self.table.get_entity(partition_key=UNIVERSITY_ID, row_key=item_id))
        except ResourceNotFoundError:
            return None

    def update(self, item_id: str, updates: Dict) -> Dict:
        item = self.get(item_id)
        if not item:
            raise ValueError("Content item not found")
        for key in ["title", "summary", "body", "category", "tags", "event_date", "venue", "city", "cover_image_url", "status"]:
            if key in updates:
                item[key] = clean(updates[key])
        item["updated_at"] = utc_now()
        self.table.upsert_entity(entity=item)
        return item

    def delete(self, item_id: str) -> bool:
        try:
            self.table.delete_entity(partition_key=UNIVERSITY_ID, row_key=item_id)
            return True
        except ResourceNotFoundError:
            return False

    def list(self, published_only: bool = True, category: str = "") -> List[Dict]:
        entities = self.table.query_entities(
            query_filter="PartitionKey eq @partition",
            parameters={"partition": UNIVERSITY_ID},
        )
        rows = [self.public_view(dict(e)) for e in entities]
        if published_only:
            rows = [r for r in rows if r.get("status") == "published"]
        if category:
            rows = [r for r in rows if r.get("category") == category]
        rows.sort(key=lambda x: x.get("event_date") or x.get("created_at") or "", reverse=True)
        return rows

    def public_view(self, item: Dict) -> Dict:
        item.pop("PartitionKey", None)
        item.pop("RowKey", None)
        return item
