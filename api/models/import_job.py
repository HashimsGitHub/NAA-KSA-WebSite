from dataclasses import dataclass


@dataclass
class ImportJob:
    import_id: str
    file_name: str
    source_type: str
    uploaded_by: str
    status: str = "uploaded"
    records_total: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    error_summary: str = ""
    created_at: str = ""
    completed_at: str = ""
