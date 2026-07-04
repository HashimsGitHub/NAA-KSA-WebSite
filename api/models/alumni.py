from dataclasses import dataclass


@dataclass
class AlumniProfile:
    alumni_id: str
    full_name: str
    email: str = ""
    mobile: str = ""
    preferred_name: str = ""
    city: str = ""
    country: str = ""
    degree: str = ""
    department: str = ""
    graduation_year: str = ""
    current_company: str = ""
    current_position: str = ""
    industry: str = ""
    linkedin_url: str = ""
    facebook_url: str = ""
    instagram_url: str = ""
    website_url: str = ""
    bio: str = ""
    skills: str = ""
    interests: str = ""
    available_to_mentor: bool = False
    looking_for_jobs: bool = False
    available_to_recruit: bool = False
    profile_image_url: str = ""
    visibility: str = "visible"
    show_mobile: bool = False
    show_email: bool = False
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""
