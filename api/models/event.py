from dataclasses import dataclass


@dataclass
class Event:
    event_id: str
    title: str
    slug: str
    description: str
    event_date: str
    start_time: str = ""
    end_time: str = ""
    venue: str = ""
    city: str = ""
    google_maps_url: str = ""
    registration_required: bool = False
    registration_open_at: str = ""
    registration_close_at: str = ""
    capacity: int = 0
    cover_image_url: str = ""
    status: str = "draft"
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""