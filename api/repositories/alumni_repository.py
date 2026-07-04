from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from azure.core.exceptions import ResourceNotFoundError

from api.shared.storage_client import StorageClient

from api.shared.config import TABLES

from api.shared.config import UNIVERSITY_ID

#UNIVERSITY_ID = "NUST-KSA"

ALUMNI_TABLE = TABLES["alumni"]

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_email(email: str) -> str:
    return email.strip().lower() if email else ""


def normalize_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


class AlumniRepository:
    def __init__(self):
        self.storage = StorageClient()
        self.table = self.storage.table(ALUMNI_TABLE)

    def create_profile(self, profile: Dict) -> Dict:
        alumni_id = profile.get("alumni_id") or str(uuid4())

        entity = {
            "PartitionKey": UNIVERSITY_ID,
            "RowKey": alumni_id,
            "alumni_id": alumni_id,
            "full_name": normalize_text(profile.get("full_name")),
            "preferred_name": normalize_text(profile.get("preferred_name")),
            "email": normalize_email(profile.get("email")),
            "mobile": normalize_text(profile.get("mobile")),
            "city": normalize_text(profile.get("city")),
            "country": normalize_text(profile.get("country")),
            "degree": normalize_text(profile.get("degree")),
            "department": normalize_text(profile.get("department")),
            "graduation_year": normalize_text(profile.get("graduation_year")),
            "current_company": normalize_text(profile.get("current_company")),
            "current_position": normalize_text(profile.get("current_position")),
            "industry": normalize_text(profile.get("industry")),
            "linkedin_url": normalize_text(profile.get("linkedin_url")),
            "facebook_url": normalize_text(profile.get("facebook_url")),
            "instagram_url": normalize_text(profile.get("instagram_url")),
            "website_url": normalize_text(profile.get("website_url")),
            "bio": normalize_text(profile.get("bio")),
            "skills": normalize_text(profile.get("skills")),
            "interests": normalize_text(profile.get("interests")),
            "available_to_mentor": bool(profile.get("available_to_mentor", False)),
            "looking_for_jobs": bool(profile.get("looking_for_jobs", False)),
            "available_to_recruit": bool(profile.get("available_to_recruit", False)),
            "profile_image_url": normalize_text(profile.get("profile_image_url")),
            "visibility": profile.get("visibility", "visible"),
            "show_mobile": bool(profile.get("show_mobile", False)),
            "show_email": bool(profile.get("show_email", False)),
            "status": profile.get("status", "active"),
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }

        self.table.create_entity(entity=entity)
        return entity

    def get_profile(self, alumni_id: str) -> Optional[Dict]:
        try:
            return dict(
                self.table.get_entity(
                    partition_key=UNIVERSITY_ID,
                    row_key=alumni_id,
                )
            )
        except ResourceNotFoundError:
            return None

    def update_profile(self, alumni_id: str, updates: Dict) -> Dict:
        profile = self.get_profile(alumni_id)

        if not profile:
            raise ValueError(f"Alumni profile not found: {alumni_id}")

        protected_fields = {
            "PartitionKey",
            "RowKey",
            "alumni_id",
            "created_at",
        }

        for key, value in updates.items():
            if key not in protected_fields:
                if key == "email":
                    profile[key] = normalize_email(value)
                elif key in [
                    "available_to_mentor",
                    "looking_for_jobs",
                    "available_to_recruit",
                    "show_mobile",
                    "show_email",
                ]:
                    profile[key] = bool(value)
                else:
                    profile[key] = normalize_text(value)

        profile["updated_at"] = utc_now()

        self.table.upsert_entity(entity=profile)
        return profile

    def delete_profile(self, alumni_id: str) -> bool:
        try:
            self.table.delete_entity(
                partition_key=UNIVERSITY_ID,
                row_key=alumni_id,
            )
            return True
        except ResourceNotFoundError:
            return False

    def list_profiles(self) -> List[Dict]:
        entities = self.table.query_entities(
            query_filter="PartitionKey eq @partition",
            parameters={"partition": UNIVERSITY_ID},
        )
        return [dict(entity) for entity in entities]

    def list_visible_profiles(self) -> List[Dict]:
        profiles = self.list_profiles()

        return [
            profile
            for profile in profiles
            if profile.get("status") == "active"
            and profile.get("visibility") == "visible"
        ]

    def search_profiles(
        self,
        name: str = "",
        city: str = "",
        country: str = "",
        degree: str = "",
        department: str = "",
        graduation_year: str = "",
        company: str = "",
        industry: str = "",
        skills: str = "",
        sort_by: str = "full_name",
        include_hidden: bool = False,
    ) -> List[Dict]:
        if include_hidden:
            profiles = self.list_profiles()
        else:
            profiles = self.list_visible_profiles()

        def contains(field_value, search_value):
            if not search_value:
                return True
            return search_value.lower() in normalize_text(field_value).lower()

        results = []

        for profile in profiles:
            if not contains(profile.get("full_name"), name):
                continue
            if not contains(profile.get("city"), city):
                continue
            if not contains(profile.get("country"), country):
                continue
            if not contains(profile.get("degree"), degree):
                continue
            if not contains(profile.get("department"), department):
                continue
            if not contains(profile.get("graduation_year"), graduation_year):
                continue
            if not contains(profile.get("current_company"), company):
                continue
            if not contains(profile.get("industry"), industry):
                continue
            if not contains(profile.get("skills"), skills):
                continue

            results.append(profile)

        allowed_sort_fields = {
            "full_name",
            "graduation_year",
            "city",
            "country",
            "degree",
            "department",
            "current_company",
        }

        if sort_by not in allowed_sort_fields:
            sort_by = "full_name"

        results.sort(
            key=lambda item: normalize_text(item.get(sort_by)).lower()
        )

        return results

    def public_view(self, profile: Dict) -> Dict:
        safe_profile = dict(profile)

        if not safe_profile.get("show_mobile", False):
            safe_profile["mobile"] = ""

        if not safe_profile.get("show_email", False):
            safe_profile["email"] = ""

        safe_profile.pop("PartitionKey", None)
        safe_profile.pop("RowKey", None)

        return safe_profile

    def search_public_profiles(self, **filters) -> List[Dict]:
        results = self.search_profiles(**filters)
        return [self.public_view(profile) for profile in results]