from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

import pandas as pd

from repositories.alumni_repository import AlumniRepository
from shared.response_utils import success_response, error_response


COLUMN_MAP = {
    "full_name": [
        "full_name",
        "fullname",
        "name",
        "full name",
        "alumni name",
        "student name",
    ],
    "email": [
        "email",
        "email address",
        "e-mail",
        "mail",
    ],
    "mobile": [
        "mobile",
        "mobile number",
        "phone",
        "phone number",
        "contact",
        "contact number",
        "whatsapp",
        "whatsapp number",
    ],
    "city": [
        "city",
        "location",
        "current city",
    ],
    "country": [
        "country",
        "current country",
    ],
    "degree": [
        "degree",
        "program",
        "qualification",
    ],
    "department": [
        "department",
        "school",
        "faculty",
        "discipline",
    ],
    "graduation_year": [
        "graduation_year",
        "graduation year",
        "grad year",
        "year",
        "batch",
        "class of",
    ],
    "current_company": [
        "company",
        "current company",
        "employer",
        "organization",
        "organisation",
    ],
    "current_position": [
        "position",
        "designation",
        "job title",
        "current position",
        "role",
    ],
    "industry": [
        "industry",
        "sector",
    ],
    "linkedin_url": [
        "linkedin",
        "linkedin url",
        "linkedin profile",
        "linkedin profile url",
    ],
    "facebook_url": [
        "facebook",
        "facebook url",
    ],
    "instagram_url": [
        "instagram",
        "instagram url",
    ],
    "website_url": [
        "website",
        "personal website",
        "portfolio",
    ],
    "skills": [
        "skills",
        "expertise",
        "specialization",
        "specialisation",
    ],
}


REQUIRED_FIELDS = ["full_name"]


def normalize_column_name(name: str) -> str:
    return str(name).strip().lower().replace("_", " ")


def clean_value(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


class ImportService:
    def __init__(self):
        self.alumni = AlumniRepository()

    def read_file(self, file_path: str) -> pd.DataFrame:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.suffix.lower() == ".csv":
            return pd.read_csv(path)

        if path.suffix.lower() in [".xlsx", ".xls"]:
            return pd.read_excel(path)

        raise ValueError("Only CSV and Excel files are supported.")

    def detect_column_mapping(self, columns: List[str]) -> Dict[str, Optional[str]]:
        normalized_source = {
            normalize_column_name(column): column
            for column in columns
        }

        mapping = {}

        for target_field, aliases in COLUMN_MAP.items():
            matched_column = None

            for alias in aliases:
                normalized_alias = normalize_column_name(alias)

                if normalized_alias in normalized_source:
                    matched_column = normalized_source[normalized_alias]
                    break

            mapping[target_field] = matched_column

        return mapping

    def normalize_dataframe(
        self,
        df: pd.DataFrame,
        mapping: Dict[str, Optional[str]],
    ) -> List[Dict]:
        records = []

        for _, row in df.iterrows():
            profile = {}

            for target_field, source_column in mapping.items():
                if source_column:
                    profile[target_field] = clean_value(row.get(source_column))
                else:
                    profile[target_field] = ""

            profile["visibility"] = "visible"
            profile["status"] = "active"
            profile["show_mobile"] = False
            profile["show_email"] = False

            records.append(profile)

        return records

    def validate_record(self, record: Dict) -> List[str]:
        errors = []

        for field in REQUIRED_FIELDS:
            if not record.get(field):
                errors.append(f"Missing required field: {field}")

        email = record.get("email", "")
        if email and "@" not in email:
            errors.append("Invalid email address.")

        return errors

    def find_duplicate(self, record: Dict, existing_profiles: List[Dict]) -> Optional[Dict]:
        email = record.get("email", "").lower()
        mobile = record.get("mobile", "")
        linkedin = record.get("linkedin_url", "").lower()
        full_name = record.get("full_name", "").lower()
        graduation_year = record.get("graduation_year", "")

        for profile in existing_profiles:
            if email and email == profile.get("email", "").lower():
                return profile

            if mobile and mobile == profile.get("mobile", ""):
                return profile

            if linkedin and linkedin == profile.get("linkedin_url", "").lower():
                return profile

            if (
                full_name
                and graduation_year
                and full_name == profile.get("full_name", "").lower()
                and graduation_year == profile.get("graduation_year", "")
            ):
                return profile

        return None

    def preview_import(self, file_path: str) -> Dict:
        try:
            df = self.read_file(file_path)
            mapping = self.detect_column_mapping(list(df.columns))
            records = self.normalize_dataframe(df, mapping)
            existing_profiles = self.alumni.list_profiles()

            preview_rows = []
            stats = {
                "total_records": len(records),
                "valid_records": 0,
                "error_records": 0,
                "new_records": 0,
                "duplicate_records": 0,
            }

            for index, record in enumerate(records, start=1):
                errors = self.validate_record(record)
                duplicate = self.find_duplicate(record, existing_profiles)

                status = "new"

                if errors:
                    status = "error"
                    stats["error_records"] += 1
                elif duplicate:
                    status = "duplicate"
                    stats["duplicate_records"] += 1
                else:
                    stats["valid_records"] += 1
                    stats["new_records"] += 1

                preview_rows.append(
                    {
                        "row_number": index,
                        "status": status,
                        "errors": errors,
                        "duplicate_alumni_id": duplicate.get("alumni_id") if duplicate else "",
                        "record": record,
                    }
                )

            return success_response(
                "Import preview generated.",
                {
                    "file_path": file_path,
                    "columns": list(df.columns),
                    "mapping": mapping,
                    "stats": stats,
                    "preview": preview_rows,
                },
            )

        except Exception as ex:
            return error_response(
                "Import preview failed.",
                [str(ex)],
            )

    def execute_import(
        self,
        file_path: str,
        allow_duplicates: bool = False,
    ) -> Dict:
        preview_result = self.preview_import(file_path)

        if not preview_result["success"]:
            return preview_result

        preview_rows = preview_result["data"]["preview"]

        created = []
        skipped = []
        failed = []

        for row in preview_rows:
            status = row["status"]
            record = row["record"]

            if status == "error":
                failed.append(row)
                continue

            if status == "duplicate" and not allow_duplicates:
                skipped.append(row)
                continue

            try:
                profile = self.alumni.create_profile(record)
                created.append(profile)

            except Exception as ex:
                row["errors"].append(str(ex))
                failed.append(row)

        return success_response(
            "Import executed.",
            {
                "created_count": len(created),
                "skipped_count": len(skipped),
                "failed_count": len(failed),
                "created": created,
                "skipped": skipped,
                "failed": failed,
            },
        )
